import pandas as pd
import random
from faker import Faker


# -----------------------------
# 1. Setup
# -----------------------------
fake = Faker("en_IN")
fake.seed_instance(500)
random.seed(500)


# -----------------------------
# 2. Load existing data
# -----------------------------
treatments_df = pd.read_csv(
    "data/treatments.csv"
)

treatment_stages_df = pd.read_csv(
    "data/treatment_stages.csv"
)


# -----------------------------
# 3. Lab test definitions
# -----------------------------
lab_tests = {
    "Hormone Panel": (800, 2500, "ng/dL"),
    "AMH": (1200, 3000, "ng/mL"),
    "FSH": (900, 2200, "mIU/mL"),
    "LH": (900, 2200, "mIU/mL"),
    "Estradiol": (1000, 2800, "pg/mL"),
    "Progesterone": (1000, 2500, "ng/mL"),
    "TSH": (500, 1500, "mIU/L"),
    "Prolactin": (700, 1800, "ng/mL"),
    "CBC": (400, 1200, "cells/uL"),
    "Ultrasound": (1000, 3500, "mm"),
    "Pregnancy Test": (300, 800, "mIU/mL"),
}


# -----------------------------
# 4. Result status
# -----------------------------
result_statuses = [
    "Normal",
    "Abnormal",
    "Borderline",
]


# -----------------------------
# 5. Generate lab tests
# -----------------------------
lab_records = []

lab_counter = 1


for _, treatment in treatments_df.iterrows():

    treatment_id = treatment["treatment_id"]

    treatment_start = pd.to_datetime(
        treatment["start_date"]
    )

    treatment_end = pd.to_datetime(
        treatment["end_date"]
    )

    treatment_type = treatment["treatment_type"]

    # Number of tests for this treatment
    number_of_tests = random.randint(1, 4)

    selected_tests = random.choices(
        list(lab_tests.keys()),
        k=number_of_tests
    )

    for test_name in selected_tests:

        min_cost, max_cost, unit = lab_tests[
            test_name
        ]

        # Generate test date within treatment period
        test_date = fake.date_between_dates(
            treatment_start.date(),
            treatment_end.date()
        )

        # Generate synthetic result
        if test_name == "CBC":
            result_value = round(
                random.uniform(4.0, 15.0),
                2
            )

        elif test_name == "Ultrasound":
            result_value = round(
                random.uniform(5.0, 25.0),
                1
            )

        elif test_name == "Pregnancy Test":
            result_value = round(
                random.uniform(0, 500),
                2
            )

        else:
            result_value = round(
                random.uniform(0.5, 50.0),
                2
            )

        result_status = random.choices(
            result_statuses,
            weights=[75, 15, 10],
            k=1
        )[0]

        lab_record = {
            "lab_test_id": f"LAB{lab_counter:06d}",
            "treatment_id": treatment_id,
            "test_name": test_name,
            "test_date": test_date,
            "result_value": result_value,
            "unit": unit,
            "result_status": result_status,
            "test_cost": random.randint(
                min_cost,
                max_cost
            ),
        }

        lab_records.append(
            lab_record
        )

        lab_counter += 1


# -----------------------------
# 6. Convert to DataFrame
# -----------------------------
lab_tests_df = pd.DataFrame(
    lab_records
)


# -----------------------------
# 7. Save CSV
# -----------------------------
lab_tests_df.to_csv(
    "data/lab_tests.csv",
    index=False
)


# -----------------------------
# 8. Display results
# -----------------------------
print(
    "Lab tests created:",
    len(lab_tests_df)
)

print("\nFirst 10 lab tests:")
print(
    lab_tests_df.head(10)
)

print("\nColumns:")
print(
    lab_tests_df.columns.tolist()
)

print("\nMissing values:")
print(
    lab_tests_df.isnull().sum()
)