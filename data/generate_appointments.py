from faker import Faker
import pandas as pd
import random
from datetime import date


# -----------------------------
# 1. Setup
# -----------------------------
fake = Faker("en_IN")
fake.seed_instance(100)
random.seed(100)


# -----------------------------
# 2. Number of appointments
# -----------------------------
NUMBER_OF_APPOINTMENTS = 40_000


# -----------------------------
# 3. Load existing datasets
# -----------------------------
patients_df = pd.read_csv("data/patients.csv")
doctors_df = pd.read_csv("data/doctors.csv")
clinics_df = pd.read_csv("data/clinics.csv")


# Convert date columns to datetime
patients_df["registration_date"] = pd.to_datetime(
    patients_df["registration_date"]
)

doctors_df["joining_date"] = pd.to_datetime(
    doctors_df["joining_date"]
)


# -----------------------------
# 4. Appointment categories
# -----------------------------
appointment_types = [
    "Initial Consultation",
    "Follow-up",
    "Treatment Review",
    "Procedure",
    "Ultrasound",
    "Lab Review",
    "Counselling",
    "Teleconsultation",
]

appointment_modes = [
    "In-person",
    "Video",
    "Phone",
]

appointment_statuses = [
    "Completed",
    "Cancelled",
    "No-show",
    "Rescheduled",
    "Scheduled",
]

reasons = [
    "Fertility Consultation",
    "IVF Consultation",
    "IUI Consultation",
    "Treatment Follow-up",
    "Cycle Monitoring",
    "Egg Retrieval Review",
    "Embryo Transfer Review",
    "Medication Review",
    "Diagnostic Consultation",
    "Report Discussion",
]


# -----------------------------
# 5. Create doctor → clinic mapping
# -----------------------------
doctor_clinic_map = dict(
    zip(
        doctors_df["doctor_id"],
        doctors_df["clinic_id"]
    )
)


# -----------------------------
# 6. Generate appointments
# -----------------------------
appointments = []

for i in range(1, NUMBER_OF_APPOINTMENTS + 1):

    # Choose a patient
    patient = patients_df.sample(
        n=1,
        random_state=random.randint(1, 1_000_000)
    ).iloc[0]

    patient_id = patient["patient_id"]
    registration_date = patient["registration_date"]

    # Choose a doctor
    doctor = doctors_df.sample(
        n=1,
        random_state=random.randint(1, 1_000_000)
    ).iloc[0]

    doctor_id = doctor["doctor_id"]
    doctor_joining_date = doctor["joining_date"]

    # Doctor's clinic
    clinic_id = doctor_clinic_map[doctor_id]

    # Appointment cannot happen before
    # patient registration or doctor joining
    start_date = max(
        registration_date,
        doctor_joining_date
    )

    end_date = pd.Timestamp("2026-09-30")

    # Generate appointment date
    appointment_date = fake.date_between_dates(
    date_start=start_date.date(),
    date_end=end_date.date()
)
    appointment_date = pd.Timestamp(
        appointment_date
    )

    # Booking date should be on or before appointment
    booking_start = registration_date

    booking_end = appointment_date

    booking_date = fake.date_between_dates(
    date_start=booking_start.date(),
    date_end=booking_end.date()
)

    appointments.append(
        {
            "appointment_id": f"A{i:05d}",
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "clinic_id": clinic_id,
            "appointment_date": appointment_date.date(),
            "booking_date": booking_date,
            "appointment_type": random.choice(
                appointment_types
            ),
            "appointment_mode": random.choice(
                appointment_modes
            ),
            "reason": random.choice(reasons),
            "status": random.choice(
                appointment_statuses
            ),
            "duration_minutes": random.choice(
                [15, 20, 30, 45, 60]
            ),
        }
    )


# -----------------------------
# 7. Convert to DataFrame
# -----------------------------
appointments_df = pd.DataFrame(appointments)


# -----------------------------
# 8. Save dataset
# -----------------------------
appointments_df.to_csv(
    "data/appointments.csv",
    index=False
)


# -----------------------------
# 9. Display results
# -----------------------------
print("Appointments created:", len(appointments_df))

print("\nFirst 5 appointments:")
print(appointments_df.head())

print("\nColumns:")
print(appointments_df.columns.tolist())

print("\nMissing values:")
print(appointments_df.isnull().sum())
