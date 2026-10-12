from faker import Faker
import pandas as pd
import random


# -----------------------------
# 1. Setup
# -----------------------------
fake = Faker("en_IN")
fake.seed_instance(300)
random.seed(300)


# -----------------------------
# 2. Load treatments
# -----------------------------
treatments_df = pd.read_csv(
    "data/treatments.csv"
)

treatments_df["start_date"] = pd.to_datetime(
    treatments_df["start_date"]
)

treatments_df["end_date"] = pd.to_datetime(
    treatments_df["end_date"]
)


# -----------------------------
# 3. Stage definitions
# -----------------------------
ivf_stages = [
    "Initial Consultation",
    "Ovarian Stimulation",
    "Follicle Monitoring",
    "Egg Retrieval",
    "Fertilization",
    "Embryo Development",
    "Embryo Transfer",
    "Pregnancy Test",
]

iui_stages = [
    "Initial Consultation",
    "Ovulation Monitoring",
    "Medication",
    "IUI Procedure",
    "Pregnancy Test",
]

fertility_consultation_stages = [
    "Initial Consultation",
    "Medical Assessment",
    "Diagnostic Review",
    "Treatment Planning",
]

ovulation_stages = [
    "Initial Consultation",
    "Hormonal Monitoring",
    "Medication",
    "Ovulation Monitoring",
    "Outcome Assessment",
]

egg_freezing_stages = [
    "Initial Consultation",
    "Ovarian Stimulation",
    "Follicle Monitoring",
    "Egg Retrieval",
    "Egg Freezing",
]

embryo_freezing_stages = [
    "Initial Consultation",
    "Egg Retrieval",
    "Fertilization",
    "Embryo Development",
    "Embryo Freezing",
]

donor_program_stages = [
    "Initial Consultation",
    "Donor Matching",
    "Medical Assessment",
    "Treatment Preparation",
    "Procedure",
    "Follow-up",
]


# -----------------------------
# 4. Map treatment type → stages
# -----------------------------
stage_map = {
    "IVF": ivf_stages,
    "IUI": iui_stages,
    "Fertility Consultation": fertility_consultation_stages,
    "Ovulation Induction": ovulation_stages,
    "Egg Freezing": egg_freezing_stages,
    "Embryo Freezing": embryo_freezing_stages,
    "Donor Program": donor_program_stages,
}


# -----------------------------
# 5. Possible stage statuses
# -----------------------------
stage_statuses = [
    "Completed",
    "In Progress",
    "Cancelled",
    "Skipped",
]


# -----------------------------
# 6. Generate stages
# -----------------------------
stages = []

stage_counter = 1


for _, treatment in treatments_df.iterrows():

    treatment_id = treatment["treatment_id"]
    treatment_type = treatment["treatment_type"]

    treatment_start = treatment["start_date"]
    treatment_end = treatment["end_date"]
    treatment_status = treatment["status"]

    # Get stages for this treatment type
    stages_for_treatment = stage_map[
        treatment_type
    ]

    number_of_stages = len(
        stages_for_treatment
    )

    total_days = max(
        (treatment_end - treatment_start).days,
        1
    )

    # -----------------------------
    # Generate each stage
    # -----------------------------
    for stage_number, stage_name in enumerate(
        stages_for_treatment,
        start=1
    ):

        # Spread stages across treatment duration
        if number_of_stages == 1:
            days_from_start = 0
        else:
            days_from_start = int(
                (stage_number - 1)
                * total_days
                / (number_of_stages - 1)
            )

        stage_date = (
            treatment_start
            + pd.Timedelta(days=days_from_start)
        )

        # Make sure stage date does not
        # go beyond treatment end date
        if stage_date > treatment_end:
            stage_date = treatment_end

        # -----------------------------
        # Determine stage status
        # -----------------------------

        if treatment_status == "Completed":
            status = "Completed"

        elif treatment_status == "Ongoing":

            if stage_number == 1:
                status = "Completed"
            elif stage_number == 2:
                status = "In Progress"
            else:
                status = "Skipped"

        elif treatment_status == "Cancelled":

            if stage_number == 1:
                status = "Completed"
            else:
                status = "Cancelled"

        else:
            # Paused treatment
            if stage_number <= 2:
                status = "Completed"
            else:
                status = "Skipped"

        stage = {
            "stage_id": f"TS{stage_counter:06d}",
            "treatment_id": treatment_id,
            "stage_number": stage_number,
            "stage_name": stage_name,
            "stage_date": stage_date.date(),
            "status": status,
        }

        stages.append(stage)

        stage_counter += 1


# -----------------------------
# 7. Convert to DataFrame
# -----------------------------
stages_df = pd.DataFrame(stages)


# -----------------------------
# 8. Save CSV
# -----------------------------
stages_df.to_csv(
    "data/treatment_stages.csv",
    index=False
)


# -----------------------------
# 9. Display results
# -----------------------------
print(
    "Treatment stages created:",
    len(stages_df)
)

print("\nFirst 10 stages:")
print(
    stages_df.head(10)
)

print("\nNumber of stages per treatment:")
print(
    stages_df.groupby("treatment_id")
    .size()
    .describe()
)

print("\nMissing values:")
print(
    stages_df.isnull().sum()
)