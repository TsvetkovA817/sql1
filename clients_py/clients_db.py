import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

class ClientsDb:
    def __init__(self, dbname="postgres", host="127.0.0.1", user="postgres", password="pass", port=5432):
        self._dbname=dbname
        self._host = host
        self._user = user
        self._password = password
        self._port = port
        self.conn = None
        self.cursor = None
        self._connect()

    def _connect(self):
        """Устанавливает соединение с базой данных"""
        try:
            self.conn = psycopg2.connect(
                dbname=self._dbname,
                host=self._host,
                user=self._user,
                password=self._password,
                port=self._port
            )
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
            print(f"Успешное подключение к базе {self._dbname}")
        except psycopg2.Error as e:
            print(f"Ошибка подключения к базе данных: {e}")
            raise

    def __del__(self):
        """Закрывает соединение при удалении объекта"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def create_db(self, create_dbname="db2"):
        """Создает новую базу данных и таблицы"""
        try:
            # Создаем базу данных
            self.cursor.execute(
                sql.SQL("CREATE DATABASE {} WITH OWNER = postgres ENCODING = 'UTF8' CONNECTION LIMIT = -1;")
                    .format(sql.Identifier(create_dbname))
            )

            # Закрываем текущее соединение
            self.cursor.close()
            self.conn.close()

            # Подключаемся к новой базе данных
            self._dbname = create_dbname
            self._connect()

            # Создаем таблицы
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    id SERIAL PRIMARY KEY, 
                    name VARCHAR(50) NOT NULL, 
                    second_name VARCHAR(50) NOT NULL, 
                    email VARCHAR(70) UNIQUE NOT NULL
                );
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tel (
                    id SERIAL PRIMARY KEY, 
                    ntel VARCHAR(50) NOT NULL, 
                    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE
                );
            ''')

            print(f"База данных {create_dbname} успешно создана")
            return True
        except psycopg2.Error as e:
            print(f"Ошибка при создании базы данных: {e}")
            return False

    def drop_db(self, dbname):
        """Удаляет указанную базу данных"""
        try:
            # Подключаемся к postgres, чтобы удалить другую базу
            temp_conn = psycopg2.connect(
                dbname="postgres",
                host=self._host,
                user=self._user,
                password=self._password,
                port=self._port
            )
            temp_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            temp_cursor = temp_conn.cursor()

            # Завершаем все соединения с удаляемой БД
            temp_cursor.execute(
                sql.SQL("SELECT pg_terminate_backend(pg_stat_activity.pid) "
                        "FROM pg_stat_activity "
                        "WHERE pg_stat_activity.datname = %s "
                        "AND pid <> pg_backend_pid();"),
                [dbname]
            )

            # Удаляем базу данных
            temp_cursor.execute(
                sql.SQL("DROP DATABASE IF EXISTS {};")
                    .format(sql.Identifier(dbname))
            )

            temp_cursor.close()
            temp_conn.close()

            print(f"База данных {dbname} успешно удалена")
            return True
        except psycopg2.Error as e:
            print(f"Ошибка при удалении базы данных: {e}")
            return False

    def add_client_record(self, name, second_name, email, phones):
        """Добавляет запись о клиенте и его телефонах в БД
        Args:
            name (str): Имя клиента
            second_name (str): Фамилия клиента
            email (str): Email клиента
            phones (list): Список телефонов клиента
        Returns:
            int: ID добавленного клиента или None в случае ошибки
        """
        try:
            # Начинаем транзакцию
            self.conn.autocommit = False

            # Добавляем клиента
            self.cursor.execute(
                "INSERT INTO clients (name, second_name, email) VALUES (%s, %s, %s) RETURNING id;",
                (name, second_name, email))
            client_id = self.cursor.fetchone()[0]

            # Добавляем телефоны
            for phone in phones:
                self.cursor.execute("INSERT INTO tel (ntel, client_id) VALUES (%s, %s);", (phone, client_id))

            # Фиксируем транзакцию
            self.conn.commit()
            return client_id

        except psycopg2.Error as e:
            # Откатываем транзакцию в случае ошибки
            self.conn.rollback()
            print(f"Ошибка при добавлении клиента: {e}")
            return None
        finally:
            self.conn.autocommit = True

    def update_client_record(self, client_id, name, second_name, email, phones):
        """Обновляет данные клиента и его телефоны в БД
        Args:
            client_id (int): ID клиента
            name (str): Новое имя
            second_name (str): Новая фамилия
            email (str): Новый email
            phones (list): Список новых телефонов
        Returns:
            bool: True если успешно, False в случае ошибки
        """
        try:
            # Начинаем транзакцию
            self.conn.autocommit = False

            # Обновляем данные клиента
            self.cursor.execute(
                "UPDATE clients SET name = %s, second_name = %s, email = %s WHERE id = %s;",
                (name, second_name, email, client_id))

            # Удаляем старые телефоны
            self.cursor.execute(
                "DELETE FROM tel WHERE client_id = %s;",
                (client_id,))

            # Добавляем новые телефоны
            for phone in phones:
                self.cursor.execute(
                    "INSERT INTO tel (ntel, client_id) VALUES (%s, %s);",
                    (phone, client_id))

            # Фиксируем транзакцию
            self.conn.commit()
            return True

        except psycopg2.Error as e:
            # Откатываем транзакцию в случае ошибки
            self.conn.rollback()
            print(f"Ошибка при обновлении клиента: {e}")
            return False
        finally:
            self.conn.autocommit = True

    def get_client_phones(self, client_id):
        """Возвращает список телефонов клиента"""
        try:
            self.cursor.execute(
                "SELECT ntel FROM tel WHERE client_id = %s;",
                (client_id,))
            return [phone[0] for phone in self.cursor.fetchall()]
        except psycopg2.Error as e:
            print(f"Ошибка при получении телефонов клиента: {e}")
            return []


    def delete_client_record(self, client_id):
        """Удаляет клиента и все его телефоны из БД
        Args:
            client_id (int): ID клиента для удаления
        Returns:
            bool: True если успешно, False в случае ошибки
        """
        try:
            # Начинаем транзакцию
            self.conn.autocommit = False

            # Удаляем телефоны клиента ON DELETE CASCADE - автоматически
            # явное удаление
            self.cursor.execute("DELETE FROM tel WHERE client_id = %s;",  (client_id,))

            # Удаляем самого клиента
            self.cursor.execute("DELETE FROM clients WHERE id = %s;", (client_id,))

            # Проверяем, была ли удалена хотя бы одна запись
            if self.cursor.rowcount == 0:
                self.conn.rollback()
                return False

            # Фиксируем транзакцию
            self.conn.commit()
            return True

        except psycopg2.Error as e:
            # Откатываем транзакцию в случае ошибки
            self.conn.rollback()
            print(f"Ошибка при удалении клиента: {e}")
            return False
        finally:
            self.conn.autocommit = True

    def search_clients(self, name="", second_name="", email="", phone=""):
        """Поиск клиентов по заданным критериям
        Args:
            name (str): Часть имени (регистронезависимо)
            second_name (str): Часть фамилии (регистронезависимо)
            email (str): Часть email (регистронезависимо)
            phone (str): Часть телефона
        Returns:
            list: Список словарей с данными клиентов и их телефонами
        """
        try:
            # Основной запрос для поиска клиентов
            query = """
                SELECT c.id, c.name, c.second_name, c.email 
                FROM clients c
                WHERE (%(name)s = '' OR c.name ILIKE %(name_pattern)s)
                  AND (%(second_name)s = '' OR c.second_name ILIKE %(second_name_pattern)s)
                  AND (%(email)s = '' OR c.email ILIKE %(email_pattern)s)
                  AND (%(phone)s = '' OR EXISTS (
                      SELECT 1 FROM tel t 
                      WHERE t.client_id = c.id AND t.ntel LIKE %(phone_pattern)s
                  ))
                ORDER BY c.id;
            """

            params = {
                'name': name,
                'name_pattern': f"%{name}%",
                'second_name': second_name,
                'second_name_pattern': f"%{second_name}%",
                'email': email,
                'email_pattern': f"%{email}%",
                'phone': phone,
                'phone_pattern': f"%{phone}%"
            }

            self.cursor.execute(query, params)
            clients = self.cursor.fetchall()

            # Для каждого клиента получаем его телефоны
            result = []
            for client in clients:
                client_id = client[0]
                self.cursor.execute(
                    "SELECT ntel FROM tel WHERE client_id = %s;", (client_id,))
                phones = self.cursor.fetchall()

                result.append({
                    'id': client_id,
                    'name': client[1],
                    'second_name': client[2],
                    'email': client[3],
                    'phones': phones
                })

            return result

        except psycopg2.Error as e:
            print(f"Ошибка при поиске клиентов: {e}")
            return []
