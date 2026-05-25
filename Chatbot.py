from Model import Database


class Chatbot:
    """Chatbot class that responds to user queries using student data"""
    
    def __init__(self):
        """Initialize chatbot with database connection"""
        self.db = Database()
    
    def get_response(self, query):
        """
        Process user query and return a response
        
        Args:
            query (str): User's question
            
        Returns:
            str: Chatbot response
        """
        query = query.lower().strip()
        
        # Get all students for reference
        students = self.db.get_all_students()
        
        # Different query types
        if "how many students" in query or "total students" in query:
            return self._count_students(students)
        
        elif "list students" in query or "show students" in query or "all students" in query:
            return self._list_all_students(students)
        
        elif "average age" in query:
            return self._average_age(students)
        
        elif "highest grade" in query or "best grade" in query:
            return self._highest_grade(students)
        
        elif "grade" in query and any(grade in query.lower() for grade in ["a", "b", "c", "d", "f"]):
            # Extract grade and return students with that grade
            for grade in ["A", "B", "C", "D", "F"]:
                if grade.lower() in query:
                    return self._students_by_grade(students, grade)
        
        elif "student" in query and "age" in query:
            # Try to find student by name
            words = query.split()
            for word in words:
                if word.lower() not in ["student", "age", "is", "what", "of", "the", "?", "age"]:
                    student = self.db.get_student_by_name(word)
                    if student:
                        return f"Student {student.name} is {student.age} years old with grade {student.grade}."
        
        elif "age" in query:
            return self._get_ages(students)
        
        else:
            return "I'm not sure how to answer that. Try asking:\n- 'How many students?'\n- 'List all students'\n- 'What's the average age?'\n- 'Show students with grade A'"
    
    def _count_students(self, students):
        """Count total students"""
        return f"There are {len(students)} students in the database."
    
    def _list_all_students(self, students):
        """List all students"""
        if not students:
            return "No students found in the database."
        
        response = "Here are all students:\n"
        for student in students:
            response += f"- {student.name} (Age: {student.age}, Grade: {student.grade})\n"
        return response
    
    def _average_age(self, students):
        """Calculate average age of students"""
        if not students:
            return "No students found."
        
        total_age = sum(student.age for student in students)
        avg_age = total_age / len(students)
        return f"The average age of students is {avg_age:.1f} years."
    
    def _highest_grade(self, students):
        """Find student(s) with highest grade"""
        if not students:
            return "No students found."
        
        grade_order = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
        top_students = []
        top_grade = None
        
        for student in students:
            grade_value = grade_order.get(student.grade, 0)
            if top_grade is None or grade_value > grade_value:
                top_grade = grade_value
                top_students = [student]
            elif grade_value == top_grade:
                top_students.append(student)
        
        response = f"Students with the highest grade ({top_students[0].grade}):\n"
        for student in top_students:
            response += f"- {student.name}\n"
        return response
    
    def _students_by_grade(self, students, grade):
        """Get all students with a specific grade"""
        filtered = [s for s in students if s.grade.upper() == grade.upper()]
        
        if not filtered:
            return f"No students found with grade {grade}."
        
        response = f"Students with grade {grade}:\n"
        for student in filtered:
            response += f"- {student.name} (Age: {student.age})\n"
        return response
    
    def _get_ages(self, students):
        """Get age information"""
        if not students:
            return "No students found."
        
        ages = [s.age for s in students]
        response = f"Age statistics:\n"
        response += f"- Youngest: {min(ages)}\n"
        response += f"- Oldest: {max(ages)}\n"
        response += f"- Average: {sum(ages)/len(ages):.1f}\n"
        return response
