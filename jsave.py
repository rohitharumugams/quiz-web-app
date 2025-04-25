from app import app, db, Exercise, Question, Option

def setup_exercise_12():
    with app.app_context():
        # Create Exercise 12 if missing
        if not Exercise.query.get(12):
            new_exercise = Exercise(
                id=12,
                name="Exercise 12",
                course_id=1  # Adjust course ID if needed
            )
            db.session.add(new_exercise)
            db.session.commit()
            print("✅ Created Exercise 12")

def insert_questions(exercise_id, questions_data):
    with app.app_context():
        exercise = Exercise.query.get(exercise_id)
        if not exercise:
            print(f"Error: Exercise ID {exercise_id} not found!")
            return

        for q in questions_data:
            question = Question(
                text=q['text'],
                question_type=q['type'],
                exercise_id=exercise_id
            )
            db.session.add(question)
            db.session.flush()

            for opt in q['options']:
                option = Option(
                    text=opt['text'],
                    is_correct=opt['is_correct'],
                    question_id=question.id
                )
                db.session.add(option)

        db.session.commit()
        print(f"✅ Inserted {len(questions_data)} questions into Exercise {exercise_id}")

# ===== PREPARE EXERCISE =====
setup_exercise_12()

# ===== EXERCISE 12 QUESTIONS =====
questions = [
    {
        "text": "Privacy concerns in affective computing arise from:",
        "type": "multiple_choice",
        "options": [
            {"text": "The collection and analysis of personal data", "is_correct": True},
            {"text": "The potential for misuse of emotional information", "is_correct": False},
            {"text": "The lack of transparency in AI decision-making", "is_correct": False},
            {"text": "None of the above.", "is_correct": False}
        ]
    },
    {
        "text": "Which of the following is not a potential Ethical Consideration that need not to be addressed?",
        "type": "multiple_choice",
        "options": [
            {"text": "Emotional Manipulation", "is_correct": False},
            {"text": "Privacy", "is_correct": False},
            {"text": "Emotional Dependency", "is_correct": False},
            {"text": "System accuracy", "is_correct": True}
        ]
    },
    {
        "text": "Which of the following has a high level of privacy intrusion?",
        "type": "multiple_choice",
        "options": [
            {"text": "Audio jack", "is_correct": False},
            {"text": "WiFi", "is_correct": False},
            {"text": "Camera", "is_correct": True},
            {"text": "Bluetooth", "is_correct": False}
        ]
    },
    {
        "text": "All mobile sensors capture the least amount of sensitive data.",
        "type": "true_false",
        "options": [
            {"text": "True", "is_correct": False},
            {"text": "False", "is_correct": True}
        ]
    },
    {
        "text": "Which of the following sensing strategies is written wrongly in order of their privacy invasiveness, in ascending order?",
        "type": "multiple_choice",
        "options": [
            {"text": "Microphone > WiFi > Accelerometer", "is_correct": False},
            {"text": "GPS > Bluetooth > Screen Touch", "is_correct": False},
            {"text": "WiFi > Gyroscope > Calls", "is_correct": True},
            {"text": "Calls > Apps > Gyroscope", "is_correct": False}
        ]
    },
    {
        "text": "What is the primary goal of anticipatory mobile computing?",
        "type": "multiple_choice",
        "options": [
            {"text": "To predict user needs and proactively provide services.", "is_correct": True},
            {"text": "To optimize battery life on mobile devices.", "is_correct": False},
            {"text": "To enhance the security of mobile devices.", "is_correct": False},
            {"text": "To increase the processing power of mobile devices.", "is_correct": False}
        ]
    },
    {
        "text": "From an ethics perspective, what is a significant concern regarding affect-sensing apps in relation to emotional dependency?",
        "type": "multiple_choice",
        "options": [
            {"text": "User engagement", "is_correct": False},
            {"text": "Privacy intrusion", "is_correct": False},
            {"text": "Emotional manipulation", "is_correct": False},
            {"text": "User addiction", "is_correct": True}
        ]
    },
    {
        "text": "What is a potential ethical concern related to facial expression recognition?",
        "type": "multiple_choice",
        "options": [
            {"text": "Privacy violations", "is_correct": False},
            {"text": "Bias in recognition systems", "is_correct": False},
            {"text": "Misinterpretation of emotions", "is_correct": False},
            {"text": "All of the above", "is_correct": True}
        ]
    },
    {
        "text": "It is possible to completely anonymize a user's personal information using algorithms.",
        "type": "true_false",
        "options": [
            {"text": "True", "is_correct": False},
            {"text": "False", "is_correct": True}
        ]
    },
    {
        "text": "Who should be involved in shaping the ethical guidelines for the development of affect-aware machines?",
        "type": "multiple_choice",
        "options": [
            {"text": "Engineers and developers only.", "is_correct": False},
            {"text": "Ethicists and philosophers only.", "is_correct": False},
            {"text": "Users and stakeholders only.", "is_correct": False},
            {"text": "A combination of engineers, ethicists, users, and other relevant stakeholders.", "is_correct": True}
        ]
    }
]

# ==== RUN FOR EXERCISE 12 ====
insert_questions(exercise_id=12, questions_data=questions)
