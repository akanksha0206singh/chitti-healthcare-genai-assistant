import pandas as pd
from getpass import getpass
from urllib.parse import quote_plus
from sqlalchemy import create_engine

# MySQL password
password = getpass("Enter your MySQL password: ")

# Encode password safely for the connection URL
password_encoded = quote_plus(password)

# Connect to MySQL
engine = create_engine(
    f"mysql+mysqlconnector://root:{password_encoded}@localhost/healthcare_ai_db"
)

# Load in foreign-key order
tables = [
    ("patients", "data/patients.csv"),
    ("clinics", "data/clinics.csv"),
    ("doctors", "data/doctors.csv"),
    ("appointments", "data/appointments.csv"),
    ("treatments", "data/treatments.csv"),
    ("treatment_stages", "data/treatment_stages.csv"),
    ("payments", "data/payments.csv"),
    ("lab_tests", "data/lab_tests.csv"),
]

for table_name, csv_path in tables:

    print(f"\nLoading {csv_path}...")

    df = pd.read_csv(csv_path)

    # Convert date columns
    for column in df.columns:
        if "date" in column:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            ).dt.date

    # Insert into existing MySQL table
    df.to_sql(
        table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=1000
    )

    print(f"{table_name}: {len(df)} rows loaded successfully")

print("\nAll data loaded successfully!")

engine.dispose()