import pandas as pd
from getpass import getpass
from urllib.parse import quote_plus
from sqlalchemy import create_engine


# -----------------------------
# MySQL connection details
# -----------------------------
password = getpass("Enter your MySQL password: ")

password_encoded = quote_plus(password)

engine = create_engine(
    f"mysql+mysqlconnector://root:{password_encoded}@localhost/healthcare_ai_db"
)


# -----------------------------
# CSV files and table order
# -----------------------------
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


# -----------------------------
# Load each CSV into MySQL
# -----------------------------
for table_name, csv_path in tables:

    print(f"\nLoading {csv_path}...")

    df = pd.read_csv(csv_path)

    # Convert date columns to proper dates
    for column in df.columns:
        if "date" in column:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            ).dt.date

    # Add data to existing MySQL table
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