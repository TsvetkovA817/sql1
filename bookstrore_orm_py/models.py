# Book.shops через вторичную таблицу stocks
# Book.stocks прямое отношение
# Shop.books через вторичную таблицу stocks
# Stock.book прямое отношение
# Прямые отношения (stocks) используются для записи и управления связями
# Отношения через secondary таблицу (shops/books) используются только для чтения (viewonly=True)
# Параметр overlaps явно указывает SQLAlchemy, какие отношения пересекаются
# можно упростить модели, оставив только один способ (например, только через secondary таблицу или только через прямые отношения)

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone

Base = declarative_base()


class Publisher(Base):
    __tablename__ = 'publishers'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    books = relationship("Book", back_populates="publisher")  #+

    def __repr__(self):
        return f"Publisher(id={self.id}, name='{self.name}')"


class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    id_publisher = Column(Integer, ForeignKey('publishers.id'), nullable=False)
    #author = Column(String(100))  # Добавляем поле автор

    publisher = relationship("Publisher", back_populates="books")  #+
    stocks = relationship("Stock", back_populates="book", overlaps="shops")
    # Отношение к магазинам через stocks
    shops = relationship("Shop", secondary="stocks", back_populates="books",
        viewonly=True  # отношение только для чтения
    )
    #1 shops = relationship("Shop", secondary='stocks', back_populates="books") #+
    #-shops = relationship("Shop", back_populates="books")  #?
    #1 stocks = relationship("Stock", back_populates="book")
    def __repr__(self):
        return f"Book(id={self.id}, title='{self.title}', publisher_id={self.id_publisher})"


class Shop(Base):
    __tablename__ = 'shops'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    stocks = relationship("Stock", back_populates="shop")
    # Отношение к книгам через stocks
    books = relationship(
        "Book",
        secondary="stocks",
        back_populates="shops",
        viewonly=True  # Это отношение только для чтения
    )

    #1 books = relationship("Book", secondary='stocks', back_populates="shops") #+
    #+books = relationship("Book", secondary='stocks', back_populates="shops")
    #-  books = relationship("Book", back_populates="shops") #
    #+stocks = relationship("Stock", back_populates="shop")  # Добавлено отношение к Stock

    def __repr__(self):
        return f"Shop(id={self.id}, name='{self.name}')"

# наличие конкретной книги в конкретном магазине
class Stock(Base):
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True)
    id_book = Column(Integer, ForeignKey('books.id'), nullable=False)
    id_shop = Column(Integer, ForeignKey('shops.id'), nullable=False)
    count = Column(Integer, default=0) # Остаток
    #location = Column(String(20))  # Склад Витрина
    book = relationship("Book", back_populates="stocks", overlaps="shops")
    shop = relationship("Shop", back_populates="stocks")
    sales = relationship("Sale", back_populates="stock")

    # Устанавливаем отношения с явным указанием back_populates
    #1 book = relationship("Book", back_populates="stocks")
    #+shop = relationship("Shop", back_populates="stocks")
    #+sales = relationship("Sale", back_populates="stock")


class Sale(Base):
    __tablename__ = 'sales'

    id = Column(Integer, primary_key=True)
    id_stock = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    #sale_date = Column(DateTime, default=datetime.utcnow)
    sale_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    stock = relationship("Stock", back_populates="sales")
