import time
from services.claim_service import process_claim


# ============================================================
# UNSEEN EVALUATION SET
# ============================================================
#
# IMPORTANT:
# These claims should NOT be used for tuning before the first run.
#
# 10 SUPPORTED
# 10 REFUTED
# 10 INSUFFICIENT
#
# Total = 30 claims
# ============================================================

TEST_CASES = [

    # ========================================================
    # SUPPORTED CLAIMS
    # ========================================================

    {
        "claim": "Mars is known as the Red Planet",
        "expected": "SUPPORTED"
    },

    {
        "claim": "The human body has two lungs",
        "expected": "SUPPORTED"
    },

    {
        "claim": "Jupiter is the largest planet in the Solar System",
        "expected": "SUPPORTED"
    },

    {
        "claim": "The Nile River flows through Egypt",
        "expected": "SUPPORTED"
    },

    {
        "claim": "The human brain is part of the nervous system",
        "expected": "SUPPORTED"
    },

    {
        "claim": "Venus is hotter than Earth",
        "expected": "SUPPORTED"
    },

    {
        "claim": "Insulin helps regulate blood glucose levels",
        "expected": "SUPPORTED"
    },

    {
        "claim": "The Amazon rainforest is located in South America",
        "expected": "SUPPORTED"
    },

    {
        "claim": "The adult human skeleton normally has 206 bones",
        "expected": "SUPPORTED"
    },

    {
        "claim": "Earth has one natural satellite called the Moon",
        "expected": "SUPPORTED"
    },


    # ========================================================
    # REFUTED CLAIMS
    # ========================================================

    {
        "claim": "Venus is the largest planet in the Solar System",
        "expected": "REFUTED"
    },

    {
        "claim": "Humans normally have five lungs",
        "expected": "REFUTED"
    },

    {
        "claim": "The Moon is larger than Earth",
        "expected": "REFUTED"
    },

    {
        "claim": "Jupiter is smaller than Mercury",
        "expected": "REFUTED"
    },

    {
        "claim": "The human heart is located inside the skull",
        "expected": "REFUTED"
    },

    {
        "claim": "The Sahara Desert is located in South America",
        "expected": "REFUTED"
    },

    {
        "claim": "Penguins are native to the Arctic",
        "expected": "REFUTED"
    },

    {
        "claim": "Water is made only of carbon and nitrogen",
        "expected": "REFUTED"
    },

    {
        "claim": "The Sun is a planet",
        "expected": "REFUTED"
    },

    {
        "claim": "Humans can survive indefinitely without oxygen",
        "expected": "REFUTED"
    },


    # ========================================================
    # INSUFFICIENT CLAIMS
    # ========================================================
    #
    # These are deliberately subjective, universal,
    # predictive, vague, or otherwise difficult to establish
    # as objective factual statements.
    # ========================================================

    {
        "claim": "Chocolate makes every person happier",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "Listening to classical music guarantees better memory",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "Every person who wakes up early becomes successful",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "Using social media always makes people unhappy",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "Playing video games guarantees higher intelligence",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "Every student who studies at night gets better grades",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "Drinking tea makes every person more creative",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "People who wear blue clothes are more trustworthy",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "Watching comedy movies guarantees a longer life",
        "expected": "INSUFFICIENT"
    },

    {
        "claim": "Every person who owns a pet is happier than people without pets",
        "expected": "INSUFFICIENT"
    }
]


# ============================================================
# CLASS STATISTICS
# ============================================================

CLASS_NAMES = [
    "SUPPORTED",
    "REFUTED",
    "INSUFFICIENT"
]


def create_class_stats():

    return {
        class_name: {
            "total": 0,
            "correct": 0
        }
        for class_name in CLASS_NAMES
    }


# ============================================================
# RUN EVALUATION
# ============================================================

def run_evaluation():

    total_claims = len(TEST_CASES)

    completed_predictions = 0
    errors = 0
    correct = 0

    class_stats = create_class_stats()

    failed_cases = []

    print("=" * 80)
    print("UNSEEN EVALUATION")
    print("=" * 80)

    print(
        f"\nTotal unseen claims: {total_claims}"
    )

    print(
        "\nIMPORTANT: Do not change the model during this run."
    )

    print(
        "This test measures generalization on claims not used during tuning."
    )

    print("\n" + "=" * 80)

    # --------------------------------------------------------
    # PROCESS EACH CLAIM
    # --------------------------------------------------------

    for index, test_case in enumerate(
        TEST_CASES,
        start=1
    ):

        claim = test_case["claim"]
        expected = test_case["expected"]

        class_stats[
            expected
        ][
            "total"
        ] += 1

        print(
            f"\n[{index}/{total_claims}]"
        )

        print(
            f"Claim: {claim}"
        )

        print(
            f"Expected: {expected}"
        )

        try:

            result = process_claim(
                claim
            )

            completed_predictions += 1

            predicted = result.get(
                "final_verdict",
                "UNKNOWN"
            )

            confidence = result.get(
                "confidence",
                0.0
            )

            decision_margin = result.get(
                "decision_margin",
                0.0
            )

            print(
                f"Predicted: {predicted}"
            )

            print(
                f"Confidence: {confidence:.4f}"
            )

            print(
                f"Decision Margin: {decision_margin:.4f}"
            )

            # ------------------------------------------------
            # CORRECT PREDICTION
            # ------------------------------------------------

            if predicted == expected:

                correct += 1

                class_stats[
                    expected
                ][
                    "correct"
                ] += 1

                print(
                    "Result: CORRECT"
                )

            # ------------------------------------------------
            # INCORRECT PREDICTION
            # ------------------------------------------------

            else:

                print(
                    "Result: INCORRECT"
                )

                failed_cases.append({
                    "claim": claim,
                    "expected": expected,
                    "predicted": predicted,
                    "confidence": confidence,
                    "decision_margin": (
                        decision_margin
                    ),
                    "decision_reason": (
                        result.get(
                            "decision_reason",
                            ""
                        )
                    ),
                    "search_queries": (
                        result.get(
                            "search_queries",
                            []
                        )
                    )
                })

        # ----------------------------------------------------
        # ERROR HANDLING
        # ----------------------------------------------------

        except Exception as error:

            errors += 1

            print(
                f"ERROR: {error}"
            )

            failed_cases.append({
                "claim": claim,
                "expected": expected,
                "predicted": "ERROR",
                "confidence": 0.0,
                "decision_margin": 0.0,
                "decision_reason": str(
                    error
                ),
                "search_queries": []
            })

        # ----------------------------------------------------
        # RATE LIMIT PROTECTION
        # ----------------------------------------------------

        if index < total_claims:

            print(
                "\nWaiting 4 seconds before next claim..."
            )

            time.sleep(
                4
            )


    # ========================================================
    # FINAL METRICS
    # ========================================================

    incorrect_or_error = (
        total_claims
        - correct
    )

    overall_accuracy = (
        correct
        / total_claims
        * 100
    )

    if completed_predictions > 0:

        completed_accuracy = (
            correct
            / completed_predictions
            * 100
        )

    else:

        completed_accuracy = 0.0


    # ========================================================
    # PRINT FINAL RESULTS
    # ========================================================

    print(
        "\n\n"
        + "=" * 80
    )

    print(
        "FINAL RESULTS"
    )

    print(
        "=" * 80
    )

    print(
        f"Total Claims: {total_claims}"
    )

    print(
        f"Completed Predictions: {completed_predictions}"
    )

    print(
        f"Errors: {errors}"
    )

    print(
        f"Correct: {correct}"
    )

    print(
        f"Incorrect or Error: {incorrect_or_error}"
    )

    print(
        f"Overall Accuracy: {overall_accuracy:.2f}%"
    )

    print(
        "Accuracy on Completed Predictions: "
        f"{completed_accuracy:.2f}%"
    )


    # ========================================================
    # PER-CLASS RESULTS
    # ========================================================

    print(
        "\n\nPER-CLASS RESULTS"
    )

    print(
        "-" * 80
    )

    for class_name in CLASS_NAMES:

        total_for_class = (
            class_stats[
                class_name
            ][
                "total"
            ]
        )

        correct_for_class = (
            class_stats[
                class_name
            ][
                "correct"
            ]
        )

        if total_for_class > 0:

            class_accuracy = (
                correct_for_class
                / total_for_class
                * 100
            )

        else:

            class_accuracy = 0.0

        print(
            f"{class_name}: "
            f"{correct_for_class}/"
            f"{total_for_class} "
            f"({class_accuracy:.2f}%)"
        )


    # ========================================================
    # FAILED CASES
    # ========================================================

    print(
        "\n\n"
        + "=" * 80
    )

    print(
        "FAILED CASES"
    )

    print(
        "=" * 80
    )

    if not failed_cases:

        print(
            "\nNo failed cases."
        )

    else:

        for failed_case in failed_cases:

            print(
                f"\nClaim: "
                f"{failed_case['claim']}"
            )

            print(
                f"Expected: "
                f"{failed_case['expected']}"
            )

            print(
                f"Predicted: "
                f"{failed_case['predicted']}"
            )

            print(
                "Confidence: "
                f"{failed_case['confidence']:.4f}"
            )

            print(
                "Decision Margin: "
                f"{failed_case['decision_margin']:.4f}"
            )

            print(
                "Decision Reason: "
                f"{failed_case['decision_reason']}"
            )

            print(
                "Search Queries: "
                f"{failed_case['search_queries']}"
            )

            print(
                "-" * 80
            )


    print(
        "\n"
        + "=" * 80
    )

    print(
        "UNSEEN EVALUATION COMPLETE"
    )

    print(
        "=" * 80
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_evaluation()