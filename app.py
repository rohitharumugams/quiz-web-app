from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
import random

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)

@app.before_first_request
def create_tables():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    exercises = db.relationship('Exercise', backref='course', lazy=True, cascade="all, delete-orphan")

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    questions = db.relationship('Question', backref='exercise', lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)
    options = db.relationship('Option', backref='question', lazy=True, cascade="all, delete-orphan")

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

@app.route('/')
def index():
    courses = Course.query.all()
    return render_template('index.html', courses=courses)

@app.route('/course/<int:course_id>')
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    total_questions = db.session.query(func.count(Question.id)).join(Exercise).filter(Exercise.course_id == course_id).scalar()
    return render_template('course.html', course=course, total_questions=total_questions)

@app.route('/exercise/<int:exercise_id>', methods=['GET', 'POST'])
def view_exercise(exercise_id):
    if exercise_id == 0:
        practice_questions = session.get('practice_test_questions', [])
        course_id = session.get('practice_test_course_id')
        if not practice_questions or not course_id:
            flash('Practice test not properly initialized', 'error')
            return redirect(url_for('view_course', course_id=course_id))
        exercise = {
            'id': 0,
            'name': "Practice Test",
            'questions': practice_questions,
            'course': Course.query.get(course_id)
        }
        is_practice_test = True
    else:
        exercise = Exercise.query.get_or_404(exercise_id)
        is_practice_test = False

    if request.method == 'POST':
        score = 0
        total_questions = len(exercise['questions'] if is_practice_test else exercise.questions)
        question_results = []
        for question in (exercise['questions'] if is_practice_test else exercise.questions):
            question_id = question['id'] if is_practice_test else question.id
            question_text = question['text'] if is_practice_test else question.text
            question_type = question['question_type'] if is_practice_test else question.question_type
            db_question = Question.query.get(question_id)
            correct_options = [opt.id for opt in db_question.options if opt.is_correct]
            user_selected_ids = []
            is_correct = False
            if question_type == 'multiple_choice':
                selected_id = request.form.get(f'question_{question_id}')
                if selected_id:
                    user_selected_ids = [int(selected_id)]
                    is_correct = int(selected_id) in correct_options
            else:
                user_selected_ids = [int(id) for id in request.form.getlist(f'question_{question_id}')]
                is_correct = set(user_selected_ids) == set(correct_options)
            if is_correct:
                score += 1
            options_with_status = []
            for option in db_question.options:
                status = ''
                if option.id in user_selected_ids:
                    status = 'correct' if option.is_correct else 'wrong'
                elif option.is_correct:
                    status = 'missed'
                options_with_status.append({'text': option.text, 'status': status})
            question_results.append({
                'question': question_text,
                'options': options_with_status,
                'was_attempted': bool(user_selected_ids),
                'is_correct': is_correct
            })
        percentage = (score / total_questions) * 100 if total_questions > 0 else 0
        result_exercise = {
            'id': exercise['id'] if is_practice_test else exercise.id,
            'name': exercise['name'] if is_practice_test else exercise.name,
            'course': exercise['course'] if is_practice_test else exercise.course
        }
        return render_template('exercise_result.html',
                               exercise=result_exercise,
                               score=score,
                               total=total_questions,
                               percentage=percentage,
                               question_results=question_results)

    if is_practice_test:
        class PracticeQuestion:
            def __init__(self, data):
                self.id = data['id']
                self.text = data['text']
                self.question_type = data['question_type']
                self.options = [PracticeOption(opt) for opt in data['options']]

        class PracticeOption:
            def __init__(self, data):
                self.id = data['id']
                self.text = data['text']
                self.is_correct = False

        exercise['questions'] = [PracticeQuestion(q) for q in exercise['questions']]

    return render_template('exercise.html', exercise=exercise)

@app.route('/practice-test/<int:course_id>', methods=['POST'])
def start_practice_test(course_id):
    question_count = int(request.form['question_count'])
    course = Course.query.get_or_404(course_id)
    questions = Question.query.join(Exercise).filter(Exercise.course_id == course_id).options(db.joinedload(Question.options)).all()
    if not questions:
        flash('No questions available for practice test', 'error')
        return redirect(url_for('view_course', course_id=course_id))
    selected_questions = random.sample(questions, min(question_count, len(questions)))
    practice_questions = []
    for question in selected_questions:
        practice_questions.append({
            'id': question.id,
            'text': question.text,
            'question_type': question.question_type,
            'options': [{'id': opt.id, 'text': opt.text} for opt in question.options]
        })
    session['practice_test_questions'] = practice_questions
    session['practice_test_course_id'] = course_id
    return redirect(url_for('view_exercise', exercise_id=0))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, is_admin=True).first()
        if user and check_password_hash(user.password, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    courses = Course.query.all()
    course_stats = []
    for course in courses:
        exercise_count = Exercise.query.filter_by(course_id=course.id).count()
        question_count = db.session.query(func.count(Question.id)).join(Exercise).filter(Exercise.course_id == course.id).scalar()
        course_stats.append({
            'course': course,
            'exercise_count': exercise_count,
            'question_count': question_count
        })
    return render_template('admin/dashboard.html', course_stats=course_stats)

if __name__ == '__main__':
    app.run(debug=True)
