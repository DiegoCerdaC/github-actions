"""
Unified Transfer Agent Evaluation using objective comparison.
Evaluates if the agent calls the correct transfer function with correct parameters.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple
from utils.firebase import set_request_ctx, set_context_id, get_request_ctx
from eval.unified_transfer.test_data import (
    USER_EVM_WALLET_ADDRESS,
    USER_SOLANA_WALLET_ADDRESS,
    TRANSFER_TEST_CASES,
)

# Import the real agent
from agents.unified_transfer.unified_transfer_agent import call_unified_transfer_agent


class UnifiedTransferAgentEval:
    """
    Evaluation framework for the Unified Transfer Agent using objective comparison.
    Tests if the agent calls the correct transfer function with correct parameters.
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
        test_chat_id = "unified_transfer_eval_test"
        set_request_ctx(test_chat_id, "function_calls", [])
        set_request_ctx(test_chat_id, "evaluation_mode", True)  # Set evaluation mode

        # Set solana_usdc_balance only if specified in the test case
        if "solana_usdc_balance" in test_case:
            print("Setting solana_usdc_balance", test_case["solana_usdc_balance"])
            set_request_ctx(
                test_chat_id, "solana_usdc_balance", test_case["solana_usdc_balance"]
            )

        # Set wallet addresses on context
        set_request_ctx(
            test_chat_id,
            "evm_wallet_address",
            USER_EVM_WALLET_ADDRESS,
        )
        set_request_ctx(
            test_chat_id,
            "solana_wallet_address",
            USER_SOLANA_WALLET_ADDRESS,
        )

        # Call the real agent directly
        try:
            task = test_case["task"]

            # Call the real agent directly
            result = await call_unified_transfer_agent(
                task=task,
                chat_id=test_chat_id,
                use_frontend_quoting=False,
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

    async def evaluate_transfers(self) -> List[Dict]:
        """
        Evaluate transfer using all transfer test cases.
        """
        print("\n[TRANSFER] Evaluating Transfer...")
        results = []

        for i, test_case in enumerate(TRANSFER_TEST_CASES, 1):
            print(
                f"**** Testing case {i}/{len(TRANSFER_TEST_CASES)}: {test_case['name']}"
            )

            try:
                result = await self.evaluate_single_case(test_case)
                results.append(result)
            except Exception as e:
                print(f"    [ERROR] Error evaluating {test_case['name']}: {e}")
                results.append(
                    {
                        "test_name": test_case["name"],
                        "test_type": "transfer",
                        "description": test_case["description"],
                        "error": str(e),
                        "test_passed": False,
                    }
                )

            # Add 3-second delay between cases to avoid API rate limiting
            if i < len(TRANSFER_TEST_CASES):
                await asyncio.sleep(3)

        print(f"[OK] Completed transfer evaluation: {len(results)} cases")
        return results

    def _calculate_summary(self, transfer_results: List[Dict]) -> Dict:
        """
        Calculate summary statistics from evaluation results.
        """
        total_successful_cases = sum(
            1
            for r in transfer_results
            if "error" not in r and r.get("test_passed", False)
        )
        total_cases = sum(1 for r in transfer_results if "error" not in r)

        success_rate = (
            (total_successful_cases / total_cases * 100) if total_cases > 0 else 0.0
        )

        return {
            "total_transfer_cases": len(transfer_results),
            "total_cases": total_cases,
            "total_successful_cases": total_successful_cases,
            "success_rate": success_rate,
        }

    async def run_full_evaluation(self) -> Dict:
        """
        Run the complete evaluation including transfer.
        """
        print("[START] Starting Unified Transfer Agent Evaluation...")

        # Run evaluations
        transfer_results = await self.evaluate_transfers()

        # Calculate summary statistics
        summary = self._calculate_summary(transfer_results)

        # Combine results
        all_results = {
            "evaluation_date": datetime.now().isoformat(),
            "transfer_results": transfer_results,
            "summary": summary,
        }

        return all_results

    def generate_report(self, results: Dict) -> str:
        """
        Generate a human-readable evaluation report.
        """
        report = f"""
Unified Transfer Agent Evaluation Report
=========================================

[TRANSFER] TRANSFER RESULTS:
"""

        for result in results["transfer_results"]:
            if "error" not in result:
                success = result.get("test_passed", False)
                report += f"- {result['test_name']}: {'[OK] PASS' if success else '[ERROR] FAIL'}\n"
            else:
                report += f"- {result['test_name']}: ERROR - {result['error']}\n"

        summary = results["summary"]
        report += f"""

[DATA] EVALUATION SUMMARY:
- Total Test Cases: {summary['total_cases']}
- Transfer Cases: {summary['total_transfer_cases']}
- Total Successful Cases: {summary['total_successful_cases']}
- Success Rate: {summary['success_rate']:.2f}%
"""

        return report

    def save_results(
        self, results: Dict, filename: str = "unified_transfer_evaluation_results.json"
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


async def run_eval_for_unified_transfer_agent():
    # Set up test context for evaluation
    test_chat_id = "unified_transfer_eval_test"
    set_context_id(test_chat_id)
    set_request_ctx(test_chat_id, "function_calls", [])  # Array to store function calls

    # Initialize evaluator with real agent
    print("[START] Initializing Unified Transfer Agent Evaluation...")
    evaluator = UnifiedTransferAgentEval(use_real_agent=True)

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
