from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Book, Genre, Cover, Review, Collection, Role
import os
import hashlib
import mimetypes
from datetime import datetime
import bleach

# Главная страница
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    books = Book.query.order_by(Book.year.desc()).paginate(page=page, per_page=10)
    return render_template('index.html', books=books)

# Аутентификация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        flash('Невозможно аутентифицироваться с указанными логином и паролем')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Книги
@app.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('book_detail.html', book=book)

@app.route('/book/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if current_user.role.name != 'Администратор':
        flash('У вас недостаточно прав для выполнения данного действия')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Сохранение книги
            book = Book(
                title=request.form['title'],
                description=bleach.clean(request.form['description']),
                year=request.form['year'],
                publisher=request.form['publisher'],
                author=request.form['author'],
                pages=request.form['pages']
            )
            db.session.add(book)
            db.session.flush()  # Получаем ID книги
            
            # Обработка жанров
            genre_ids = request.form.getlist('genres')
            for genre_id in genre_ids:
                genre = Genre.query.get(genre_id)
                if genre:
                    book.genres.append(genre)
            
            # Обработка обложки
            if 'cover' in request.files:
                file = request.files['cover']
                if file.filename:
                    filename = secure_filename(file.filename)
                    file_content = file.read()
                    md5_hash = hashlib.md5(file_content).hexdigest()
                    
                    # Проверка существования файла
                    existing_cover = Cover.query.filter_by(md5_hash=md5_hash).first()
                    if existing_cover:
                        book.cover_id = existing_cover.id
                    else:
                        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                        cover = Cover(
                            filename=filename,
                            mime_type=mime_type,
                            md5_hash=md5_hash
                        )
                        db.session.add(cover)
                        db.session.flush()
                        book.cover_id = cover.id
                        
                        # Сохранение файла
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(cover.id))
                        with open(file_path, 'wb') as f:
                            f.write(file_content)
            
            db.session.commit()
            flash('Книга успешно добавлена')
            return redirect(url_for('book_detail', book_id=book.id))
            
        except Exception as e:
            db.session.rollback()
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.')
            return render_template('book_form.html', book=book)
    
    genres = Genre.query.all()
    return render_template('book_form.html', genres=genres)

@app.route('/book/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    if current_user.role.name not in ['Администратор', 'Модератор']:
        flash('У вас недостаточно прав для выполнения данного действия')
        return redirect(url_for('index'))
    
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        try:
            book.title = request.form['title']
            book.description = bleach.clean(request.form['description'])
            book.year = request.form['year']
            book.publisher = request.form['publisher']
            book.author = request.form['author']
            book.pages = request.form['pages']
            
            # Обновление жанров
            book.genres = []
            genre_ids = request.form.getlist('genres')
            for genre_id in genre_ids:
                genre = Genre.query.get(genre_id)
                if genre:
                    book.genres.append(genre)
            
            db.session.commit()
            flash('Книга успешно обновлена')
            return redirect(url_for('book_detail', book_id=book.id))
            
        except Exception as e:
            db.session.rollback()
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.')
    
    genres = Genre.query.all()
    return render_template('book_form.html', book=book, genres=genres)

@app.route('/book/<int:book_id>/delete', methods=['POST'])
@login_required
def delete_book(book_id):
    if current_user.role.name != 'Администратор':
        flash('У вас недостаточно прав для выполнения данного действия')
        return redirect(url_for('index'))
    
    book = Book.query.get_or_404(book_id)
    try:
        # Удаление файла обложки
        if book.cover:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(book.cover.id))
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.session.delete(book)
        db.session.commit()
        flash('Книга успешно удалена')
    except Exception as e:
        db.session.rollback()
        flash('При удалении книги возникла ошибка')
    
    return redirect(url_for('index'))

# Рецензии
@app.route('/book/<int:book_id>/review', methods=['GET', 'POST'])
@login_required
def add_review(book_id):
    book = Book.query.get_or_404(book_id)
    
    # Проверка существования рецензии
    existing_review = Review.query.filter_by(book_id=book_id, user_id=current_user.id).first()
    if existing_review:
        flash('Вы уже оставили рецензию на эту книгу')
        return redirect(url_for('book_detail', book_id=book_id))
    
    if request.method == 'POST':
        try:
            review = Review(
                book_id=book_id,
                user_id=current_user.id,
                rating=request.form['rating'],
                text=bleach.clean(request.form['text'])
            )
            db.session.add(review)
            db.session.commit()
            flash('Рецензия успешно добавлена')
            return redirect(url_for('book_detail', book_id=book_id))
        except Exception as e:
            db.session.rollback()
            flash('При сохранении рецензии возникла ошибка')
    
    return render_template('review_form.html', book=book)

# Подборки
@app.route('/collections')
@login_required
def collections():
    if current_user.role.name != 'Пользователь':
        flash('У вас нет доступа к этой странице', 'danger')
        return redirect(url_for('index'))
    collections = Collection.query.filter_by(user_id=current_user.id).all()
    return render_template('collections.html', collections=collections)

@app.route('/collections/<int:collection_id>')
@login_required
def collection_detail(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    if collection.user_id != current_user.id:
        flash('У вас нет доступа к этой подборке', 'danger')
        return redirect(url_for('collections'))
    return render_template('collection_detail.html', collection=collection)

@app.route('/collections/create', methods=['GET', 'POST'])
@login_required
def create_collection():
    if current_user.role.name != 'Пользователь':
        flash('У вас нет доступа к этой странице', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Название подборки обязательно', 'danger')
            return redirect(url_for('create_collection'))
        
        collection = Collection(name=name, description=description, user_id=current_user.id)
        db.session.add(collection)
        db.session.commit()
        
        flash('Подборка успешно создана', 'success')
        return redirect(url_for('collections'))
    
    return render_template('create_collection.html')

@app.route('/collections/<int:collection_id>/add/<int:book_id>', methods=['POST'])
@login_required
def add_to_collection(collection_id, book_id):
    collection = Collection.query.get_or_404(collection_id)
    if collection.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'У вас нет доступа к этой подборке'})
    
    book = Book.query.get_or_404(book_id)
    if book in collection.books:
        return jsonify({'success': False, 'error': 'Книга уже в подборке'})
    
    collection.books.append(book)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/collections/<int:collection_id>/remove/<int:book_id>', methods=['POST'])
@login_required
def remove_from_collection(collection_id, book_id):
    collection = Collection.query.get_or_404(collection_id)
    if collection.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'У вас нет доступа к этой подборке'})
    
    book = Book.query.get_or_404(book_id)
    if book not in collection.books:
        return jsonify({'success': False, 'error': 'Книги нет в подборке'})
    
    collection.books.remove(book)
    db.session.commit()
    return jsonify({'success': True})

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        middle_name = request.form.get('middle_name')
        
        # Проверяем, существует ли пользователь
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Пользователь с таким именем уже существует', 'danger')
            return redirect(url_for('register'))
        
        # Получаем роль "Пользователь"
        user_role = Role.query.filter_by(name='Пользователь').first()
        if not user_role:
            flash('Ошибка: роль пользователя не найдена', 'danger')
            return redirect(url_for('register'))
        
        # Создаем нового пользователя
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            role=user_role
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при регистрации', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html')

# Маршрут для отображения обложки
@app.route('/cover/<int:cover_id>')
def get_cover(cover_id):
    cover = Cover.query.get_or_404(cover_id)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(cover.id))
    return send_file(file_path, mimetype=cover.mime_type) 