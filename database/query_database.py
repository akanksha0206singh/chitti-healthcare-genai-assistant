import mysql.connector
from getpass import getpass


# -----------------------------
# MySQL connection
# -----------------------------
password = getpass("Enter your MySQL password: ")

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password=password,
    database="healthcare_ai_db"
)

cursor = connection.cursor()


# -----------------------------
# Ask the user a question
# -----------------------------
question = input("Ask your healthcare question: ").lower()


# -----------------------------
# Simple question router
# -----------------------------
if "how many patients" in question or "total patients" in question:

    query = """
    SELECT COUNT(*)
    FROM patients;
    """

    cursor.execute(query)
    result = cursor.fetchone()

    print("Total patients:", result[0])


elif "completed treatments" in question:

    query = """
    SELECT COUNT(*)
    FROM treatments
    WHERE status = 'Completed';
    """

    cursor.execute(query)
    result = cursor.fetchone()

    print("Completed treatments:", result[0])


elif (
    "most common treatment" in question
    or "which treatment is most common" in question
):

    query = """
    SELECT treatment_type, COUNT(*) AS total
    FROM treatments
    GROUP BY treatment_type
    ORDER BY total DESC
    LIMIT 1;
    """

    cursor.execute(query)
    result = cursor.fetchone()

    print("Most common treatment:", result[0])
    print("Number of treatments:", result[1])


elif "most appointments" in question:

    query = """
    SELECT clinic_id, COUNT(*) AS total
    FROM appointments
    GROUP BY clinic_id
    ORDER BY total DESC
    LIMIT 1;
    """

    cursor.execute(query)
    result = cursor.fetchone()

    print("Clinic with most appointments:", result[0])
    print("Appointments:", result[1])


elif "total paid" in question or "paid amount" in question:

    query = """
    SELECT SUM(amount)
    FROM payments
    WHERE status = 'Paid';
    """

    cursor.execute(query)
    result = cursor.fetchone()

    print("Total paid amount:", result[0])


else:
    print("Sorry, I don't know how to answer that question yet.")


# -----------------------------
# Close connection
# -----------------------------
cursor.close()
connection.close()
