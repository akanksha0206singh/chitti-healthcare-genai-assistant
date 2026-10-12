from faker import Faker
import pandas as pd
import random
from datetime import date


# -----------------------------
# 1. Setup
# -----------------------------
fake = Faker("en_IN")
fake.seed_instance(200)
random.seed(200)


# -----------------------------
# 2. Number of treatments
# -----------------------------
NUMBER_OF_TREATMENTS = 12_000


# -----------------------------
# 3. Load existing datasets
# -----------------------------
patients_df = pd.read_csv("data/patients.csv")
doctors_df = pd.read_csv("data/doctors.csv")


# Convert dates
patients_df["registration_date"] = pd.to_datetime(
    patients_df["registration_date"]
)

doctors_df["joining_date"] = pd.to_datetime(
    doctors_df["joining_date"]
)


# -----------------------------
# 4. Treatment types
# -----------------------------
treatment_types = [
    "IVF",
    "IUI",
    "Fertility Consultation",
    "Ovulation Induction",
    "Egg Freezing",
    "Embryo Freezing",
    "Donor Program",
]


# -----------------------------
# 5. Treatment statuses
# -----------------------------
treatment_statuses = [
    "Ongoing",
    "Completed",
    "Cancelled",
    "Paused",
]


# -----------------------------
# 6. Treatment outcomes
# -----------------------------
treatment_outcomes = [
    "Successful",
    "Unsuccessful",
    "In Progress",
    "Not Applicable",
]


# -----------------------------
# 7. Generate treatments
# -----------------------------
treatments = []

for i in range(1, NUMBER_OF_TREATMENTS + 1):

    # Select a patient
    patient = patients_df.iloc[
        random.randint(0, len(patients_df) - 1)
    ]

    patient_id = patient["patient_id"]
    registration_date = patient["registration_date"]

    # Select a doctor
    doctor = doctors_df.iloc[
        random.randint(0, len(doctors_df) - 1)
    ]

    doctor_id = doctor["doctor_id"]
    clinic_id = doctor["clinic_id"]
    doctor_joining_date = doctor["joining_date"]

    # Treatment should start after both
    # patient registration and doctor joining
    start_date = max(
        registration_date,
        doctor_joining_date
    )

    end_date_limit = pd.Timestamp("2026-09-30")

    # Generate treatment start date
    treatment_start = fake.date_between_dates(
        start_date.date(),
        end_date_limit.date()
    )

    treatment_start = pd.Timestamp(treatment_start)

    # Treatment duration
    duration_days = random.randint(15, 180)

    treatment_end = treatment_start + pd.Timedelta(
        days=duration_days
    )

    # Do not allow treatment to extend beyond
    # our project data period
    if treatment_end > end_date_limit:
        treatment_end = end_date_limit

    # Determine status
    status = random.choice(treatment_statuses)

    # Outcome
    if status == "Completed":
        outcome = random.choice([
            "Successful",
            "Unsuccessful"
        ])
    elif status == "Ongoing":
        outcome = "In Progress"
    else:
        outcome = "Not Applicable"

    treatment = {
        "treatment_id": f"T{i:05d}",
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "clinic_id": clinic_id,
        "treatment_type": random.choice(treatment_types),
        "start_date": treatment_start.date(),
        "end_date": treatment_end.date(),
        "status": status,
        "outcome": outcome,
        "estimated_cost": random.randint(
            25_000,
            3_00_000
        ),
    }

    treatments.append(treatment)


# -----------------------------
# 8. Convert to DataFrame
# -----------------------------
treatments_df = pd.DataFrame(treatments)


# -----------------------------
# 9. Save CSV
# -----------------------------
treatments_df.to_csv(
    "data/treatments.csv",
    index=False
)


# -----------------------------
# 10. Display results
# -----------------------------
print(
    "Treatments created:",
    len(treatments_df)
)

print("\nFirst 5 treatments:")
print(treatments_df.head())

print("\nColumns:")
print(treatments_df.columns.tolist())

print("\nMissing values:")
print(treatments_df.isnull().sum())