from app import app, db
from models import Book, Genre

def add_initial_data():
    with app.app_context():
        # Добавляем жанры
        genres = [
            'Фантастика',
            'Детектив',
            'Роман',
            'Поэзия',
            'Исторический роман',
            'Приключения',
            'Ужасы',
            'Научная литература',
            'Психология',
            'Бизнес',
            'Фэнтези'
        ]
        
        genre_objects = {}
        for genre_name in genres:
            genre = Genre.query.filter_by(name=genre_name).first()
            if not genre:
                genre = Genre(name=genre_name)
                db.session.add(genre)
                db.session.flush()
            genre_objects[genre_name] = genre
        
        # Добавляем книги
        books = [
            {
                'title': '1984',
                'description': 'Антиутопический роман Джорджа Оруэлла, описывающий тоталитарное общество.',
                'year': 1949,
                'publisher': 'Secker & Warburg',
                'author': 'Джордж Оруэлл',
                'pages': 328,
                'genres': ['Фантастика', 'Научная литература']
            },
            {
                'title': 'Атлант расправил плечи',
                'description': 'Философский роман Айн Рэнд о роли разума в жизни человека и общества.',
                'year': 1957,
                'publisher': 'Random House',
                'author': 'Айн Рэнд',
                'pages': 1168,
                'genres': ['Роман', 'Философия']
            },
            {
                'title': 'Психология влияния',
                'description': 'Классическая работа по психологии влияния и убеждения.',
                'year': 1984,
                'publisher': 'HarperCollins',
                'author': 'Роберт Чалдини',
                'pages': 320,
                'genres': ['Психология', 'Бизнес']
            },
            {
                'title': 'Властелин колец',
                'description': 'Эпическая фэнтезийная трилогия о борьбе добра со злом в вымышленном мире Средиземья.',
                'year': 1954,
                'publisher': 'Allen & Unwin',
                'author': 'Джон Р. Р. Толкин',
                'pages': 1216,
                'genres': ['Фэнтези', 'Приключения']
            },
            {
                'title': 'Гарри Поттер и философский камень',
                'description': 'Первая книга серии о юном волшебнике Гарри Поттере.',
                'year': 1997,
                'publisher': 'Bloomsbury',
                'author': 'Джоан Роулинг',
                'pages': 309,
                'genres': ['Фэнтези', 'Приключения']
            },
            {
                'title': 'Игра престолов',
                'description': 'Первая книга цикла "Песнь Льда и Пламени" о борьбе за власть в вымышленном мире.',
                'year': 1996,
                'publisher': 'Bantam Books',
                'author': 'Джордж Р. Р. Мартин',
                'pages': 694,
                'genres': ['Фэнтези', 'Приключения']
            },
            {
                'title': 'Метро 2033',
                'description': 'Постапокалиптический роман о жизни людей в московском метро после ядерной войны.',
                'year': 2005,
                'publisher': 'Эксмо',
                'author': 'Дмитрий Глуховский',
                'pages': 384,
                'genres': ['Фантастика', 'Ужасы']
            },
            {
                'title': 'Богатый папа, бедный папа',
                'description': 'Книга о финансовой грамотности и правильном отношении к деньгам.',
                'year': 1997,
                'publisher': 'Warner Books',
                'author': 'Роберт Кийосаки',
                'pages': 336,
                'genres': ['Бизнес', 'Психология']
            }
        ]
        
        for book_data in books:
            # Проверяем, существует ли книга
            existing_book = Book.query.filter_by(title=book_data['title']).first()
            if not existing_book:
                book = Book(
                    title=book_data['title'],
                    description=book_data['description'],
                    year=book_data['year'],
                    publisher=book_data['publisher'],
                    author=book_data['author'],
                    pages=book_data['pages']
                )
                
                # Добавляем жанры
                for genre_name in book_data['genres']:
                    if genre_name in genre_objects:
                        book.genres.append(genre_objects[genre_name])
                
                db.session.add(book)
        
        try:
            db.session.commit()
            print("Начальные данные успешно добавлены!")
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при добавлении данных: {e}")

if __name__ == '__main__':
    add_initial_data() 