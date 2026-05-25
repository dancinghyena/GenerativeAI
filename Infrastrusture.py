import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

class Connector:
    def __init__(self):
        self.connection = psycopg2.connect(
            os.getenv("DATABASE_URL")
        )
        
    def add_student(self, name, age, grade):
        cursor = self.connection.cursor()
        query = "INSERT INTO students (name, age, grade) VALUES (%s, %s, %s)"
        values = (name, age, grade)
        cursor.execute(query, values)
        self.connection.commit()
        cursor.close()
        
    def get_students(self):
        cursor = self.connection.cursor(RealDictCursor)
        query = "SELECT name, age, grade FROM students"
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results  
    
    def update_student(self, name, age, grade):
        cursor = self.connection.cursor()
        query = "UPDATE students SET age = %s, grade = %s WHERE name = %s"
        values = (age, grade, name)
        cursor.execute(query, values)
        self.connection.commit()
        cursor.close()
    
    def delete_student(self, name):
        cursor = self.connection.cursor()
        query = "DELETE FROM students WHERE name = %s"
        values = (name,)
        cursor.execute(query, values)
        self.connection.commit()
        cursor.close()
    
    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
              
        

