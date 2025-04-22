# vocabulary
import sqlalchemy
import psycopg2
print(sqlalchemy.__version__, psycopg2.__version__)

from datetime import datetime, timezone
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy import inspect
import sys
from models import Base, User, Lesson, Phrase, UserWord, UserProgress
from typing import List, Optional
from datetime import datetime, timezone



class DBSession:
    # PostgreSQL  # db = DBSession("postgresql://user:password@localhost/bookstore")
    # MySQL  # db = DBSession("mysql+pymysql://user:password@localhost/bookstore")
    # db_url="sqlite:///bookstore.db"
    #def __init__(self, db_url="postgresql://user:password@localhost/bookstore"):
    def __init__(self, dbname="postgres", host="127.0.0.1", user="postgres", password="****", port=5432):
        self._dbname = dbname
        self._host = host
        self._user = user
        self._password = password
        self._port = port
        self.engine = None
        self.session = None
        self._is_connected = False  # Флаг успешного подключения

        self.system_db_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"
        self.db_url = f"postgresql://{self._user}:{self._password}@{self._host}/{self._dbname}"
        if not self._connect():
            print("Нет подключения при инициализации")
            #sys.exit(1)  # Завершаем программу


    def _connect(self):
        """Устанавливает соединение с базой данных"""
        try:
            db_url = f"postgresql://{self._user}:{self._password}@{self._host}/{self._dbname}"
            self.engine = create_engine(db_url)
            # Проверка подключения через тестовый запрос
            with self.engine.connect() as test_conn:
                test_conn.execute(text("SELECT 1"))

            # Если дошли сюда - подключение успешно
            self._is_connected = True
            #Base.metadata.create_all(self.engine) #авто с
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            print(f"Успешное подключение к базе {self._dbname}")
            return True

        except OperationalError as e:
            print(f"ОШИБКА: Не удалось подключиться к базе {self._dbname}")
            print(f"Детали: {e}")
            return False

        except Exception as e:
            print(f"Неизвестная ошибка при подключении: {e}")
            return False

    def is_connected(self):
        """Проверяет активное подключение к БД"""
        if not self._is_connected:
            return False
        try:
            # Дополнительная проверка через тестовый запрос
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except:
            self._is_connected = False
            return False


    def __del__(self):
        """Закрывает соединение при удалении объекта"""
        if hasattr(self, 'session') and self.session:
            self.close()

    def close(self):
        self.session.close()


    def create_db(self, db_name):
        """Создает новую БД (использует psycopg2 напрямую)"""
        try:
            # Подключаемся к системной БД без SQLAlchemy
            conn = psycopg2.connect(
                dbname="postgres",
                user=self._user,
                password=self._password,
                host=self._host,
                port=self._port,
                # Отключаем autocommit=False по умолчанию
                #autocommit=True
            )
            conn.autocommit = True  # Явное указание

            with conn.cursor() as cursor:
                # Безопасное формирование SQL с использованием sql.Identifier
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name) ))
                print(f"БД {db_name} создана")

                # Обновляем подключение к новой БД
                self._dbname = db_name
                self._connect()

            return f"postgresql://{self._user}:{self._password}@{self._host}:{self._port}/{db_name}"

        except Exception as e:
            print(f"Ошибка при создании БД: {e}")
            raise

    def drop_db(self, db_name):
        """Удаляет БД (использует psycopg2 напрямую)"""
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user=self._user,
                password=self._password,
                host=self._host,
                port=self._port,
                #autocommit=True
            )
            conn.autocommit = True
            with conn.cursor() as cursor:
                # Завершаем все соединения с БД
                cursor.execute("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = %s
                    AND pid <> pg_backend_pid();
                """, (db_name,))

                # Удаляем БД
                cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))
                print(f"БД {db_name} удалена")
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при удалении БД: {e}")
            return False


    def db_exists(self, db_name):
        """Проверяет существование БД"""
        engine = create_engine(self.system_db_url)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 1 FROM pg_database WHERE datname = :db_name
            """), {'db_name': db_name})
            return bool(result.scalar())

    def create_tables(self):
        """
        Создает все таблицы в базе данных на основе ORM-моделей
        из модуля models.py (Users, Lessons ...)
        """
        if not self.is_connected():
            print("Ошибка: Нет подключения к БД!")
            return False
        try:
            # Создаем все таблицы, определенные в Base.metadata
            Base.metadata.create_all(self.engine)
            # Проверяем, что таблицы действительно созданы
            inspector = inspect(self.engine)
            required_tables = {'lessons', 'users', 'phrases', 'user_words'}
            existing_tables = set(inspector.get_table_names())

            if not required_tables.issubset(existing_tables):
                missing_tables = required_tables - existing_tables
                print(f"Ошибка: Не созданы таблицы: {missing_tables}")
                return False

            print("Все таблицы успешно созданы")
            return True

        except Exception as e:
            print(f"Ошибка при создании таблиц: {e}")
            return False
            #print("Все таблицы успешно созданы")
            # # Проверяем, что таблицы действительно созданы
            #inspector = inspect(self.engine)
            #existing_tables = inspector.get_table_names()
            #required_tables = ['lessons', 'users', 'phrases', 'user_words']
            #for table in required_tables:
            #    if table not in existing_tables:
            #        print(f"Предупреждение: Таблица {table} не создана")


    def drop_tables(self):
        """
        Удаляет все таблицы из базы данных (все - данные будут потеряны)
        """
        try:
            Base.metadata.drop_all(self.engine)
            print("Все таблицы удалены")
        except Exception as e:
            print(f"Ошибка при удалении таблиц: {e}")
            raise



class CRUDOperations:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    # User
    def create_user(self, telegram_id: str, username: str, ui_language: str = 'ru',
                    target_language: str = 'en') -> User:
        """Добавить поьзователя"""
        with self.Session() as session:
            user = User(
                telegram_id=telegram_id,
                username=username,
                ui_language=ui_language,
                target_language=target_language
            )
            session.add(user)
            session.commit()
            return user

    def get_user_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        """Получить юзера по Telegram ID"""
        with self.Session() as session:
            return session.query(User).filter(User.telegram_id == telegram_id).first()

    def get_all_users(self):
        with self.Session() as session:
            return session.query(User).all()

    def get_user_by_id(self, p_uid: str) -> Optional[User]:
        """Получить юзера по ID"""
        with self.Session() as session:
            return session.query(User).filter(User.id == p_uid).first()

    def update_user_language(self, telegram_id: str, ui_language: str = None, target_language: str = None) -> Optional[
        User]:
        """Изменить языки юзера"""
        with self.Session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                if ui_language:
                    user.ui_language = ui_language
                if target_language:
                    user.target_language = target_language
                user.last_active_date = datetime.now(timezone.utc)
                session.commit()
            return user

    def update_user_activity(self, telegram_id: str) -> None:
        """Обновить активность"""
        with self.Session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.last_active_date = datetime.now(timezone.utc)
                session.commit()

    # Lesson operations
    def create_lesson(self, title: str, description: str = None, difficulty_level: int = 1) -> Lesson:
        """Добавить урок"""
        with self.Session() as session:
            lesson = Lesson(
                title=title,
                description=description,
                difficulty_level=difficulty_level
            )
            session.add(lesson)
            session.commit()
            return lesson

    def get_lesson_by_id(self, lesson_id: int) -> Optional[Lesson]:
        """Получить урок по ID"""
        with self.Session() as session:
            return session.query(Lesson).filter(Lesson.id == lesson_id).first()

    def get_all_lessons(self) -> List[Lesson]:
        """Список уроков"""
        with self.Session() as session:
            return session.query(Lesson).all()

    def update_lesson(self, lesson_id: int, title: str = None, description: str = None, difficulty_level: int = None) -> \
    Optional[Lesson]:
        with self.Session() as session:
            lesson = session.query(Lesson).filter(Lesson.id == lesson_id).first()
            if lesson:
                if title:
                    lesson.title = title
                if description:
                    lesson.description = description
                if difficulty_level:
                    lesson.difficulty_level = difficulty_level
                session.commit()
            return lesson

    # Phrase
    def create_phrase(self, lesson_id: int, text_ru: str, text_en: str, text_zh: str,
                      category: str = None, usage_example: str = None) -> Phrase:
        """Новая фраза"""
        with self.Session() as session:
            phrase = Phrase(
                lesson_id=lesson_id,
                text_ru=text_ru,
                text_en=text_en,
                text_zh=text_zh,
                category=category,
                usage_example=usage_example
            )
            session.add(phrase)
            session.commit()
            return phrase

    def get_phrase_by_id(self, phrase_id: int) -> Optional[Phrase]:
        """Получить по ID"""
        with self.Session() as session:
            return session.query(Phrase).filter(Phrase.id == phrase_id).first()

    def get_phrases_by_lesson(self, lesson_id: int) -> List[Phrase]:
        """Все фразы урока"""
        with self.Session() as session:
            return session.query(Phrase).filter(Phrase.lesson_id == lesson_id).all()

    def get_all_phrases(self):
        """Все фразы """
        with self.Session() as session:
            return session.query(Phrase).all()

    def update_phrase(self, phrase_id: int, text_ru: str = None, text_en: str = None, text_zh: str = None,
                      category: str = None, usage_example: str = None) -> Optional[Phrase]:
        """Изменить фразу"""
        with self.Session() as session:
            phrase = session.query(Phrase).filter(Phrase.id == phrase_id).first()
            if phrase:
                if text_ru:
                    phrase.text_ru = text_ru
                if text_en:
                    phrase.text_en = text_en
                if text_zh:
                    phrase.text_zh = text_zh
                if category:
                    phrase.category = category
                if usage_example:
                    phrase.usage_example = usage_example
                session.commit()
            return phrase

    # UserWord / словарь юзера
    def add_word_to_user_vocabulary(self, user_id: int, phrase_id: int) -> UserWord:
        """Добавить"""
        with self.Session() as session:
            # Слово уже есть
            existing_word = session.query(UserWord).filter(
                UserWord.user_id == user_id,
                UserWord.phrase_id == phrase_id
            ).first()

            if existing_word:
                return existing_word

            user_word = UserWord(
                user_id=user_id,
                phrase_id=phrase_id,
                last_review=datetime.now(timezone.utc)
            )
            session.add(user_word)
            session.commit()
            return user_word

    def get_user_word(self, user_id: int, phrase_id: int) -> Optional[UserWord]:
        """Получить слово из словаря юзера, vocabulary"""
        with self.Session() as session:
            return session.query(UserWord).filter(
                UserWord.user_id == user_id,
                UserWord.phrase_id == phrase_id
            ).first()

    def get_user_vocabulary(self, user_id: int) -> List[UserWord]:
        """Получить список слов пользователя"""
        with self.Session() as session:
            return session.query(UserWord).filter(UserWord.user_id == user_id).all()

    def update_user_word_progress(self, user_id: int, phrase_id: int, is_learned: bool = None,
                                  repetition_count: int = None) -> Optional[UserWord]:
        """Изменить результат изучения"""
        with self.Session() as session:
            user_word = session.query(UserWord).filter(
                UserWord.user_id == user_id,
                UserWord.phrase_id == phrase_id
            ).first()

            if user_word:
                if is_learned is not None:
                    user_word.is_learned = is_learned
                if repetition_count is not None:
                    user_word.repetition_count = repetition_count

                user_word.last_review = datetime.now(timezone.utc)
                session.commit()

            return user_word

    def remove_word_from_user_vocabulary(self, user_id: int, phrase_id: int) -> bool:
        """Удалить"""
        with self.Session() as session:
            user_word = session.query(UserWord).filter(
                UserWord.user_id == user_id,
                UserWord.phrase_id == phrase_id
            ).first()

            if user_word:
                session.delete(user_word)
                session.commit()
                return True
            return False

    # UserProgress
    def start_or_update_lesson_progress(self, user_id: int, lesson_id: int,
                                        is_completed: bool = False, score: int = 0) -> UserProgress:
        """Старт стоп изучение урока"""
        with self.Session() as session:
            progress = session.query(UserProgress).filter(
                UserProgress.user_id == user_id,
                UserProgress.lesson_id == lesson_id
            ).first()

            if not progress:
                progress = UserProgress(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    is_completed=is_completed,
                    score=score
                )
                session.add(progress)
            else:
                progress.repetition_count += 1
                if is_completed:
                    progress.is_completed = is_completed
                    progress.completion_date = datetime.now(timezone.utc)
                if score > progress.score:
                    progress.score = score

            session.commit()
            return progress

    def get_user_progress(self, user_id: int, lesson_id: int) -> Optional[UserProgress]:
        """результат юзера по уроку"""
        with self.Session() as session:
            return session.query(UserProgress).filter(
                UserProgress.user_id == user_id,
                UserProgress.lesson_id == lesson_id
            ).first()

    def get_all_user_progress(self, user_id: int) -> List[UserProgress]:
        """все данные по прогрессу пользователя"""
        with self.Session() as session:
            return session.query(UserProgress).filter(
                UserProgress.user_id == user_id
            ).all()

    def complete_lesson(self, user_id: int, lesson_id: int, score: int) -> Optional[UserProgress]:
        """урок завершен"""
        with self.Session() as session:
            progress = session.query(UserProgress).filter(
                UserProgress.user_id == user_id,
                UserProgress.lesson_id == lesson_id
            ).first()

            if progress:
                progress.is_completed = True
                progress.completion_date = datetime.now(timezone.utc)
                progress.score = score
                session.commit()
            else:
                progress = self.start_or_update_lesson_progress(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    is_completed=True,
                    score=score
                )

            return progress


if __name__ == '__main__':
    # тест
    db = DBSession(dbname="lfl", host="127.0.0.1", user="postgres", password="****", port=5432)
    print(db)
    # Инициализация
    db_url = "postgresql://postgres:****@localhost/lfl"
    crud = CRUDOperations(db_url)

    # Создание пользователя
    #user1 = crud.create_user(telegram_id="123456", username="test_user1")
    #user2 = crud.create_user(telegram_id="456789", username="test_user2")

    # Получение пользователя
    user3 = crud.get_user_by_telegram_id("123456")

    # Создание урока
    # lesson1 = crud.create_lesson(title="Lesson 1", description="Desc lesson 1")
    # lesson2 = crud.create_lesson(title="Basic Phrases", description="Common everyday phrases")
    lesson1 = crud.get_lesson_by_id(1)
    print(lesson1)

    # Добавление фразы в урок
    phrase = crud.create_phrase(
        lesson_id=lesson1.id,
        text_ru="Привет",
        text_en="Hello",
        text_zh="你好",
        category="greetings, meeting"
    )

    phrase2 = crud.get_phrase_by_id(1)
    # Добавление слова в словарь пользователя
    user_word = crud.add_word_to_user_vocabulary(user_id=user3.id, phrase_id=phrase2.id)

    # Обновление прогресса изучения слова
    crud.update_user_word_progress(
        user_id=user3.id,
        phrase_id=phrase2.id,
        is_learned=True,
        repetition_count=3
    )

     # Отметить урок как пройденный
    progress = crud.complete_lesson(
        user_id=user3.id,
        lesson_id=lesson1.id,
        score=95
    )