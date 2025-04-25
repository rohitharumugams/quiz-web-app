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

# Database Models
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
    question_type = db.Column(db.String(20), nullable=False)  # 'multiple_choice' or 'multiple_answer'
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)
    options = db.relationship('Option', backref='question', lazy=True, cascade="all, delete-orphan")

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

# Client Routes
@app.route('/')
def index():
    courses = Course.query.all()
    return render_template('index.html', courses=courses)

@app.route('/course/<int:course_id>')
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    total_questions = db.session.query(func.count(Question.id))\
        .join(Exercise)\
        .filter(Exercise.course_id == course_id)\
        .scalar()
    return render_template('course.html', 
                         course=course,
                         total_questions=total_questions)

@app.route('/exercise/<int:exercise_id>', methods=['GET', 'POST'])
def view_exercise(exercise_id):
    # Handle practice test setup
    if exercise_id == 0:  # Practice test
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
    
    # Handle form submission
    if request.method == 'POST':
        score = 0
        total_questions = len(exercise['questions'] if is_practice_test else exercise.questions)
        question_results = []
        
        for question in (exercise['questions'] if is_practice_test else exercise.questions):
            # For practice tests, question is a dict. For regular exercises, it's a SQLAlchemy object
            question_id = question['id'] if is_practice_test else question.id
            question_text = question['text'] if is_practice_test else question.text
            question_type = question['question_type'] if is_practice_test else question.question_type
            
            # Get correct answers from database
            db_question = Question.query.get(question_id)
            correct_options = [opt.id for opt in db_question.options if opt.is_correct]
            
            user_selected_ids = []
            is_correct = False
            
            if question_type == 'multiple_choice':
                selected_id = request.form.get(f'question_{question_id}')
                if selected_id:
                    user_selected_ids = [int(selected_id)]
                    is_correct = int(selected_id) in correct_options
            else:  # multiple_answer
                user_selected_ids = [int(id) for id in request.form.getlist(f'question_{question_id}')]
                is_correct = set(user_selected_ids) == set(correct_options)
            
            if is_correct:
                score += 1
            
            # Get all options with status for display
            options_with_status = []
            for option in db_question.options:
                status = ''
                if option.id in user_selected_ids:
                    status = 'correct' if option.is_correct else 'wrong'
                elif option.is_correct:
                    status = 'missed'
                
                options_with_status.append({
                    'text': option.text,
                    'status': status
                })
            
            question_results.append({
                'question': question_text,
                'options': options_with_status,
                'was_attempted': bool(user_selected_ids),
                'is_correct': is_correct
            })
        
        percentage = (score / total_questions) * 100 if total_questions > 0 else 0
        
        # Prepare exercise data for results template
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
    
    # GET request - show the exercise
    # Convert practice test questions to proper format for template
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
    
    # Get all questions with their options
    questions = Question.query\
        .join(Exercise)\
        .filter(Exercise.course_id == course_id)\
        .options(db.joinedload(Question.options))\
        .all()
    
    if not questions:
        flash('No questions available for practice test', 'error')
        return redirect(url_for('view_course', course_id=course_id))
    
    # Randomly select questions
    selected_questions = random.sample(questions, min(question_count, len(questions)))
    
    # Prepare question data with options
    practice_questions = []
    for question in selected_questions:
        practice_questions.append({
            'id': question.id,
            'text': question.text,
            'question_type': question.question_type,
            'options': [{'id': opt.id, 'text': opt.text} for opt in question.options]
        })
    
    # Store in session
    session['practice_test_questions'] = practice_questions
    session['practice_test_course_id'] = course_id
    
    return redirect(url_for('view_exercise', exercise_id=0))

# Admin Routes
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
    
    # Get counts for each course
    course_stats = []
    for course in courses:
        exercise_count = Exercise.query.filter_by(course_id=course.id).count()
        question_count = db.session.query(func.count(Question.id))\
            .join(Exercise)\
            .filter(Exercise.course_id == course.id)\
            .scalar()
        
        course_stats.append({
            'course': course,
            'exercise_count': exercise_count,
            'question_count': question_count
        })
    
    return render_template('admin/dashboard.html', course_stats=course_stats)

# Course CRUD
@app.route('/admin/add_course', methods=['GET', 'POST'])
def add_course():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        new_course = Course(name=name, description=description)
        db.session.add(new_course)
        db.session.commit()
        flash('Course added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_course.html')

@app.route('/admin/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        course.name = request.form['name']
        course.description = request.form['description']
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_course.html', course=course)

@app.route('/admin/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Exercise CRUD
@app.route('/admin/add_exercise/<int:course_id>', methods=['GET', 'POST'])
def add_exercise(course_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        name = request.form['name']
        new_exercise = Exercise(name=name, course_id=course_id)
        db.session.add(new_exercise)
        db.session.commit()
        flash('Exercise added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_exercise.html', course=course)

@app.route('/admin/edit_exercise/<int:exercise_id>', methods=['GET', 'POST'])
def edit_exercise(exercise_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    exercise = Exercise.query.get_or_404(exercise_id)
    
    if request.method == 'POST':
        exercise.name = request.form['name']
        db.session.commit()
        flash('Exercise updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_exercise.html', exercise=exercise)

@app.route('/admin/delete_exercise/<int:exercise_id>', methods=['POST'])
def delete_exercise(exercise_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    exercise = Exercise.query.get_or_404(exercise_id)
    db.session.delete(exercise)
    db.session.commit()
    flash('Exercise deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Question CRUD
@app.route('/admin/add_question/<int:exercise_id>', methods=['GET', 'POST'])
def add_question(exercise_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    exercise = Exercise.query.get_or_404(exercise_id)
    
    if request.method == 'POST':
        text = request.form['text']
        question_type = request.form['question_type']
        options = request.form.getlist('options[]')
        correct_options = request.form.getlist('correct_options[]')
        
        new_question = Question(text=text, question_type=question_type, exercise_id=exercise_id)
        db.session.add(new_question)
        db.session.commit()
        
        for i, option_text in enumerate(options):
            is_correct = str(i) in correct_options
            new_option = Option(text=option_text, is_correct=is_correct, question_id=new_question.id)
            db.session.add(new_option)
        
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('add_question', exercise_id=exercise_id))
    
    return render_template('admin/add_question.html', exercise=exercise)

@app.route('/admin/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    question = Question.query.get_or_404(question_id)
    
    if request.method == 'POST':
        question.text = request.form['text']
        question.question_type = request.form['question_type']
        
        # Update options
        for option in question.options:
            option.text = request.form[f'option_{option.id}']
            option.is_correct = (request.form.get(f'correct_option') == str(option.id))
        
        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('add_question', exercise_id=question.exercise_id))
    
    return render_template('admin/edit_question.html', question=question)

@app.route('/admin/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    question = Question.query.get_or_404(question_id)
    exercise_id = question.exercise_id
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('add_question', exercise_id=exercise_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
