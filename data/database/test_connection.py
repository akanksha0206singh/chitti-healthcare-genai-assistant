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

    if connection.is_connected():
        print("MySQL connection successful!")

        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")

        database_name = cursor.fetchone()[0]
        print("Connected database:", database_name)

        cursor.close()
        connection.close()

except mysql.connector.Error as error:
    print("MySQL connection failed:")
    print(error)