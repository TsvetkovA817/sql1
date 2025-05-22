# vocabulary
import random
import sqlalchemy
import psycopg2
from sqlalchemy.sql.functions import random

print(sqlalchemy.__version__, psycopg2.__version__)

from datetime import datetime, timezone
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text, func, inspect
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import (
    OperationalError,
    SQLAlchemyError,
    IntegrityError,
    DataError,
    DatabaseError
)
import sys
from datetime import datetime, timezone
import logging
from typing import Optional, Union, List, Dict, Any, Tuple
from contextlib import contextmanager
from time import sleep
from models import Base, User, Lesson, Phrase, UserWord, UserProgress

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DBSession:
    def __init__(self, dbname="postgres", host="127.0.0.1", user="postgres", password="****", port=5432,
                 max_retries=3, retry_delay=1):
        self._dbname = dbname
        self._host = host
        self._user = user
        self._password = password
        self._port = port
        self.engine = None
        self.Session = None
        self._is_connected = False  # Флаг успешного подключения
        self.max_retries = max_retries  # Попытки подключения
        self.retry_delay = retry_delay

        self.system_db_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"
        self.db_url = f"postgresql://{self._user}:{self._password}@{self._host}/{self._dbname}"
        self._connect_with_retry()
        # if not self._connect():
        #     print("Нет подключения")
        # sys.exit(1)  # Завершаем программу

    def _connect_with_retry(self):
        """Попытка подключения c повторами"""
        for attempt in range(self.max_retries):
            try:
                if self._connect():
                    return
            except Exception as e:
                logger.error(f"Попытка {attempt + 1}, не удачных: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise ConnectionError(f"Не подключились к БД после {self.max_retries} попыток")
                sleep(self.retry_delay)

    def _connect(self) -> bool:
        """Устанавливает соединение с базой данных"""
        try:

            # db_url = f"postgresql://{self._user}:{self._password}@{self._host}/{self._dbname}"
            # self.engine = create_engine(db_url)

            self.engine = create_engine(
                self.db_url,
                pool_pre_ping=True,  # Проверка соединения перед использованием
                pool_recycle=3600,  # Переподключение каждый час
                echo=False  # Логирование SQL (откл)
            )

            # Проверка подключения через тестовый запрос
            with self.engine.connect() as test_conn:
                test_conn.execute(text("SELECT 1"))
                test_conn.close()

            # Если дошли сюда - подключение успешно
            self._is_connected = True
            # Base.metadata.create_all(self.engine) #авто с
            # Session = sessionmaker(bind=self.engine)
            # self.session = Session()

            # sessionmaker - cоздает фабрику сессий
            # scoped_session() -  контейнер для сессий обеспечивает:
            # работу (безопасность в многопоточной среде)
            # единую сессию на поток (одна и та же сессия будет возвращаться в пределах одного потока)
            # автоматическое управление жизненным циклом сессии

            self.Session = scoped_session(sessionmaker(
                bind=self.engine,  # Привязывает сессии к созданному движку БД
                autocommit=False,  # Отключает авто-коммит (требует явного commit())
                autoflush=False,  # Отключает автоматический flush перед запросами
                expire_on_commit=False  # Не сбрасывает состояние объектов после коммита
            ))
            logger.info(f"Успешное подключение к базе {self._dbname}")
            # print(f"Успешное подключение к базе {self._dbname}")
            return True
        # проблема с сетью или доступом к БД
        except OperationalError as e:
            logger.error(f"ОШИБКА: Не удалось подключиться к базе {self._dbname}")
            logger.error(f"Детали: {str(e)}")
            self._is_connected = False
            raise
            # return False # Возврат `False` скрыл бы проблему, сделав отладку сложнее

        # ошибка в запросе или конфигурации
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError: ошибка при подключении к БД ")
            logger.error(f"Подробно: {str(e)}")
            self._is_connected = False
            raise

        except Exception as e:
            # print(f"Неизвестная ошибка при подключении: {e}")
            # return False
            logger.error(f"Неизвестная ошибка при подключении к БД")
            logger.error(f"Подробнее: {str(e)}")
            self._is_connected = False
            raise

    def is_connected(self):
        """Проверяет активное подключение к БД"""
        if not self._is_connected:
            return False
        try:
            # Дополнительная проверка через тестовый запрос
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        # обработка ошибок
        except SQLAlchemyError as e:
            logger.error(f"Ошибка соединения с базой данных: {str(e)}")
            self._is_connected = False
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке соединения с базой данных: {str(e)}")
            self._is_connected = False
            return False

    def __del__(self):
        """Закрывает соединение при удалении объекта"""
        self.close()

    def close(self):
        """Закрывает соединение с БД"""
        try:
            if hasattr(self, 'Session') and self.Session:
                self.Session.remove()
            if hasattr(self, 'engine') and self.engine:
                self.engine.dispose()
            self._is_connected = False
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error while closing connection: {str(e)}")

    def create_db(self, db_name) -> str:
        """Создает новую БД (использует psycopg2 напрямую)"""
        try:
            # Подключаемся к системной БД без SQLAlchemy
            conn = psycopg2.connect(
                dbname="postgres",
                user=self._user,
                password=self._password,
                host=self._host,
                port=self._port,
            )
            conn.autocommit = True  # Явное указание

            with conn.cursor() as cursor:
                # Проверяем, не существует ли уже БД
                cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                if cursor.fetchone():
                    logger.warning(f"Database {db_name} already exists")
                    return f"postgresql://{self._user}:***@{self._host}:{self._port}/{db_name}"
                # Создаем БД
                # Безопасное формирование SQL с использованием sql.Identifier
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
                logger.info(f"БД {db_name} создана")
                # print(f"БД {db_name} создана")

                # Обновляем подключение к новой БД
                self._dbname = db_name
                self._connect_with_retry()

            return f"postgresql://{self._user}:***@{self._host}:{self._port}/{db_name}"

        except psycopg2.OperationalError as e:
            logger.error(f"OperationalError при создании БД: {str(e)}")
            raise
        except psycopg2.DatabaseError as e:
            logger.error(f"DatabaseError при создании БД: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при создании БД: {e}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

    def drop_db(self, db_name):
        """Удаляет БД (использует psycopg2 напрямую)"""
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user=self._user,
                password=self._password,
                host=self._host,
                port=self._port,
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
                logger.info(f"БД {db_name} удалена")
            conn.close()
            return True

        except psycopg2.OperationalError as e:
            logger.error(f"OperationalError при удалении БД: {str(e)}")
            return False
        except psycopg2.DatabaseError as e:
            logger.error(f"DatabaseError при удалении БД: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при удалении БД: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

    def db_exists(self, db_name: str) -> bool:
        """Проверяет существование БД"""
        try:
            engine = create_engine(self.system_db_url)
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 1 FROM pg_database WHERE datname = :db_name
                """), {'db_name': db_name})
                return bool(result.scalar())
        except OperationalError as e:
            logger.error(f"OperationalError при проверке БД: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке БД: {str(e)}")
            return False

    def create_tables(self):
        """
        Создает все таблицы в базе данных на основе ORM-моделей
        из модуля models.py (Users, Lessons ...)
        """
        if not self.is_connected():
            logger.error("Ошибка: Нет подключения к БД!")
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
                logger.error(f"Ошибка: Не созданы таблицы: {missing_tables}")
                return False

            logger.info("Все таблицы успешно созданы")
            return True
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError при создании таблиц: {str(e)}")
            return False
        except Exception as e:
            print(f"Ошибка при создании таблиц: {e}")
            return False

            # # Проверяем, что таблицы действительно созданы
            # inspector = inspect(self.engine)
            # existing_tables = inspector.get_table_names()
            # required_tables = ['lessons', 'users', 'phrases', 'user_words']
            # for table in required_tables:
            #    if table not in existing_tables:
            #        print(f"Предупреждение: Таблица {table} не создана")

    def drop_tables(self) -> bool:
        """
        Удаляет все таблицы из базы данных (все - данные будут потеряны)
        """
        if not self.is_connected():
            logger.error("Нет соединения с БД")
            return False
        try:
            Base.metadata.drop_all(self.engine)
            logger.info("Все таблицы удалены")
            return True
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError при удалении таблиц: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при удалении таблиц: {e}")
            return False


class CRUDOperations:
    def __init__(self, database_url: str):
        try:
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            logger.info("CRUDOperations инициализация успешна")
        except OperationalError as e:
            logger.error(f"OperationalError Ошибка при соединении с БД: {str(e)}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError при инициализации: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            raise

    @contextmanager
    def _session_scope(self):
        """Менеджер для управления сессиями"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Вн.ошибка: {str(e)}")
            raise
        except DataError as e:
            session.rollback()
            logger.error(f"Ошибка данных: {str(e)}")
            raise
        except DatabaseError as e:
            session.rollback()
            logger.error(f"Ошибка БД: {str(e)}")
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка: {str(e)}")
            raise
        finally:
            session.close()

    # User
    def create_user(self, telegram_id: str, username: str, ui_language: str = 'ru',
                    target_language: str = 'en') -> Tuple[Optional[User], Optional[str]]:
        """Добавить поьзователя"""
        try:
            with self._session_scope() as session:
                # Существует ли уже пользователь
                if session.query(User).filter(User.telegram_id == telegram_id).first():
                    logger.warning(f"Пользователь с ИД {telegram_id} уже есть")
                    return None, "Пользователь уже есть"

                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    ui_language=ui_language,
                    target_language=target_language,
                    create_date=datetime.now(timezone.utc),
                    last_active_date=datetime.now(timezone.utc)
                )
                session.add(user)
                logger.info(f"Добавлен пользователь: {telegram_id}")
                return user, None
        except IntegrityError as e:
            logger.error(f"IntegrityError при создании пользователя: {str(e)}")
            return None, "IntegrityError"
        except DataError as e:
            logger.error(f"Ошибка данных при создании пользователя: {str(e)}")
            return None, "Ошибка данных"
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            return None, "Ошибка при создании пользователя"

    def get_user_by_telegram_id(self, telegram_id: str) -> Tuple[Optional[User], Optional[str]]:
        """Получить юзера по Telegram ID"""
        try:
            with self._session_scope() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                if not user:
                    logger.warning(f"Пользователь с ИД {telegram_id} не найден")
                return user, None
        except Exception as e:
            logger.error(f"Ошибка при получении данных пользователя: {str(e)}")
            return None, 'Ошибка'

    def get_all_users(self) -> Tuple[Optional[List[User]], Optional[str]]:
        """Получить всех пользователей"""
        try:
            with self._session_scope() as session:
                return session.query(User).all(), None
        except Exception as e:
            logger.error(f"Оибка при получении пользователей : {str(e)}")
            return None, "Ошибка"

    def get_user_by_id(self, p_uid: str) -> Optional[User]:
        """Получить юзера по ID"""
        try:
            with self._session_scope() as session:
                user = session.query(User).filter(User.id == p_uid).first()
                if not user:
                    logger.warning(f"Пользователь id {p_uid} не найден")
                return user
        except Exception as e:
            logger.error(f"Ошибка получения юзера по ид: {str(e)}")
            return None

    def update_user_language(self, telegram_id: str, ui_language: str = None,
                             target_language: str = None) -> Tuple[Optional[User], Optional[str]]:
        """Изменить языки юзера"""
        try:
            with self._session_scope() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                if not user:
                    logger.warning(f"Пользователь {telegram_id} не найден")
                    return None, "Пользователь не найден"

                if ui_language:
                    user.ui_language = ui_language
                if target_language:
                    user.target_language = target_language
                user.last_active_date = datetime.now(timezone.utc)

                logger.info(f"Обновление языка для пользователя {telegram_id}")
                return user, None
        except DataError as e:
            logger.error(f"Data error при обновлении языка: {str(e)}")
            return None, "Ошибка данных"
        except Exception as e:
            logger.error(f"Ошибка при обновлении языка: {str(e)}")
            return None, "Ошибка при обновлении языка"

    def update_user_activity(self, telegram_id: str) -> None:
        """Обновить активность"""
        with self.Session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.last_active_date = datetime.now(timezone.utc)
                session.commit()

    # Методы для уроков
    def create_lesson(self, title: str, description: str = None,
                      difficulty_level: int = 1) -> Tuple[Optional[Lesson], Optional[str]]:
        """Добавить урок"""
        try:
            with self._session_scope() as session:
                lesson = Lesson(
                    title=title,
                    description=description,
                    difficulty_level=difficulty_level,
                    create_date=datetime.now(timezone.utc)
                )
                session.add(lesson)
                logger.info(f"Создан новый урок: {title}")
                return lesson, None
        except IntegrityError as e:
            logger.error(f"Integrity error при создании урока: {str(e)}")
            return None, "Integrity error при создании урока"
        except Exception as e:
            logger.error(f"Ошибка при создании урока: {str(e)}")
            return None, "Ошибка при создании урока"

    def get_lesson_by_id(self, lesson_id: int) -> Optional[Lesson]:
        """Получить урок по ID"""
        try:
            with self._session_scope() as session:
                lesson = session.query(Lesson).filter(Lesson.id == lesson_id).first()
                if not lesson:
                    logger.warning(f"Урок с ИД {lesson_id} не найден")
                return lesson
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            return None

    def get_all_lessons(self) -> Optional[List[Lesson]]:
        """Список уроков"""
        # with self.Session() as session:
        #     return session.query(Lesson).all()
        try:
            with self._session_scope() as session:
                lessons = session.query(Lesson).all()
                if not lessons:
                    logger.warning(f"Уроки не получены")
                return lessons
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            return None

    def update_lesson(self, lesson_id: int, title: str = None, description: str = None,
                      difficulty_level: int = None) -> Tuple[Optional[Lesson], Optional[str]]:
        """Обновить данные"""
        try:
            with self._session_scope() as session:
                lesson = session.query(Lesson).filter(Lesson.id == lesson_id).first()
                if not lesson:
                    logger.warning(f"Lesson {lesson_id} not found for update")
                    return None, "Lesson not found"

                if title:
                    lesson.title = title
                if description:
                    lesson.description = description
                if difficulty_level:
                    lesson.difficulty_level = difficulty_level

                logger.info(f"Обновлен урок {lesson_id}")
                return lesson, None
        except Exception as e:
            logger.error(f"Ошибка : {str(e)}")
            return None, "Ошибка"

    # Phrase операции со словарем
    def create_phrase(self, lesson_id: int, text_ru: str, text_en: str, text_zh: str, category: str = None,
                      usage_example: str = None) -> Tuple[Optional[Phrase], Optional[str]]:
        """Новая фраза"""
        try:
            with self.Session() as session:
                # Проверяем существование урока
                if not session.query(Lesson).filter(Lesson.id == lesson_id).first():
                    logger.warning(f"Урок {lesson_id} не найден")
                    return None, "Урок не найден"

                phrase = Phrase(
                    lesson_id=lesson_id,
                    text_ru=text_ru,
                    text_en=text_en,
                    text_zh=text_zh,
                    category=category,
                    usage_example=usage_example,
                )
                session.add(phrase)
                logger.info(f"Создана фраза в уроке {lesson_id}")
                return phrase, None

        except IntegrityError as e:
            logger.error(f"Integrity error при создании фразы: {str(e)}")
            return None, "Ошибка"
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            return None, "Ошибка"

    def get_phrase_by_id(self, phrase_id: int) -> Optional[Phrase]:
        """Получить по ID"""
        with self.Session() as session:
            return session.query(Phrase).filter(Phrase.id == phrase_id).first()

    def get_all_phrases(self) -> Tuple[Optional[List[Phrase]], Optional[str]]:
        """Все фразы """
        # with self.Session() as session:
        #     return session.query(Phrase).all()
        try:
            with self._session_scope() as session:
                phrases = session.query(Phrase).all()
                if not phrases:
                    logger.warning(f"Нет словаря")
                return phrases, None
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            return None, "Ошибка"

    def get_phrases_by_lesson(self, lesson_id: int) -> Tuple[Optional[List[Phrase]], Optional[str]]:
        """Все фразы урока"""
        try:
            with self._session_scope() as session:
                phrases = session.query(Phrase).filter(Phrase.lesson_id == lesson_id).all()
                if not phrases:
                    logger.warning(f"Нет словаря для урока {lesson_id}")
                return phrases, None
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            return None, "Ошибка"

    def update_phrase(self, phrase_id: int, text_ru: str = None, text_en: str = None, text_zh: str = None,
                      category: str = None, usage_example: str = None) -> Tuple[Optional[Phrase], Optional[str]]:
        """Изменить фразу"""
        try:
            with self.Session() as session:
                # Проверяем существование фразы
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
                else:
                    logger.warning(f"фраза {phrase_id} не найдена")
                    return None, "Фраза не найдена"

                logger.info(f"Изменена фраза {phrase_id}")
                return phrase, None
        except IntegrityError as e:
            logger.error(f"Integrity error при обновлении: {str(e)}")
            return None, "Ошибка"
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            return None, "Ошибка"

    # UserWord / словарь юзера
    def add_word_to_user_vocabulary(self, user_id: int,
                                    phrase_id: int) -> Tuple[Optional[UserWord], Optional[str]]:
        """Добавить слово в словарь пользователя"""
        try:
            with self._session_scope() as session:
                # Проверяем существование пользователя и фразы
                if not session.query(User).filter(User.id == user_id).first():
                    return None, "Юзер пропал"
                if not session.query(Phrase).filter(Phrase.id == phrase_id).first():
                    return None, "Слова нет в общем словаре"

                # Проверяем, есть ли это слово в словаре этого юзера
                existing = session.query(UserWord).filter(
                    UserWord.user_id == user_id,
                    UserWord.phrase_id == phrase_id
                ).first()

                if existing:
                    logger.info(f"Слово {phrase_id} уже есть у пользователя {user_id}")
                    return existing, "Слово уже есть"

                user_word = UserWord(
                    user_id=user_id,
                    phrase_id=phrase_id,
                    last_review=datetime.now(timezone.utc),
                )
                session.add(user_word)
                logger.info(f"Добавлена фраза {phrase_id} в словарь пользователя {user_id}")
                return user_word, None
        except IntegrityError as e:
            logger.error(f"Integrity ошибка: {str(e)}")
            return None, "Ошибка"
        except Exception as e:
            logger.error(f"Ошибка при добавлении слова в словарь польователя: {str(e)}")
            return None, "Ошибка"

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

    def update_user_word_progress(self, user_id: int, phrase_id: int,
                                  is_learned: bool = None,
                                  repetition_count: int = None) -> Tuple[Optional[UserWord], Optional[str]]:
        """Обновить резултат изучения слова"""
        try:
            with self._session_scope() as session:
                user_word = session.query(UserWord).filter(
                    UserWord.user_id == user_id,
                    UserWord.phrase_id == phrase_id
                ).first()

                if not user_word:
                    logger.warning(f"Не найдена фраза {user_id}, фраза {phrase_id}")
                    return None, "Слова нет в пользовательском словаре"

                if is_learned is not None:
                    user_word.is_learned = is_learned
                    if is_learned:
                        user_word.learned_at = datetime.now(timezone.utc)
                if repetition_count is not None:
                    user_word.repetition_count = repetition_count

                user_word.last_review = datetime.now(timezone.utc)

                logger.info(f"Изменен прогресс по фразе {phrase_id} для юзера {user_id}")
                return user_word, None
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            return None, "Ошибка"

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
                                        is_completed: bool = False,
                                        score: int = 0) -> Tuple[Optional[UserProgress], Optional[str]]:
        """Начать или обновить прогресс урока"""
        try:
            with self._session_scope() as session:
                # Проверяем пользователя и урок
                if not session.query(User).filter(User.id == user_id).first():
                    return None, "Юзер не найден"
                if not session.query(Lesson).filter(Lesson.id == lesson_id).first():
                    return None, "Урока нет"

                progress = session.query(UserProgress).filter(
                    UserProgress.user_id == user_id,
                    UserProgress.lesson_id == lesson_id
                ).first()

                if not progress:
                    progress = UserProgress(
                        user_id=user_id,
                        lesson_id=lesson_id,
                        is_completed=is_completed,
                        score=score,
                        started_at=datetime.now(timezone.utc)
                    )
                    session.add(progress)
                    logger.info(f"Пользователь {user_id} начал урок {lesson_id}")
                else:
                    progress.repetition_count += 1
                    if is_completed:
                        progress.is_completed = is_completed
                        progress.completion_date = datetime.now(timezone.utc)
                    if score > progress.score:
                        progress.score = score
                    progress.updated_at = datetime.now(timezone.utc)
                    logger.info(f"Обновлен прогресс юзер {user_id} по уроку {lesson_id}")
                return progress, None
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            return None, "Ошибка"

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

    def complete_lesson(self, user_id: int, lesson_id: int, score: int) -> Tuple[Optional[UserProgress], Optional[str]]:
        """Урок завершен"""
        try:
            with self._session_scope() as session:
                progress = session.query(UserProgress).filter(
                    UserProgress.user_id == user_id,
                    UserProgress.lesson_id == lesson_id
                ).first()

                if progress:
                    progress.is_completed = True
                    progress.completion_date = datetime.now(timezone.utc)
                    progress.score = score
                    progress.updated_at = datetime.now(timezone.utc)
                else:
                    progress = UserProgress(
                        user_id=user_id,
                        lesson_id=lesson_id,
                        is_completed=True,
                        score=score,
                        started_at=datetime.now(timezone.utc),
                        completion_date=datetime.now(timezone.utc)
                    )
                    session.add(progress)

                logger.info(f"Урок {lesson_id} завершен юзером {user_id}")
                return progress, None
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            return None, "Ошибка"

    def update_user_lesson(self, telegram_id: str, lesson_id: int) -> Tuple[Dict[str, Any], Optional[str]]:
        """Обновляет текущий урок пользователя"""
        try:
            with self._session_scope() as session:
                # Получаем пользователя
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                if not user:
                    return {}, "User not found"

                # Проверяем существование урока
                lesson = session.query(Lesson).filter(Lesson.id == lesson_id).first()
                if not lesson:
                    return {}, "Lesson not found"

                # Обновляем урок
                user.current_lesson_id = lesson_id
                session.commit()

                return {
                           'user_id': user.id,
                           'lesson_id': lesson_id,
                           'lesson_title': lesson.title
                       }, None

        except Exception as e:
            logger.error(f"Error updating user lesson: {str(e)}")
            return {}, str(e)

    def get_or_create_user(self, telegram_id: str, username: str, ui_language: str,
                           target_language: str) -> Tuple[Optional[User], Optional[str]]:
        """Получает или создает пользователя"""
        try:
            user, error = self.get_user_by_telegram_id(telegram_id)
            if error:
                return None, error
            if not user:
                return self.create_user(telegram_id, username, ui_language, target_language)
            return user, None
        except Exception as e:
            return None, str(e)

    def get_user_stats(self, user_id: int) -> Tuple[Dict, Optional[str]]:
        """Возвращает статистику пользователя"""
        try:
            with self._session_scope() as session:
                word_count = session.query(func.count(UserWord.id)).filter(UserWord.user_id == user_id).scalar()
                learned_words = session.query(func.count(UserWord.id)).filter(
                    UserWord.user_id == user_id,
                    UserWord.is_learned == True
                ).scalar()

                user = session.query(User).filter(User.id == user_id).first()
                lesson_title = None
                if user and user.current_lesson_id:
                    lesson = session.query(Lesson).filter(Lesson.id == user.current_lesson_id).first()
                    lesson_title = lesson.title if lesson else None

                return {
                           'word_count': word_count or 0,
                           'learned_words': learned_words or 0,
                           'current_lesson_title': lesson_title
                       }, None
        except Exception as e:
            return {}, str(e)

    def get_learning_data(self, user_id: int, lesson_id: Optional[int] = None) -> Tuple[Dict, Optional[str]]:
        """Данные для изучения"""
        try:
            with self._session_scope() as session:
                # 1. Получаем пользователя
                user = session.query(User).get(user_id)
                if not user:
                    return {}, "User not found"

                # 2. Получаем фразы пользователя если есть
                user_phrases_query = session.query(Phrase).join(UserWord, UserWord.phrase_id == Phrase.id) \
                    .filter(UserWord.user_id == user_id)

                if lesson_id:
                    user_phrases_query = user_phrases_query.filter(Phrase.lesson_id == lesson_id)

                user_phrases = user_phrases_query.all()

                # 3. Определяем фразы для изучения
                phrases_query = session.query(Phrase)
                if not user_phrases:
                    # Если нет фраз у пользователя
                    if lesson_id:
                        phrases_query = phrases_query.filter(Phrase.lesson_id == lesson_id)
                else:
                    # Если есть фразы у пользователя
                    phrases_query = phrases_query.filter(Phrase.id.in_([p.id for p in user_phrases]))

                study_phrases = phrases_query.all()

                if not study_phrases:
                    return {}, "Словарь пуст"

                # 4. Выбираем случайную фразу для изучения
                current_phrase = session.query(Phrase) \
                    .filter(Phrase.id.in_([p.id for p in study_phrases])) \
                    .order_by(func.random()) \
                    .first()

                # 5. Получаем 3 случайные фразы из всех (исключая текущую)
                other_phrases = session.query(Phrase) \
                    .filter(Phrase.id != current_phrase.id) \
                    .order_by(func.random()) \
                    .limit(3) \
                    .all()

                # 6. Формируем результат
                return {
                           'current_phrase': {
                               'id': current_phrase.id,
                               'text_ru': current_phrase.text_ru,
                               'text_en': current_phrase.text_en,
                               'text_zh': current_phrase.text_zh,
                               'lesson_id': current_phrase.lesson_id
                           },
                           'other_phrases': [{
                               'id': p.id,
                               'text_ru': p.text_ru,
                               'text_en': p.text_en,
                               'text_zh': p.text_zh
                           } for p in other_phrases],
                           'target_language': user.target_language,
                           'ui_language': user.ui_language,
                           'all_phrases_count': len(study_phrases)
                       }, None

        except Exception as e:
            logger.error(f"ошибка в get_learning_data: {str(e)}")
            return {}, str(e)


if __name__ == '__main__':
    # тесты
    db = DBSession(dbname="lfl", host="127.0.0.1", user="postgres", password="***", port=5432)
    print(db)
    # Инициализация
    db_url = "postgresql://postgres:5432@localhost/lfl"
    crud = CRUDOperations(db_url)

    # Создание пользователя - ок
    # user1 = crud.create_user(telegram_id="12345677", username="test_user3")
    # user2 = crud.create_user(telegram_id="456789", username="test_user2")

    # Получение пользователя
    user3 = crud.get_user_by_telegram_id("123456")

    # Создание урока  ок
    # lesson1 = crud.create_lesson(title="Lesson 3", description="Desc lesson 3")
    # lesson2 = crud.create_lesson(title="Basic Phrases", description="Common everyday phrases")
    lesson1 = crud.get_lesson_by_id(1)
    print(lesson1)

    # Добавление фразы в урок ok
    # phrase = crud.create_phrase(
    #     lesson_id=lesson1.id,
    #     text_ru="Привет3",
    #     text_en="Hello3",
    #     text_zh="你好3",
    #     category="greetings, meeting"
    # )

    phrase2 = crud.get_phrase_by_id(3)
    # Добавление слова в словарь пользователя ok
    # user_word = crud.add_word_to_user_vocabulary(user_id=user3.id, phrase_id=phrase2.id)

    # Обновление прогресса изучения слова  ok
    crud.update_user_word_progress(
        user_id=user3.id,
        phrase_id=phrase2.id,
        is_learned=True,
        repetition_count=5
    )

    # Отметить урок как пройденный  ok
    progress = crud.complete_lesson(
        user_id=user3.id,
        lesson_id=lesson1.id,
        score=99
    )
