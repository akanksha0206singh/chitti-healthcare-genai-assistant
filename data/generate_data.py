from pathlib import Path
from faker import Faker
import pandas as pd
import random
from datetime import date


# -----------------------------
# 1. Create Faker + random seed
# -----------------------------
fake = Faker("en_IN")
fake.seed_instance(42)
random.seed(42)


# -----------------------------
# 2. Dataset size
# -----------------------------
NUMBER_OF_PATIENTS = 10_000


# -----------------------------
# 3. Controlled healthcare data
# -----------------------------
locations = [
    ("Udaipur", "Rajasthan"),
    ("Jaipur", "Rajasthan"),
    ("Jodhpur", "Rajasthan"),
    ("Kota", "Rajasthan"),
    ("Ahmedabad", "Gujarat"),
    ("Surat", "Gujarat"),
    ("Mumbai", "Maharashtra"),
    ("Pune", "Maharashtra"),
    ("Delhi", "Delhi"),
    ("Lucknow", "Uttar Pradesh"),
    ("Patna", "Bihar"),
    ("Chandigarh", "Chandigarh"),
    ("Bengaluru", "Karnataka"),
    ("Hyderabad", "Telangana"),
    ("Indore", "Madhya Pradesh"),
]

genders = [
    "Female",
    "Male",
    "Other"
]

blood_groups = [
    "A+", "A-", "B+", "B-",
    "O+", "O-", "AB+", "AB-"
]

languages = [
    "Hindi",
    "English",
    "Gujarati",
    "Marathi",
    "Punjabi",
    "Bengali",
]

registration_channels = [
    "Website",
    "Mobile App",
    "Walk-in",
    "Doctor Referral",
    "Phone",
    "Camp",
]

patient_statuses = [
    "Active",
    "Inactive",
    "Completed",
    "Follow-up",
]


# -----------------------------
# 4. Generate patients
# -----------------------------
patients = []

for i in range(1, NUMBER_OF_PATIENTS + 1):

    city, state = random.choice(locations)

    patient = {
        "patient_id": f"P{i:05d}",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "date_of_birth": fake.date_between_dates(
            date(1970, 1, 1),
            date(2005, 12, 31)
        ),
        "gender": random.choice(genders),
        "city": city,
        "state": state,
        "registration_date": fake.date_between_dates(
            date(2024, 1, 1),
            date(2026, 9, 30)
        ),
        "blood_group": random.choice(blood_groups),
        "phone": (
            str(random.randint(6, 9))
            + str(random.randint(100000000, 999999999))
        ),
        "email": fake.email(),
        "preferred_language": random.choice(languages),
        "registration_channel": random.choice(registration_channels),
        "patient_status": random.choice(patient_statuses),
    }

    patients.append(patient)


# -----------------------------
# 5. Convert to DataFrame
# -----------------------------
patients_df = pd.DataFrame(patients)


# -----------------------------
# 6. Create data directory
# -----------------------------
project_dir = Path(__file__).resolve().parent.parent
data_dir = project_dir / "data"

data_dir.mkdir(exist_ok=True)


# -----------------------------
# 7. Save CSV
# -----------------------------
patients_df.to_csv(
    data_dir / "patients.csv",
    index=False
)


# -----------------------------
# 8. Show results
# -----------------------------
print("Patient dataset created successfully!")
print(f"Number of records: {len(patients_df)}")
print(f"Number of columns: {len(patients_df.columns)}")

print("\nFirst 5 records:")
print(patients_df.head())

print("\nDataset information:")
patients_df.info()