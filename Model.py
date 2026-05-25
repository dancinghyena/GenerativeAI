from Infrastrusture import Connector


class Student:
    """Represents a Student in the database"""
    
    def __init__(self, name, age, grade, student_id=None):
        self.__student_id = student_id
        self.__name = name
        self.__age = age
        self.__grade = grade

    @property
    def student_id(self):
        return self.__student_id
    
    @property
    def name(self):
        return self.__name
    
    @property
    def age(self):
        return self.__age
    
    @property
    def grade(self):
        return self.__grade
    
    def get_name(self):
        return self.__name
    
    def get_age(self):
        return self.__age
    
    def get_grade(self):
        return self.__grade
    
    def update(self, name=None, age=None, grade=None):
        if name is not None:
            self.__name = name
        if age is not None:
            self.__age = age
        if grade is not None:
            self.__grade = grade
    
    def to_dict(self):
        """Convert student to dictionary for easy access"""
        return {
            "id": self.__student_id,
            "name": self.__name,
            "age": self.__age,
            "grade": self.__grade
        }


class Database:
    """Handles all database operations using Connector"""
    
    def __init__(self):
        """Initialize database connection"""
        self.connector = Connector()
    
    def add_student(self, name, age, grade):
        """Add a new student to the database"""
        try:
            self.connector.add_student(name, age, grade)
            return True, "Student added successfully"
        except Exception as e:
            return False, f"Error adding student: {str(e)}"
    
    def get_all_students(self):
        """Fetch all students from database"""
        try:
            results = self.connector.get_students()
            students = []
            for row in results:
                # Handle both tuple and dict formats
                if isinstance(row, dict):
                    student = Student(
                        name=row['name'],
                        age=row['age'],
                        grade=row['grade'],
                        student_id=row.get('id')
                    )
                else:
                    # Tuple format: (name, age, grade)
                    student = Student(
                        name=row[0],
                        age=row[1],
                        grade=row[2]
                    )
                students.append(student)
            return students
        except Exception as e:
            print(f"Error fetching students: {str(e)}")
            return []
    
    def get_student_by_name(self, name):
        """Fetch a specific student by name"""
        try:
            students = self.get_all_students()
            for student in students:
                if student.name.lower() == name.lower():
                    return student
            return None
        except Exception as e:
            print(f"Error fetching student: {str(e)}")
            return None
    
    def update_student(self, name, age, grade):
        """Update an existing student"""
        try:
            self.connector.update_student(name, age, grade)
            return True, "Student updated successfully"
        except Exception as e:
            return False, f"Error updating student: {str(e)}"
    
    def delete_student(self, name):
        """Delete a student from the database"""
        try:
            self.connector.delete_student(name)
            return True, "Student deleted successfully"
        except Exception as e:
            return False, f"Error deleting student: {str(e)}"
    
    def close(self):
        """Close the database connection"""
        self.connector.close()
    