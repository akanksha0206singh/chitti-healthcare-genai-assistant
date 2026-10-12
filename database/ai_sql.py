from google import genai
import mysql.connector
from getpass import getpass
import os
import re
from decimal import Decimal


# -----------------------------------
# 1. Connect to Gemini
# -----------------------------------
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# -----------------------------------
# 2. Connect to MySQL
# -----------------------------------
mysql_password = getpass("Enter your MySQL password: ")

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password=mysql_password,
    database="healthcare_ai_db"
)

cursor = connection.cursor()


# -----------------------------------
# 3. Database schema
# -----------------------------------
schema = """
patients(
    patient_id,
    first_name,
    last_name,
    date_of_birth,
    gender,
    city,
    state,
    registration_date,
    blood_group,
    phone,
    email,
    preferred_language,
    registration_channel,
    patient_status
)

clinics(
    clinic_id,
    clinic_name,
    city,
    state,
    clinic_type,
    opening_date,
    capacity,
    status
)

doctors(
    doctor_id,
    first_name,
    last_name,
    specialization,
    experience_years,
    gender,
    clinic_id,
    joining_date,
    status
)

appointments(
    appointment_id,
    patient_id,
    doctor_id,
    clinic_id,
    appointment_date,
    booking_date,
    appointment_type,
    appointment_mode,
    reason,
    status,
    duration_minutes
)

treatments(
    treatment_id,
    patient_id,
    doctor_id,
    clinic_id,
    treatment_type,
    start_date,
    end_date,
    status,
    outcome,
    estimated_cost
)

treatment_stages(
    stage_id,
    treatment_id,
    stage_number,
    stage_name,
    stage_date,
    status
)

payments(
    payment_id,
    treatment_id,
    payment_number,
    payment_date,
    amount,
    payment_method,
    status
)

lab_tests(
    lab_test_id,
    treatment_id,
    test_name,
    test_date,
    result_value,
    unit,
    result_status,
    test_cost
)

Important valid values:

Payment status:
Paid, Pending, Failed, Refunded

Treatment status:
Completed, Ongoing, Cancelled, Paused

Appointment status:
Completed, No-show, Rescheduled, Cancelled

Lab test result status:
Normal, Borderline, Abnormal
"""


# -----------------------------------
# 4. Ask the user
# -----------------------------------
question = input("Ask your healthcare question: ").strip()

if not question:
    print("Please enter a question.")
    cursor.close()
    connection.close()
    raise SystemExit


# -----------------------------------
# 5. Ask Gemini to generate SQL
# -----------------------------------
sql_prompt = f"""
You are a MySQL SQL assistant.

Database schema:
{schema}

User question:
{question}

Generate ONE read-only MySQL SELECT query that answers the question.

Rules:
- Use only the tables and columns shown in the schema.
- Return SQL only.
- Use valid MySQL syntax.
- Do not invent tables, columns, or status values.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, REPLACE.
- Generate only ONE SQL statement.
- Do not include explanations or markdown.
"""

sql_response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=sql_prompt
)

sql_query = sql_response.text.strip()


# -----------------------------------
# 6. Clean Markdown fences
# -----------------------------------
sql_query = re.sub(
    r"```sql",
    "",
    sql_query,
    flags=re.IGNORECASE
)

sql_query = sql_query.replace("```", "").strip()


# -----------------------------------
# 7. SQL safety validation
# -----------------------------------
lower_sql = sql_query.lower().strip()

dangerous_keywords = [
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "replace",
    "grant",
    "revoke",
    "rename"
]

# Must begin with SELECT or WITH
is_read_query = (
    lower_sql.startswith("select")
    or lower_sql.startswith("with")
)

# Prevent multiple SQL statements
semicolon_count = sql_query.count(";")

# Check dangerous SQL keywords
contains_dangerous_keyword = any(
    re.search(r"\b" + word + r"\b", lower_sql)
    for word in dangerous_keywords
)


if not is_read_query:
    print("\nBlocked: Only SELECT/WITH queries are allowed.")
    print("Generated SQL:")
    print(sql_query)

elif semicolon_count > 1:
    print("\nBlocked: Multiple SQL statements are not allowed.")
    print("Generated SQL:")
    print(sql_query)

elif contains_dangerous_keyword:
    print("\nBlocked: Potentially destructive SQL detected.")
    print("Generated SQL:")
    print(sql_query)

else:

    # -----------------------------------
    # 8. Execute SQL
    # -----------------------------------
    try:

        cursor.execute(sql_query)

        results = cursor.fetchall()

        print("\nGemini generated SQL:")
        print(sql_query)

        print("\nDatabase result:")
        for row in results:
            print(row)


        # -----------------------------------
        # 9. Format answer
        # -----------------------------------
        if not results:

            print("\nAnswer:")
            print("No matching data was found.")

        else:

            first_row = results[0]

            # One-column result
            if len(first_row) == 1:

                value = first_row[0]

                print("\nAnswer:")

                if value is None:

                    print("No matching data was found.")

                elif isinstance(value, Decimal):

                    print(f"₹{value:,.2f}")

                elif isinstance(value, (int, float)):

                    print(f"{value:,}")

                else:

                    print(value)


            # Two-column result
            elif len(first_row) == 2:

                name = first_row[0]
                value = first_row[1]

                print("\nAnswer:")

                if value is None:

                    print(f"{name}: no matching data was found.")

                elif isinstance(value, Decimal):

                    print(f"{name}: ₹{value:,.2f}")

                elif isinstance(value, (int, float)):

                    print(f"{name}: {value:,}")

                else:

                    print(f"{name}: {value}")


            # Three-column result
            elif len(first_row) == 3:

                first_value = first_row[0]
                second_value = first_row[1]
                third_value = first_row[2]

                print("\nAnswer:")

                if isinstance(third_value, Decimal):

                    print(
                        f"{second_value} ({first_value}): "
                        f"₹{third_value:,.2f}"
                    )

                elif isinstance(third_value, (int, float)):

                    print(
                        f"{second_value} ({first_value}) has "
                        f"{third_value:,}."
                    )

                else:

                    print(
                        f"{second_value} ({first_value}): "
                        f"{third_value}"
                    )


            # More than three columns
            else:

                print("\nAnswer:")

                for row in results:
                    print(row)


    except mysql.connector.Error as error:

        print("\nMySQL error:")
        print(error)


# -----------------------------------
# 10. Close database connection
# -----------------------------------
cursor.close()
connection.close()