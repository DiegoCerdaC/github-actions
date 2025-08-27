"""
Enso Agent Evaluation using objective comparison.
Evaluates if the agent calls the correct defi_quote function with correct parameters.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List
from utils.firebase import set_request_ctx, set_context_id, get_request_ctx
from eval.enso.test_data import (
    USER_EVM_WALLET_ADDRESS,
    ENSO_TEST_CASES,
)

# Import the real agent
from agents.enso.enso_agent import call_enso_agent


class EnsoAgentEval:
    """
    Evaluation framework for the Enso Agent using objective comparison.
    Tests if the agent calls the correct defi_quote function with correct parameters.
    """

    def __init__(self, use_real_agent: bool = True):
        """
        Initialize the evaluator.

        Args:
            use_real_agent: If True, calls the real agent. If False, simulates based on ground truth.
        """
        self.use_real_agent = use_real_agent

    @staticmethod
    def normalize_function_call(call: Dict) -> Dict:
        """Normalize function call for case-insensitive comparison"""
        if isinstance(call, dict):
            normalized = {}
            for key, value in call.items():
                if key == "parameters" and isinstance(value, dict):
                    normalized_params = {}
                    for param_key, param_value in value.items():
                        # Convert string values to lowercase for case-insensitive comparison
                        if isinstance(param_value, str):
                            normalized_params[param_key] = param_value.lower()
                        else:
                            normalized_params[param_key] = param_value
                    normalized[key] = normalized_params
                else:
                    normalized[key] = value
            return normalized
        return call

    async def evaluate_single_case(self, test_case: Dict) -> Dict:
        """
        Evaluate a single test case using objective comparison.
        """
        # Clear previous function calls from context before this test
        test_chat_id = "enso_eval_test"
        set_request_ctx(test_chat_id, "function_calls", [])
        set_request_ctx(test_chat_id, "evaluation_mode", True)  # Set evaluation mode

        # Set wallet addresses on context
        set_request_ctx(
            test_chat_id,
            "evm_wallet_address",
            USER_EVM_WALLET_ADDRESS,
        )

        # Call the real agent directly
        try:
            task = test_case["task"]

            # Call the real agent directly
            await call_enso_agent(
                task=task,
                chat_id=test_chat_id,
                use_frontend_quoting=True,
            )

            print(f"    Test Case: {test_case.get('name', 'Unknown')}")
            print(f"    Description: {test_case.get('description', 'N/A')}")
            print(f"    Prompt for agent: {task}")
            expected_functions = [
                call.get("function")
                for call in test_case.get("expected_function_calls", [])
                if isinstance(call, dict) and "function" in call
            ]
            if not expected_functions:
                expected_functions = None
            print(f"    Expected function(s) to be called: {expected_functions}")

        except Exception as e:
            print(f"Error calling real agent: {e}")

        # Get the actual function calls from context
        actual_function_calls = get_request_ctx(test_chat_id, "function_calls") or []

        expected_function_calls = test_case.get("expected_function_calls", [])

        # Normalize function calls for case-insensitive comparison
        normalized_actual = [
            self.normalize_function_call(call) for call in actual_function_calls
        ]
        normalized_expected = [
            self.normalize_function_call(call) for call in expected_function_calls
        ]

        # Compare actual vs expected - exact match (case-insensitive)
        test_passed = normalized_actual == normalized_expected

        print(f"    Result: {'PASS' if test_passed else 'FAIL'}")

        print("  ")
        return {
            "test_name": test_case.get("name", "Unknown"),
            "test_type": test_case.get("description", "N/A"),
            "task": task,
            "function_calls": actual_function_calls,
            "expected_function_calls": expected_function_calls,
            "test_passed": test_passed,
        }

    async def evaluate_enso(self) -> List[Dict]:
        """
        Evaluate enso using all enso test cases categorized by type.
        """
        print("\n[ENSO] Evaluating Enso Agent...")
        results = []
        total_cases = sum(len(cases) for cases in ENSO_TEST_CASES.values())
        current_case = 0

        for category, test_cases in ENSO_TEST_CASES.items():
            print(
                f"\n[CATEGORY] Evaluating {category} tests ({len(test_cases)} cases)..."
            )

            for test_case in test_cases:
                current_case += 1
                print(
                    f"**** Testing case {current_case}/{total_cases}: {test_case['name']} ({category})"
                )

                try:
                    result = await self.evaluate_single_case(test_case)
                    # Add category information to the result
                    result["category"] = category
                    results.append(result)
                except Exception as e:
                    print(f"    [ERROR] Error evaluating {test_case['name']}: {e}")
                    results.append(
                        {
                            "test_name": test_case["name"],
                            "description": test_case["description"],
                            "category": category,
                            "error": str(e),
                            "test_passed": False,
                        }
                    )

                # Add 2-second delay between cases to avoid API rate limiting
                if current_case < total_cases:
                    await asyncio.sleep(2)

        print(
            f"[OK] Completed enso evaluation: {len(results)} cases across {len(ENSO_TEST_CASES)} categories"
        )
        return results

    def _calculate_summary(self, enso_results: List[Dict]) -> Dict:
        """
        Calculate summary statistics from evaluation results by category.
        """
        total_successful_cases = sum(
            1 for r in enso_results if "error" not in r and r.get("test_passed", False)
        )
        total_cases = sum(1 for r in enso_results if "error" not in r)

        success_rate = (
            (total_successful_cases / total_cases * 100) if total_cases > 0 else 0.0
        )

        # Calculate summary by category
        category_summary = {}
        for result in enso_results:
            if "error" not in result:
                category = result.get("category", "UNKNOWN")
                if category not in category_summary:
                    category_summary[category] = {"total": 0, "passed": 0}

                category_summary[category]["total"] += 1
                if result.get("test_passed", False):
                    category_summary[category]["passed"] += 1

        # Calculate success rate for each category
        for category in category_summary:
            total = category_summary[category]["total"]
            passed = category_summary[category]["passed"]
            category_summary[category]["success_rate"] = (
                (passed / total * 100) if total > 0 else 0.0
            )

        return {
            "total_enso_cases": len(enso_results),
            "total_cases": total_cases,
            "total_successful_cases": total_successful_cases,
            "success_rate": success_rate,
            "category_summary": category_summary,
        }

    async def run_full_evaluation(self) -> Dict:
        """
        Run the complete evaluation for Enso Agent
        """
        print("[START] Starting Enso Agent Evaluation...")

        # Run evaluations
        enso_results = await self.evaluate_enso()

        # Calculate summary statistics
        summary = self._calculate_summary(enso_results)

        # Combine results
        all_results = {
            "evaluation_date": datetime.now().isoformat(),
            "enso_results": enso_results,
            "summary": summary,
        }

        return all_results

    def generate_report(self, results: Dict) -> str:
        """
        Generate a human-readable evaluation report with category breakdown.
        """
        report = f"""
Enso Agent Evaluation Report
=========================================

[ENSO] ENSO RESULTS BY CATEGORY:
"""

        # Group results by category
        results_by_category = {}
        for result in results["enso_results"]:
            category = result.get("category", "UNKNOWN")
            if category not in results_by_category:
                results_by_category[category] = []
            results_by_category[category].append(result)

        # Print results by category
        for category in sorted(results_by_category.keys()):
            report += f"\n[{category}] ({len(results_by_category[category])} tests):\n"
            for result in results_by_category[category]:
                if "error" not in result:
                    success = result.get("test_passed", False)
                    report += f"  - {result['test_name']}: {'[OK] PASS' if success else '[ERROR] FAIL'}\n"
                else:
                    report += f"  - {result['test_name']}: ERROR - {result['error']}\n"

        summary = results["summary"]
        report += f"""

[DATA] EVALUATION SUMMARY:
- Total Test Cases: {summary['total_cases']}
- Total Successful Cases: {summary['total_successful_cases']}
- Overall Success Rate: {summary['success_rate']:.2f}%

[CATEGORY BREAKDOWN]:
"""

        # Print category summary
        for category, cat_summary in summary.get("category_summary", {}).items():
            report += f"- {category}: {cat_summary['passed']}/{cat_summary['total']} passed ({cat_summary['success_rate']:.2f}%)\n"

        return report

    def save_results(
        self, results: Dict, filename: str = "enso_evaluation_results.json"
    ):
        """
        Save evaluation results to a JSON file.
        """
        try:
            with open(filename, "w") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"[SAVE] Results saved to {filename}")
        except Exception as e:
            print(f"[ERROR] Error saving results: {e}")


async def run_eval_for_enso_agent():
    # Set up test context for evaluation
    test_chat_id = "enso_eval_test"
    set_context_id(test_chat_id)
    set_request_ctx(test_chat_id, "function_calls", [])  # Array to store function calls

    # Initialize evaluator with real agent
    print("[START] Initializing Enso Agent Evaluation...")
    evaluator = EnsoAgentEval(use_real_agent=True)

    # Run full evaluation
    print("[RUNNING] Starting full evaluation...")
    results = await evaluator.run_full_evaluation()

    # Generate report
    report = evaluator.generate_report(results)
    print("\n[REPORT] Evaluation Report:")
    print(report)

    # Save results
    evaluator.save_results(results)

    return results
