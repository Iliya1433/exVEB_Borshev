from app import app, db
from models import Book, Cover
import os
import requests
from PIL import Image
from io import BytesIO
import hashlib

def download_and_save_cover(url, book_id):
    try:
        # Скачиваем изображение
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Не удалось скачать обложку для книги {book_id}")
            return None
        
        # Получаем содержимое файла
        file_content = response.content
        
        # Создаем MD5 хеш
        md5_hash = hashlib.md5(file_content).hexdigest()
        
        # Проверяем, существует ли уже такая обложка
        existing_cover = Cover.query.filter_by(md5_hash=md5_hash).first()
        if existing_cover:
            return existing_cover
        
        # Определяем MIME-тип
        mime_type = response.headers.get('content-type', 'image/jpeg')
        
        # Создаем объект обложки
        cover = Cover(
            filename=f"cover_{book_id}.jpg",
            mime_type=mime_type,
            md5_hash=md5_hash
        )
        db.session.add(cover)
        db.session.flush()
        
        # Сохраняем файл
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(cover.id))
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return cover
    except Exception as e:
        print(f"Ошибка при обработке обложки для книги {book_id}: {e}")
        return None

def add_covers():
    with app.app_context():
        # Словарь с URL обложек для книг
        cover_urls = {
            '1984': 'https://imo10.labirint.ru/books/860997/cover.jpg/484-0',
            'Атлант расправил плечи': 'https://cdn.litres.ru/pub/c/cover_415/4236675.webp',
            'Психология влияния': 'https://cdn.litres.ru/pub/c/cover_415/127790.webp',
            'Властелин колец': 'https://cdn.litres.ru/pub/c/cover_415/147165.webp',
            'Гарри Поттер и философский камень': 'https://cdn.litres.ru/pub/c/cover_415/71512585.webp',
            'Игра престолов': 'https://cdn.litres.ru/pub/c/cover_415/42805691.webp',
            'Метро 2033': 'https://cdn.litres.ru/pub/c/cover_415/128391.webp',
            'Богатый папа, бедный папа': 'https://cdn.litres.ru/pub/c/cover_415/119256.webp'
        }
        
        for title, url in cover_urls.items():
            book = Book.query.filter_by(title=title).first()
            if book:
                cover = download_and_save_cover(url, book.id)
                if cover:
                    book.cover_id = cover.id
                    print(f"Добавлена обложка для книги '{title}'")
        
        try:
            db.session.commit()
            print("Обложки успешно добавлены!")
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при добавлении обложек: {e}")

if __name__ == '__main__':
    add_covers() 