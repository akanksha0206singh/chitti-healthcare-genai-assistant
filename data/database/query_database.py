import mysql.connector
from getpass import getpass

password = getpass("Enter your MySQL password: ")

try:
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password=password,
        database="healthcare_ai_db"
    )

    cursor = connection.cursor()

    # Example business question:
    # How many completed treatments are there?
    query = """
    SELECT COUNT(*) AS completed_treatments
    FROM treatments
    WHERE status = 'Completed';
    """

    cursor.execute(query)

    result = cursor.fetchone()

    print("Completed treatments:", result[0])

    cursor.close()
    connection.close()

except mysql.connector.Error as error:
    print("Database error:", error)