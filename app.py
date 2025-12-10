# app.py
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, session, request, abort, g
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Загрузить .env
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'dev-secret'   # в prod — обязателен .env
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация db, модели и формы
from models import db, User, Note
from forms import NoteForm, RegisterForm, LoginForm

db.init_app(app)

# Создаём таблицы при первом запуске
with app.app_context():
    db.create_all()

# Простейшая имитация пользователя для заметок (если нужен owner_id)
def ensure_user():
    if 'user_id' not in session:
        session['user_id'] = None
    return session.get('user_id')

# Главная — список заметок и форма добавления

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Главная страница: если пользователь не аутентифицирован,
    перенаправляем на страницу регистрации (/register).
    После входа/регистрации пользователь увидит список заметок.
    """
    # Если нет user_id в сессии — перенаправляем на регистрацию
    if not session.get('user_id'):
        return redirect(url_for('register'))

    # Если пользователь аутентифицирован — обычная логика страницы
    form = NoteForm()
    if form.validate_on_submit():
        owner_id = session.get('user_id')  # id владельца (если есть)
        note = Note(
            title=form.title.data.strip(),
            content=form.content.data.strip(),
            owner_id=owner_id
        )
        db.session.add(note)
        db.session.commit()
        flash('Заметка успешно создана.', 'success')
        return redirect(url_for('index'))

    notes = Note.query.order_by(Note.created_at.desc()).all()
    return render_template('index.html', notes=notes, form=form)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        password_hash = generate_password_hash(password)
        user = User(username=username, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна. Войдите.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            # Успешный вход — сохраняем в сессии
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Вход успешно выполнен.', 'success')
            return redirect(url_for('index'))
        flash('Неверный логин или пароль.', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html', form=form)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли.', 'info')
    return redirect(url_for('index'))

# Редактирование заметки (только владелец или анонимные не могут)
@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    current_user = session.get('user_id')
    # если заметки привязаны к user, проверяем права
    if note.owner_id is not None and note.owner_id != current_user:
        abort(403)
    form = NoteForm(obj=note)
    if form.validate_on_submit():
        note.title = form.title.data.strip()
        note.content = form.content.data.strip()
        note.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Заметка обновлена.', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', form=form, note=note)

# Delete
@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    current_user = session.get('user_id')
    if note.owner_id is not None and note.owner_id != current_user:
        abort(403)
    db.session.delete(note)
    db.session.commit()
    flash('Заметка удалена.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Для разработки — flask run или python app.py
    app.run(host='127.0.0.1', port=5000)
