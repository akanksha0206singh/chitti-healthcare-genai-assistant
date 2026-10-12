from faker import Faker
import pandas as pd
import random
from datetime import date


# -----------------------------
# 1. Setup
# -----------------------------
fake = Faker("en_IN")
fake.seed_instance(42)
random.seed(42)


# -----------------------------
# 2. Clinic information
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

clinic_types = [
    "Fertility Center",
    "IVF Center",
    "Reproductive Health Center"
]

clinic_statuses = [
    "Active",
    "Inactive"
]


# -----------------------------
# 3. Generate 25 clinics
# -----------------------------
clinics = []

for i in range(1, 26):

    city, state = random.choice(locations)

    clinic = {
        "clinic_id": f"C{i:03d}",
        "clinic_name": f"Hope Fertility Center {i:02d}",
        "city": city,
        "state": state,
        "clinic_type": random.choice(clinic_types),
        "opening_date": fake.date_between_dates(
            date(2015, 1, 1),
            date(2025, 12, 31)
        ),
        "capacity": random.randint(30, 120),
        "status": random.choice(clinic_statuses)
    }

    clinics.append(clinic)


# -----------------------------
# 4. Convert clinics to DataFrame
# -----------------------------
clinics_df = pd.DataFrame(clinics)


# -----------------------------
# 5. Save clinics
# -----------------------------
clinics_df.to_csv(
    "data/clinics.csv",
    index=False
)


# -----------------------------
# 6. Doctor information
# -----------------------------
specializations = [
    "Reproductive Medicine",
    "Fertility Specialist",
    "Gynecology",
    "Embryology",
    "Andrology",
    "Obstetrics and Gynecology"
]

doctor_statuses = [
    "Active",
    "Inactive",
    "On Leave"
]

doctor_genders = [
    "Female",
    "Male"
]


# -----------------------------
## -----------------------------
# 7. Get active clinics
# -----------------------------
active_clinics = clinics_df[
    clinics_df["status"] == "Active"
]["clinic_id"].tolist()


# -----------------------------
# 8. Generate 40 doctors
# -----------------------------
doctors = []

# First: give every active clinic
# at least one doctor
for i, clinic_id in enumerate(active_clinics, start=1):

    doctor = {
        "doctor_id": f"D{i:03d}",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "specialization": random.choice(specializations),
        "experience_years": random.randint(2, 25),
        "gender": random.choice(doctor_genders),
        "clinic_id": clinic_id,
        "joining_date": fake.date_between_dates(
            date(2016, 1, 1),
            date(2026, 9, 30)
        ),
        "status": random.choice(doctor_statuses)
    }

    doctors.append(doctor)


# Second: generate the remaining doctors
for i in range(len(active_clinics) + 1, 41):

    clinic_id = random.choice(active_clinics)

    doctor = {
        "doctor_id": f"D{i:03d}",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "specialization": random.choice(specializations),
        "experience_years": random.randint(2, 25),
        "gender": random.choice(doctor_genders),
        "clinic_id": clinic_id,
        "joining_date": fake.date_between_dates(
            date(2016, 1, 1),
            date(2026, 9, 30)
        ),
        "status": random.choice(doctor_statuses)
    }

    doctors.append(doctor)


# -----------------------------
# 9. Convert doctors to DataFrame
# -----------------------------
doctors_df = pd.DataFrame(doctors)


# -----------------------------
# 10. Save doctors
# -----------------------------
doctors_df.to_csv(
    "data/doctors.csv",
    index=False
)


# -----------------------------
# 11. Display results
# -----------------------------
print("Clinics created:", len(clinics_df))
print("Active clinics:", len(active_clinics))
print("Doctors created:", len(doctors_df))

print("\nFirst 5 clinics:")
print(clinics_df.head())

print("\nFirst 5 doctors:")
print(doctors_df.head())