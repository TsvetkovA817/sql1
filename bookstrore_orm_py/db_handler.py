from datetime import datetime, timezone
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy import inspect
import sys
from models import Base, Publisher, Book, Shop, Stock, Sale



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
        из модуля models.py (Publisher, Book, Shop, Stock)
        """
        if not self.is_connected():
            print("Ошибка: Нет подключения к БД!")
            return False
        try:
            # Создаем все таблицы, определенные в Base.metadata
            Base.metadata.create_all(self.engine)
            # Проверяем, что таблицы действительно созданы
            inspector = inspect(self.engine)
            required_tables = {'publishers', 'books', 'shops', 'stocks'}
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
            #required_tables = ['publishers', 'books', 'shops', 'stocks']
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
    def __init__(self, db_session):
        self.session = db_session.session

    # Общие методы для всех сущностей
    def read_entities(self, entity_class, **filters):
        query = self.session.query(entity_class)
        for key, value in filters.items():
            if hasattr(entity_class, key):
                if isinstance(value, str):
                    query = query.filter(getattr(entity_class, key).ilike(f'%{value}%'))
                else:
                    query = query.filter(getattr(entity_class, key) == value)
        return query.all()

    def create_entity(self, entity_class, **data):
        entity = entity_class(**data)
        self.session.add(entity)
        self.session.commit()
        return entity

    def update_entity(self, entity_class, entity_id, **data):
        entity = self.session.query(entity_class).get(entity_id)
        if entity:
            for key, value in data.items():
                setattr(entity, key, value)
            self.session.commit()
            return True
        return False

    def delete_entity(self, entity_class, entity_id):
        entity = self.session.query(entity_class).get(entity_id)
        if entity:
            self.session.delete(entity)
            self.session.commit()
            return True
        return False

    # Специфичные методы для каждой сущности
    # CRUD для Publisher
    def create_publisher(self, name):
        publisher = Publisher(name=name)
        self.session.add(publisher)
        self.session.commit()
        return publisher

    def create_publisher2(self, name):
        return self.create_entity(Publisher, name=name)

    def read_publishers_all(self):
        return self.session.query(Publisher).all()

    def read_publishers(self, **filters):
        query = self.session.query(Publisher)
        for key, value in filters.items():
            if hasattr(Publisher, key):
                if key == 'name':
                    query = query.filter(getattr(Publisher, key).ilike(f'%{value}%'))
                else:
                    query = query.filter(getattr(Publisher, key) == value)
        return query.all()

    def read_publishers2(self, **filters):
        return self.read_entities(Publisher, **filters)

    def update_publisher(self, publisher_id, new_name):
        publisher = self.session.query(Publisher).get(publisher_id)
        if publisher:
            publisher.name = new_name
            self.session.commit()
            return True
        return False

    def delete_publisher(self, publisher_id):
        publisher = self.session.query(Publisher).get(publisher_id)
        if publisher:
            self.session.delete(publisher)
            self.session.commit()
            return True
        return False

    # CRUD для Book
    def create_book(self, title, publisher_id):
        book = Book(title=title, id_publisher=publisher_id)
        self.session.add(book)
        self.session.commit()
        return book

    def get_book_by_id(self, book_id):
        """Получает книгу по ID"""
        return self.session.query(Book).get(book_id)

    def read_books_all(self):
        return self.session.query(Book).all()

    def read_booksby_publisher(self, publisher_id=None):
        query = self.session.query(Book)
        if publisher_id:
            query = query.filter_by(id_publisher=publisher_id)
        return query.all()

    def read_books(self, **filters):
        """
        Возвращает список книг с возможностью фильтрации
        Поддерживаемые фильтры:
        - id: точный поиск по ID
        - title: поиск по части названия (регистронезависимый)
        - publisher_id: точный поиск по ID издателя
        """
        query = self.session.query(Book)

        if 'id' in filters:
            query = query.filter(Book.id == filters['id'])

        if 'title' in filters:
            query = query.filter(Book.title.ilike(f'%{filters["title"]}%'))

        if 'publisher_id' in filters:
            query = query.filter(Book.publisher_id == filters['publisher_id'])

        return query.all()


    def update_book(self, book_id, new_title=None, new_publisher_id=None):
        book = self.session.query(Book).get(book_id)
        if book:
            if new_title is not None:
                book.title = new_title
            if new_publisher_id is not None:
                book.id_publisher = new_publisher_id
            self.session.commit()
            return True
        return False

    def delete_book(self, book_id):
        book = self.session.query(Book).get(book_id)
        if book:
            self.session.delete(book)
            self.session.commit()
            return True
        return False

    # CRUD для Shop
    def get_shop_by_id(self, shop_id):
        return self.session.query(Shop).get(shop_id)

    def create_shop(self, name):
        shop = Shop(name=name)
        self.session.add(shop)
        self.session.commit()
        return shop

    def read_shops_all(self):
        """Возвращает список всех магазинов"""
        return self.session.query(Shop).all()


    def read_shops(self, **filters):
        query = self.session.query(Shop)
        for key, value in filters.items():
            if hasattr(Shop, key):
                if key == 'name':
                    query = query.filter(getattr(Shop, key).ilike(f'%{value}%'))
                else:
                    query = query.filter(getattr(Shop, key) == value)
        return query.all()

    def update_shop(self, shop_id, new_name):
        shop = self.session.query(Shop).get(shop_id)
        if shop:
            shop.name = new_name
            self.session.commit()
            return True
        return False

    def delete_shop(self, shop_id):
        shop = self.session.query(Shop).get(shop_id)
        if shop:
            self.session.delete(shop)
            self.session.commit()
            return True
        return False

    # Работа со связями (Stock)
    def get_stock(self, book_id, shop_id):
        return (self.session.query(Stock)
                .filter_by(id_book=book_id, id_shop=shop_id)
                .first())

    def add_book_to_shop(self, book_id, shop_id, count=1):
        stock = Stock(id_book=book_id, id_shop=shop_id, count=count)
        self.session.add(stock)
        self.session.commit()
        return stock

    def remove_book_from_shop(self, book_id, shop_id):
        stock = self.session.query(Stock).filter_by(
            id_book=book_id,
            id_shop=shop_id
        ).first()
        if stock:
            self.session.delete(stock)
            self.session.commit()
            return True
        return False

    def read_stock_by_shop(self, shop_id):
        """Возвращает сток книг для указанного магазина"""
        return self.session.query(Stock).filter_by(id_shop=shop_id).join(Book).all()

    def update_book_count_in_shop(self, book_id, shop_id, new_count):
        """Обновляет количество книг в стоке магазина"""
        stock = self.get_stock(book_id, shop_id)
        if stock:
            stock.count = new_count
            self.session.commit()
            return True
        return False

    def update_book_count_in_shop2(self, book_id, shop_id, new_count):
        stock = self.session.query(Stock).filter_by(
            id_book=book_id,
            id_shop=shop_id
        ).first()
        if stock:
            stock.count = new_count
            self.session.commit()
            return True
        return False


    # Специальные запросы
    def get_books_by_publisher(self, publisher_id_or_name):
        """Получает все книги указанного издателя (по ID или имени)"""
        query = self.session.query(Book).join(Publisher)

        if isinstance(publisher_id_or_name, int):
            query = query.filter(Publisher.id == publisher_id_or_name)
        else:
            query = query.filter(Publisher.name.ilike(f"%{publisher_id_or_name}%"))

        return query.all()

    def get_shops_with_publisher_books(self, publisher_id_or_name):
        """Получает магазины, где есть книги указанного издателя"""
        query = self.session.query(Shop).join(Stock).join(Book).join(Publisher)

        if isinstance(publisher_id_or_name, int):
            query = query.filter(Publisher.id == publisher_id_or_name)
        else:
            query = query.filter(Publisher.name.ilike(f"%{publisher_id_or_name}%"))

        return query.distinct().all()

    # CRUD для продаж
    def get_shop_by_id(self, shop_id):
        """Получает магазин по ID"""
        return self.session.query(Shop).get(shop_id)

    def get_stock(self, book_id, shop_id):
        """Получает сток по ID книги и магазина"""
        return (self.session.query(Stock)
                .filter_by(id_book=book_id, id_shop=shop_id)
                .first())


    def create_sale(self, stock_id, price, quantity=1, sale_date=None):
        """Регистрирует продажу книги"""
        sale = Sale(
            id_stock=stock_id,
            price=price,
            quantity=quantity,
            #sale_date=sale_date or datetime.utcnow()
            sale_date=sale_date or datetime.now(timezone.utc)
        )
        self.session.add(sale)

        # Обновляем количество книг в наличии
        stock = self.session.query(Stock).get(stock_id)
        if stock:
            stock.count -= quantity
            if stock.count < 0:
                raise ValueError("Недостаточно книг в наличии")

        self.session.commit()
        return sale

    def read_sales(self, shop_id=None, book_id=None, publisher_id=None, start_date=None, end_date=None):
        """Получает список продаж с возможностью фильтрации"""
        query = self.session.query(Sale).join(Stock).join(Book)

        if shop_id:
            query = query.filter(Stock.id_shop == shop_id)
        if book_id:
            query = query.filter(Stock.id_book == book_id)
        if publisher_id:
            query = query.join(Publisher).filter(Publisher.id == publisher_id)
        if start_date:
            query = query.filter(Sale.sale_date >= start_date)
        if end_date:
            query = query.filter(Sale.sale_date <= end_date)

        return query.order_by(Sale.sale_date.desc()).all()

    def update_sale(self, sale_id, new_price=None, new_quantity=None):
        """Обновляет данные о продаже"""
        sale = self.session.query(Sale).get(sale_id)
        if not sale:
            return False

        # Рассчитываем разницу в количестве для корректировки запасов
        quantity_diff = 0
        if new_quantity is not None and new_quantity != sale.quantity:
            quantity_diff = sale.quantity - new_quantity

        if new_price is not None:
            sale.price = new_price
        if new_quantity is not None:
            sale.quantity = new_quantity

        # Корректируем количество в запасах
        if quantity_diff != 0:
            stock = sale.stock
            stock.count += quantity_diff
            if stock.count < 0:
                raise ValueError("Недостаточно книг в наличии")

        self.session.commit()
        return True

    def delete_sale(self, sale_id):
        """Отменяет продажу и возвращает книги в запас"""
        sale = self.session.query(Sale).get(sale_id)
        if not sale:
            return False

        # Возвращаем книги в запас
        stock = sale.stock
        stock.count += sale.quantity

        self.session.delete(sale)
        self.session.commit()
        return True

    # Дополнительные методы для аналитики
    def get_total_sales(self, **filters):
        """Возвращает общую сумму продаж по фильтрам"""
        sales = self.read_sales(**filters)
        return sum(sale.price * sale.quantity for sale in sales)

    def get_books_sold_count(self, **filters):
        """Возвращает количество проданных книг по фильтрам"""
        sales = self.read_sales(**filters)
        return sum(sale.quantity for sale in sales)

    def get_top_selling_books(self, limit=5, **filters):
        """Возвращает самые продаваемые книги"""
        query = self.session.query(
            Book.title,
            Publisher.name.label('publisher'),
            func.sum(Sale.quantity).label('total_sold'),
            func.sum(Sale.price * Sale.quantity).label('total_revenue')
        ).join(Stock, Stock.id_book == Book.id) \
            .join(Sale, Sale.id_stock == Stock.id) \
            .join(Publisher, Publisher.id == Book.id_publisher)

        if 'shop_id' in filters:
            query = query.filter(Stock.id_shop == filters['shop_id'])
        if 'publisher_id' in filters:
            query = query.filter(Book.id_publisher == filters['publisher_id'])
        if 'start_date' in filters:
            query = query.filter(Sale.sale_date >= filters['start_date'])
        if 'end_date' in filters:
            query = query.filter(Sale.sale_date <= filters['end_date'])

        return query.group_by(Book.title, Publisher.name) \
            .order_by(func.sum(Sale.quantity).desc()) \
            .limit(limit) \
            .all()


if __name__ == '__main__':
    # тест
    db = DBSession(dbname="postgre4s", host="127.0.0.1", user="postgres", password="****", port=5432)
    print(db)
    crud = CRUDOperations(db)