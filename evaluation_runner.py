import time

from services.claim_service import process_claim


TEST_CASES = [
    {
        "claim": "The Earth revolves around the Sun",
        "expected": "SUPPORTED"
    },
    {
        "claim": "The Sun revolves around the Earth",
        "expected": "REFUTED"
    },
    {
        "claim": "The Moon is made of cheese",
        "expected": "REFUTED"
    },
    {
        "claim": "Smoking increases the risk of lung cancer",
        "expected": "SUPPORTED"
    },
    {
        "claim": "Passive smoking increases the risk of lung cancer",
        "expected": "SUPPORTED"
    },
    {
        "claim": "The Earth is flat",
        "expected": "REFUTED"
    },
    {
        "claim": "Water is composed of hydrogen and oxygen",
        "expected": "SUPPORTED"
    },
    {
        "claim": "Humans can breathe normally in outer space without equipment",
        "expected": "REFUTED"
    },
    {
        "claim": "The human heart pumps blood through the body",
        "expected": "SUPPORTED"
    },
    {
        "claim": "The Pacific Ocean is larger than the Atlantic Ocean",
        "expected": "SUPPORTED"
    },
    {
        "claim": "The Great Wall of China is visible from the Moon with the naked eye",
        "expected": "REFUTED"
    },
    {
        "claim": "Antibiotics are effective against viral infections such as the common cold",
        "expected": "REFUTED"
    },
    {
        "claim": "Vaccines can stimulate an immune response",
        "expected": "SUPPORTED"
    },
    {
        "claim": "The Sahara is the largest hot desert in the world",
        "expected": "SUPPORTED"
    },
    {
        "claim": "Humans have three hearts",
        "expected": "REFUTED"
    },
    {
        "claim": "Drinking coffee makes every person more intelligent",
        "expected": "INSUFFICIENT"
    },
    {
        "claim": "Every person who exercises daily will live past 100 years",
        "expected": "INSUFFICIENT"
    },
    {
        "claim": "Listening to music guarantees higher exam scores",
        "expected": "INSUFFICIENT"
    },
    {
        "claim": "Every person who drinks green tea will lose weight",
        "expected": "INSUFFICIENT"
    },
    {
        "claim": "Using a smartphone makes every person less intelligent",
        "expected": "INSUFFICIENT"
    }
]


def run_evaluation():

    total = len(TEST_CASES)
    correct = 0
    completed = 0
    errors = 0

    class_stats = {
        "SUPPORTED": {
            "total": 0,
            "correct": 0
        },
        "REFUTED": {
            "total": 0,
            "correct": 0
        },
        "INSUFFICIENT": {
            "total": 0,
            "correct": 0
        }
    }

    failed_cases = []

    print("\n")
    print("=" * 80)
    print("AI FACT CHECKING SYSTEM - EVALUATION")
    print("=" * 80)

    for index, test_case in enumerate(
        TEST_CASES,
        start=1
    ):

        claim = test_case["claim"]
        expected = test_case["expected"]

        print(
            f"\n[{index}/{total}] Testing:"
        )

        print(
            claim
        )

        class_stats[
            expected
        ]["total"] += 1

        try:

            result = process_claim(
                claim
            )

            completed += 1

            predicted = result[
                "final_verdict"
            ]

            confidence = result[
                "confidence"
            ]

            decision_margin = result[
                "decision_margin"
            ]

            is_correct = (
                predicted == expected
            )

            if is_correct:

                correct += 1

                class_stats[
                    expected
                ]["correct"] += 1

                result_status = "CORRECT"

            else:

                result_status = "WRONG"

                failed_cases.append({
                    "claim": claim,
                    "expected": expected,
                    "predicted": predicted,
                    "confidence": confidence,
                    "decision_margin": (
                        decision_margin
                    )
                })

            print(
                f"Expected:   {expected}"
            )

            print(
                f"Predicted:  {predicted}"
            )

            print(
                f"Confidence: {confidence:.4f}"
            )

            print(
                f"Margin:     {decision_margin:.4f}"
            )

            print(
                f"Result:     {result_status}"
            )

        except Exception as error:

            errors += 1

            print(
                "ERROR:"
            )

            print(
                error
            )

            failed_cases.append({
                "claim": claim,
                "expected": expected,
                "predicted": "ERROR",
                "confidence": 0.0,
                "decision_margin": 0.0
            })

        # -----------------------------------------
        # SHORT PAUSE BETWEEN CLAIMS
        # -----------------------------------------

        if index < total:

            print(
                "\nWaiting 4 seconds before next claim..."
            )

            time.sleep(4)

    overall_accuracy = (
        correct / total
    ) * 100

    if completed > 0:

        completed_accuracy = (
            correct / completed
        ) * 100

    else:

        completed_accuracy = 0.0

    print("\n")
    print("=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)

    print(
        f"Total Claims: {total}"
    )

    print(
        f"Completed Predictions: {completed}"
    )

    print(
        f"Errors: {errors}"
    )

    print(
        f"Correct: {correct}"
    )

    print(
        f"Incorrect or Error: {total - correct}"
    )

    print(
        f"Overall Accuracy: {overall_accuracy:.2f}%"
    )

    print(
        f"Accuracy on Completed Predictions: "
        f"{completed_accuracy:.2f}%"
    )

    print("\n")
    print("PER-CLASS RESULTS")
    print("-" * 80)

    for label, stats in class_stats.items():

        class_total = stats["total"]
        class_correct = stats["correct"]

        if class_total > 0:

            class_accuracy = (
                class_correct
                / class_total
            ) * 100

        else:

            class_accuracy = 0.0

        print(
            f"{label}: "
            f"{class_correct}/{class_total} "
            f"({class_accuracy:.2f}%)"
        )

    if failed_cases:

        print("\n")
        print("=" * 80)
        print("FAILED CASES")
        print("=" * 80)

        for case in failed_cases:

            print(
                f"\nClaim: {case['claim']}"
            )

            print(
                f"Expected: {case['expected']}"
            )

            print(
                f"Predicted: {case['predicted']}"
            )

            print(
                f"Confidence: "
                f"{case['confidence']:.4f}"
            )

            print(
                f"Decision Margin: "
                f"{case['decision_margin']:.4f}"
            )

    print("\n")
    print("=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":

    run_evaluation()