from app import app, db
from app import User, Course, Exercise, Question, Option  # Import from app instead of models
import json

def import_data():
    with app.app_context():
        db.drop_all()  # Clear existing tables
        db.create_all()  # Recreate tables
        
        with open('db_export.json') as f:
            data = json.load(f)
            
            # Import in correct order to maintain relationships
            for user_data in data['users']:
                db.session.add(User(**user_data))
            db.session.commit()
            
            for course_data in data['courses']:
                db.session.add(Course(**course_data))
            db.session.commit()
            
            for exercise_data in data['exercises']:
                db.session.add(Exercise(**exercise_data))
            db.session.commit()
            
            for question_data in data['questions']:
                db.session.add(Question(**question_data))
            db.session.commit()
            
            for option_data in data['options']:
                db.session.add(Option(**option_data))
            db.session.commit()

if __name__ == '__main__':
    import_data()
