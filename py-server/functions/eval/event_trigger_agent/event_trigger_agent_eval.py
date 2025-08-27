"""
Event Trigger Agent Evaluation using objective comparison.
Evaluates robustness and scalability of the event trigger agent.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple
from utils.firebase import set_request_ctx, set_context_id, get_request_ctx
from eval.event_trigger_agent.test_data import (
    ROBUSTNESS_TEST_CASES,
    SCALABILITY_TEST_CASES,
)

# Import the real agent
from agents.event_trigger_agent.event_trigger_agent import call_event_trigger_agent


class EventTriggerAgentEval:
    """
    Evaluation framework for the Event Trigger Agent using objective comparison.
    Tests robustness and scalability of event detection capabilities.
    """

    def __init__(self, use_real_agent: bool = True):
        """
        Initialize the evaluator.

        Args:
            use_real_agent: If True, calls the real agent. If False, simulates based on ground truth.
        """
        self.use_real_agent = use_real_agent

    async def evaluate_single_case(self, test_case: Dict) -> Dict:
        """
        Evaluate a single test case using objective comparison.
        """
        # Clear previous triggered events from context before this test
        test_chat_id = "event_trigger_eval_test"
        set_request_ctx(test_chat_id, "triggered_events", [])

        # Call the real agent directly
        try:
            tweet_content = test_case["tweet"]["text"]

            # Ensure proper encoding
            if isinstance(tweet_content, str):
                # Convert any problematic characters to safe ASCII
                safe_tweet_content = tweet_content.encode("ascii", "replace").decode(
                    "ascii"
                )
            else:
                safe_tweet_content = str(tweet_content)

            # Prepare the tweet data in the format expected by the real agent
            tweet_data = {
                "username": test_case["tweet"]["username"],
                "tweet_content": safe_tweet_content,  # Use safe version
                "tweet_date": test_case["tweet"]["created_at"],
                "id": test_case["tweet"]["id"],
            }

            # Call the real agent directly
            await call_event_trigger_agent(
                tweet=tweet_data,
                events=test_case["events"],
                chat_id=test_chat_id,
                use_frontend_quoting=False,
                is_evaluation=True,
            )

            print(f"    ")

        except Exception as e:
            print(f"Error calling real agent: {e}")

        # Get the actual triggered events from context
        actual_triggered_events = (
            get_request_ctx(test_chat_id, "triggered_events") or []
        )

        expected_events = test_case.get("expected_triggers", [])

        # Compare actual vs expected by comparing each field individually
        def compare_events(actual, expected):
            """Compare two event objects by their individual fields"""
            return (
                actual.get("eventId") == expected.get("eventId")
                and actual.get("tweetContent") == expected.get("tweetContent")
                and actual.get("username") == expected.get("username")
                and actual.get("tweetId") == expected.get("tweetId")
            )

        # Find matching events
        correct_triggered = []
        false_positives = []
        false_negatives = []

        # Check for correct matches and false positives
        for actual_event in actual_triggered_events:
            found_match = False
            for expected_event in expected_events:
                if compare_events(actual_event, expected_event):
                    correct_triggered.append(actual_event)
                    found_match = True
                    break
            if not found_match:
                false_positives.append(actual_event)

        # Check for false negatives (expected but not found)
        for expected_event in expected_events:
            found_match = False
            for actual_event in actual_triggered_events:
                if compare_events(actual_event, expected_event):
                    found_match = True
                    break
            if not found_match:
                false_negatives.append(expected_event)

        # Determine if test passed
        test_passed = len(false_positives) == 0 and len(false_negatives) == 0

        # Calculate precision, recall, and F1 score
        precision = (
            len(correct_triggered) / len(actual_triggered_events)
            if actual_triggered_events
            else 1.0
        )
        recall = (
            len(correct_triggered) / len(expected_events) if expected_events else 1.0
        )

        print(f"   Test Case: {test_case.get('name', 'Unknown')}")
        print(f"   Tweet Content: {tweet_content}")
        print(f"   Expected Triggers: {len(expected_events)} events")
        print(f"   Agent Triggers: {len(actual_triggered_events)} events")
        print(f"   Result: {'PASS' if test_passed else 'FAIL'}")
        print(f"   Precision: {precision:.3f}, Recall: {recall:.3f}")
        if not test_passed:
            if false_positives:
                print(f"   False Positives: {len(false_positives)} events")
                for fp in false_positives:
                    print(
                        f"     - {fp.get('eventId', 'Unknown')} (tweet: {fp.get('tweetId', 'Unknown')})"
                    )
            if false_negatives:
                print(f"   False Negatives: {len(false_negatives)} events")
                for fn in false_negatives:
                    print(
                        f"     - {fn.get('eventId', 'Unknown')} (tweet: {fn.get('tweetId', 'Unknown')})"
                    )

        print("  ")
        return {
            "test_name": test_case.get("name", "Unknown"),
            "test_type": test_case.get("description", "N/A"),
            "tweet_content": tweet_content,
            "triggered_events": actual_triggered_events,
            "expected_events": expected_events,
            "test_passed": test_passed,
            "precision": precision,
            "recall": recall,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "correct_triggered": correct_triggered,
        }

    async def evaluate_robustness(self) -> List[Dict]:
        """
        Evaluate robustness using all robustness test cases.
        """
        print("\n[ROBUST] Evaluating Robustness...")
        results = []

        for i, test_case in enumerate(ROBUSTNESS_TEST_CASES, 1):
            print(
                f"**** Testing case {i}/{len(ROBUSTNESS_TEST_CASES)}: {test_case['name']}"
            )

            try:
                result = await self.evaluate_single_case(test_case)
                results.append(result)
            except Exception as e:
                print(f"    [ERROR] Error evaluating {test_case['name']}: {e}")
                results.append(
                    {
                        "test_name": test_case["name"],
                        "test_type": "robustness",
                        "description": test_case["description"],
                        "error": str(e),
                        "test_passed": False,
                        "precision": 0.0,
                        "recall": 0.0,
                    }
                )

            # Add 3-second delay between cases to avoid API rate limiting
            if i < len(ROBUSTNESS_TEST_CASES):
                await asyncio.sleep(3)

        print(f"[OK] Completed robustness evaluation: {len(results)} cases")
        return results

    async def evaluate_scalability(self) -> List[Dict]:
        """
        Evaluate scalability using scalability test cases with different event counts.
        """
        print("\n[SCALE] Evaluating Scalability...")
        results = []

        for test_case in SCALABILITY_TEST_CASES:
            # Test with different numbers of events
            print(f"****  Testing case: {test_case['name']}")
            for event_count in [1, 5, 10, 20]:
                try:
                    print(f"---- Testing with {event_count} events")
                    # Create modified test case with specific event count
                    events_key = f"events_{event_count}"
                    if events_key in test_case:
                        modified_case = {**test_case, "events": test_case[events_key]}
                        result = await self.evaluate_single_case(modified_case)
                        result["event_count"] = event_count
                        result["test_type"] = "scalability"
                        results.append(result)
                except Exception as e:
                    print(
                        f"    [ERROR] Error evaluating {test_case['name']} with {event_count} events: {e}"
                    )
                    results.append(
                        {
                            "test_name": test_case["name"],
                            "event_count": event_count,
                            "test_type": "scalability",
                            "description": test_case["description"],
                            "error": str(e),
                            "test_passed": False,
                            "precision": 0.0,
                            "recall": 0.0,
                        }
                    )

                # Add 3-second delay between cases to avoid API rate limiting
                if event_count < 20:  # Don't wait after the last event count
                    await asyncio.sleep(3)

        print(f"[OK] Completed scalability evaluation: {len(results)} cases")
        return results

    async def run_full_evaluation(self) -> Dict:
        """
        Run the complete evaluation including robustness and scalability.
        """
        print("[START] Starting Event Trigger Agent Evaluation...")

        # Run evaluations
        robustness_results = await self.evaluate_robustness()
        scalability_results = await self.evaluate_scalability()

        # Calculate summary statistics
        total_successfull_cases = 0
        total_precision = 0.0
        total_recall = 0.0
        total_cases = 0

        for result in robustness_results + scalability_results:
            if "error" not in result:
                total_cases += 1
                if result.get("test_passed", False):
                    total_successfull_cases += 1
                total_precision += result.get("precision", 0.0)
                total_recall += result.get("recall", 0.0)

        avg_precision = (
            (total_precision / total_cases * 100) if total_cases > 0 else 0.0
        )
        avg_recall = (total_recall / total_cases * 100) if total_cases > 0 else 0.0
        success_rate = (
            (total_successfull_cases / total_cases * 100) if total_cases > 0 else 0.0
        )

        # Combine results
        all_results = {
            "evaluation_date": datetime.now().isoformat(),
            "robustness_results": robustness_results,
            "scalability_results": scalability_results,
            "summary": {
                "total_robustness_cases": len(robustness_results),
                "total_scalability_cases": len(scalability_results),
                "total_cases": total_cases,
                "total_successfull_cases": total_successfull_cases,
                "success_rate": success_rate,
                "average_precision": avg_precision,
                "average_recall": avg_recall,
            },
        }

        return all_results

    def generate_report(self, results: Dict) -> str:
        """
        Generate a human-readable evaluation report.
        """
        report = f"""
Event Trigger Agent Evaluation Report
=========================================

[ROBUST] ROBUSTNESS RESULTS:
"""

        for result in results["robustness_results"]:
            if "error" not in result:
                success = result.get("test_passed", False)
                precision = result.get("precision", 0.0)
                recall = result.get("recall", 0.0)
                report += f"- {result['test_name']}: {'[OK] PASS' if success else '[ERROR] FAIL'} (P:{precision:.3f}, R:{recall:.3f})\n"
            else:
                report += f"- {result['test_name']}: ERROR - {result['error']}\n"

        report += f"""
[SCALE] SCALABILITY RESULTS:
"""

        # Group scalability results by test name
        scalability_by_test = {}
        for result in results["scalability_results"]:
            test_name = result["test_name"]
            if test_name not in scalability_by_test:
                scalability_by_test[test_name] = {}
            scalability_by_test[test_name][result["event_count"]] = result

        for test_name, event_results in scalability_by_test.items():
            report += f"- {test_name}:\n"
            for event_count in [1, 5, 10, 20]:
                if event_count in event_results:
                    result = event_results[event_count]
                    if "error" not in result:
                        success = result.get("test_passed", False)
                        precision = result.get("precision", 0.0)
                        recall = result.get("recall", 0.0)
                        report += f"  {event_count} events: {'[OK] PASS' if success else '[ERROR] FAIL'} (P:{precision:.3f}, R:{recall:.3f})\n"
                    else:
                        report += f"  {event_count} events: ERROR\n"

        summary = results["summary"]
        report += f"""

[DATA] EVALUATION SUMMARY:
- Total Test Cases: {summary['total_cases']}
- Robustness Cases: {summary['total_robustness_cases']}
- Scalability Cases: {summary['total_scalability_cases']}
- Total Successful Cases: {summary['total_successfull_cases']}
- Success Rate: {summary['success_rate']:.2f}%
- Average Precision: {summary['average_precision']:.2f}%
- Average Recall: {summary['average_recall']:.2f}%
"""

        return report

    def save_results(self, results: Dict, filename: str = "evaluation_results.json"):
        """
        Save evaluation results to a JSON file.
        """
        try:
            with open(filename, "w") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"[SAVE] Results saved to {filename}")
        except Exception as e:
            print(f"[ERROR] Error saving results: {e}")


async def run_eval_for_event_trigger_agent():
    # Set up test context for evaluation
    test_chat_id = "event_trigger_eval_test"
    set_context_id(test_chat_id)
    set_request_ctx(test_chat_id, "triggered_event_ids", [])  # Array to store event IDs

    # Initialize evaluator with real agent
    print("[START] Initializing Event Trigger Agent Evaluation...")
    evaluator = EventTriggerAgentEval(use_real_agent=True)

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
