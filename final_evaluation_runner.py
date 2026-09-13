import json
import time
from pathlib import Path

from services.claim_service import process_claim


TEST_CASES = [

    # ==================================================
    # SUPPORTED
    # ==================================================

    {
        "claim": "Mount Everest is the highest mountain above sea level.",
        "expected": "SUPPORTED"
    },

    {
        "claim": "Tokyo is the capital of Japan.",
        "expected": "SUPPORTED"
    },

    {
        "claim": "Gold has the chemical symbol Au.",
        "expected": "SUPPORTED"
    },

    {
        "claim": "Saturn has a prominent ring system.",
        "expected": "SUPPORTED"
    },

    {
        "claim": "The human heart has four chambers.",
        "expected": "SUPPORTED"
    },

    {
        "claim": "Photosynthesis allows plants to convert light energy into chemical energy.",
        "expected": "SUPPORTED"
    },

    {
        "claim": "Insulin helps regulate blood glucose levels.",
        "expected": "SUPPORTED"
    },

    {
        "claim": "The Nile River flows through Egypt.",
        "expected": "SUPPORTED"
    },


    # ==================================================
    # REFUTED
    # ==================================================

    {
        "claim": "The Moon is a star.",
        "expected": "REFUTED"
    },

    {
        "claim": "Canberra is the capital of New Zealand.",
        "expected": "REFUTED"
    },

    {
        "claim": "Whales are fish.",
        "expected": "REFUTED"
    },

    {
        "claim": "Antarctica is the hottest continent on Earth.",
        "expected": "REFUTED"
    },

    {
        "claim": "Venus is the farthest planet from the Sun.",
        "expected": "REFUTED"
    },

    {
        "claim": "Humans normally have three hearts.",
        "expected": "REFUTED"
    },

    {
        "claim": "DNA uses uracil instead of thymine.",
        "expected": "REFUTED"
    },

    {
        "claim": "Water normally boils at 50 degrees Celsius at sea level.",
        "expected": "REFUTED"
    },


    # ==================================================
    # INSUFFICIENT
    # ==================================================

    {
        "claim": "Intelligent extraterrestrial life currently exists on Proxima Centauri b.",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "A previously unknown civilization currently lives beneath Antarctica.",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "Humans will permanently live on Mars by 2040.",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "A cure for every type of cancer will be discovered within five years.",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "There is an undiscovered planet containing intelligent human-like life.",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "Scientists will completely eliminate aging in humans before 2050.",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "An unknown species larger than a blue whale currently lives in the deepest ocean.",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "Humans will discover confirmed extraterrestrial intelligence within the next ten years.",
        "expected": "INSUFFICIENT"
    }

]


OUTPUT_FILE = Path(
    "final_evaluation_results.json"
)


def run_evaluation():

    total = len(TEST_CASES)

    correct = 0

    errors = 0

    results = []


    print("\n")
    print("=" * 72)

    print(
        "FINAL FRESH HOLDOUT EVALUATION"
    )

    print("=" * 72)

    print(
        f"Total claims: {total}"
    )

    print(
        "8 SUPPORTED | 8 REFUTED | 8 INSUFFICIENT"
    )

    print("=" * 72)


    for index, test in enumerate(
        TEST_CASES,
        start=1
    ):

        claim = test["claim"]

        expected = test["expected"]


        print("\n")
        print("-" * 72)

        print(
            f"TEST {index}/{total}"
        )

        print(
            f"Claim: {claim}"
        )

        print(
            f"Expected: {expected}"
        )

        print("-" * 72)


        started = time.perf_counter()


        try:

            result = process_claim(
                claim
            )


            predicted = result.get(
                "final_verdict",
                "UNKNOWN"
            )


            confidence = result.get(
                "confidence",
                0.0
            )


            elapsed = (
                time.perf_counter()
                - started
            )


            is_correct = (
                predicted == expected
            )


            if is_correct:

                correct += 1

                outcome = "PASS"

            else:

                outcome = "FAIL"


            print(
                f"Predicted: {predicted}"
            )

            print(
                f"Confidence: {confidence:.4f}"
            )

            print(
                f"Result: {outcome}"
            )

            print(
                f"Time: {elapsed:.2f} seconds"
            )


            results.append(
                {
                    "claim": claim,
                    "expected": expected,
                    "predicted": predicted,
                    "confidence": confidence,
                    "correct": is_correct,
                    "time_seconds": round(
                        elapsed,
                        2
                    )
                }
            )


        except Exception as error:

            errors += 1


            elapsed = (
                time.perf_counter()
                - started
            )


            print(
                "ERROR:"
            )

            print(
                str(error)
            )


            results.append(
                {
                    "claim": claim,
                    "expected": expected,
                    "predicted": "ERROR",
                    "confidence": 0.0,
                    "correct": False,
                    "time_seconds": round(
                        elapsed,
                        2
                    ),
                    "error": str(error)
                }
            )


        # Small pause between external retrieval calls.
        time.sleep(2)


        with open(
            OUTPUT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                results,
                file,
                indent=4,
                ensure_ascii=False
            )


    completed_without_errors = (
        total - errors
    )


    accuracy = (
        correct / total
        * 100
    )


    print("\n")
    print("=" * 72)

    print(
        "FINAL EVALUATION SUMMARY"
    )

    print("=" * 72)

    print(
        f"Total claims: {total}"
    )

    print(
        f"Correct: {correct}"
    )

    print(
        f"Incorrect: {total - correct - errors}"
    )

    print(
        f"Runtime errors: {errors}"
    )

    print(
        f"Completed without errors: {completed_without_errors}"
    )

    print(
        f"Overall accuracy: {accuracy:.2f}%"
    )

    print(
        f"Results saved to: {OUTPUT_FILE}"
    )

    print("=" * 72)


if __name__ == "__main__":

    run_evaluation()