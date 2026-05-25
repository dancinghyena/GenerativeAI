import mysql.connector as connector
from dotenv import load_dotenv
class Connector:
            self.connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="your_password",
            database="student_db"
        )

