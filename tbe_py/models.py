# Прямые отношения используются для записи и управления связями
# Отношения через secondary таблицу  используются только для чтения (viewonly=True)
# Параметр overlaps явно указывает SQLAlchemy, какие отношения пересекаются
# можно упростить модели, оставив только один способ (например, только через secondary таблицу или только через прямые отношения)

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), unique=True, nullable=False)  # Идентификатор
    username = Column(String(100))  # Имя пользователя
    ui_language = Column(String(3), nullable=False, default='ru')  # ru/en/zh
    target_language = Column(String(3), nullable=False, default='en')  # Язык изучения
    create_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_active_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    current_lesson_id = Column(Integer, ForeignKey('lessons.id'), nullable=True)

    # Связи
    user_words = relationship("UserWord", back_populates="user")
    progress = relationship("UserProgress", back_populates="user")
    current_lesson = relationship("Lesson")

    def __repr__(self):
        return f"User(id={self.id}, username='{self.username}')"


class Lesson(Base):
    __tablename__ = 'lessons'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(300))
    difficulty_level = Column(Integer, default=1)  # Уровень сложности
    create_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Связи
    phrases = relationship("Phrase", back_populates="lesson")
    progress = relationship("UserProgress", back_populates="lesson")

    def __repr__(self):
        return f"Lesson(id={self.id}, title='{self.title}')"


class Phrase(Base):
    __tablename__ = 'phrases'

    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey('lessons.id'), nullable=False)

    # Тексты на разных языках
    text_ru = Column(String(100), nullable=False)
    text_en = Column(String(100), nullable=False)
    text_zh = Column(String(100), nullable=False)

    # Дополнительная информация
    category = Column(String(50))  # Например: "быт", "работа", "путешествия"
    usage_example = Column(String(500))  # Пример использования фразы

    # Связи
    lesson = relationship("Lesson", back_populates="phrases")
    user_words = relationship("UserWord", back_populates="phrase")

    def __repr__(self):
        return f"Phrase(id={self.id}, text_en='{self.text_en[:20]}...')"


class UserWord(Base):
    __tablename__ = 'user_words'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    phrase_id = Column(Integer, ForeignKey('phrases.id'), nullable=False)

    # Анализ изучения
    is_learned = Column(Boolean, default=False)
    last_review = Column(DateTime)
    next_review = Column(DateTime)
    repetition_count = Column(Integer, default=0)

    # Связи
    user = relationship("User", back_populates="user_words")
    phrase = relationship("Phrase", back_populates="user_words")

    def __repr__(self):
        return f"UserWord(user_id={self.user_id}, phrase_id={self.phrase_id})"


class UserProgress(Base):
    __tablename__ = 'user_progress'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    lesson_id = Column(Integer, ForeignKey('lessons.id'), nullable=False)

    # Прогресс по уроку
    is_completed = Column(Boolean, default=False)
    completion_date = Column(DateTime)
    score = Column(Integer, default=0)
    repetition_count = Column(Integer, default=0)

    # Связи
    user = relationship("User", back_populates="progress")
    lesson = relationship("Lesson", back_populates="progress")

    def __repr__(self):
        return f"UserProgress(user_id={self.user_id}, lesson_id={self.lesson_id})"