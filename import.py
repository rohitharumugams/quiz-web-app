from app import db, Course, Exercise, Question, Option, app
import json

def load_data():
    with app.app_context():
        db.create_all()  # Create tables if they don't exist

        # Load quiz data
        with open('quiz_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        for course_data in data:
            course = Course(name=course_data['name'], description=course_data.get('description', ''))
            db.session.add(course)
            db.session.flush()  # Get course.id

            for ex_data in course_data.get('exercises', []):
                exercise = Exercise(name=ex_data['name'], course_id=course.id)
                db.session.add(exercise)
                db.session.flush()  # Get exercise.id

                for q_data in ex_data.get('questions', []):
                    question = Question(
                        text=q_data['text'],
                        question_type=q_data['question_type'],
                        exercise_id=exercise.id
                    )
                    db.session.add(question)
                    db.session.flush()  # Get question.id

                    for opt_data in q_data['options']:
                        option = Option(
                            text=opt_data['text'],
                            is_correct=opt_data['is_correct'],
                            question_id=question.id
                        )
                        db.session.add(option)

        db.session.commit()
        print("Data imported successfully.")

if __name__ == '__main__':
    load_data()
