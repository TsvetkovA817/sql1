# Clients
# DROP DATABASE [ IF EXISTS ] имя
#import psycopg2
#from psycopg2 import sql
#from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from config_handler import ConfigHandler
from language_handler import LanguageHandler
from clients_db import ClientsDb

class MainApplication:

    def __init__(self, root):
        # Инициализация конфига
        self.config = ConfigHandler()
        self.db_config = self.config.get_db_config()

        # Инициализация подключения к БД
        self.db_connection = None
        self.db = None

        self.root = root
        self.lang = LanguageHandler()
        # Инициализация интерфейса с текущим языком
        x = (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2
        y = (root.winfo_screenheight() - root.winfo_reqheight()) // 2
        w = 600
        h = 400
        self.root.geometry(f"{w}x{h}+{x-w//2}+{y-h//2}")
        self._connect_to_db(self.db_config)
        self._init_ui()



    def _connect_to_db(self, db_config):
        """Подключиться к БД с указанными параметрами"""
        try:
            self.db = ClientsDb(**db_config)
            self.db_connection = self.db.conn
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"Подключено к БД: {db_config['dbname']}", fg="green")
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.config(text="Не подключено к БД", fg="red")
            return False

    def _init_ui(self):
        """Инициализирует интерфейс с текущим языком . обновляет весь интерфейс"""
        # Очищаем предыдущие виджеты (кроме меню)
        for widget in self.root.winfo_children():
            if not isinstance(widget, tk.Menu):
                widget.destroy()
        print(self.lang.current_lang)
        self.root.title(self.lang.get_text("app_title")+" / TsvetkovAV v.1")

        # Создаем главное меню
        #self.menu_bar = tk.Menu(self.root)
        self.root.geometry("800x600")

        # Основное содержимое окна
        self._create_main_content()

        # Создаем главное меню
        self._create_menu()

        # Статус подключения
        self._create_status_bar()

    def _create_main_content(self):
        """Создает основное содержимое окна"""
        # Основной фрейм для центрирования содержимого
        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Приветственная надпись
        self.label1 = tk.Label(
            main_frame,
            text=self.lang.get_text("welcome_message"),
            font=('Arial', 14)
        )
        self.label1.pack(pady=(50, 10))

        # Описание приложения
        self.label2 = tk.Label(
            main_frame,
            text=self.lang.get_text("app_description"),
            font=('Arial', 14)
        )
        self.label2.pack(pady=10)

        # Доп информация
        self.label3 = tk.Label(
            main_frame,
            text=self.lang.get_text("current_db_status").format(
                dbname=self.db._dbname if self.db else "N/A"
            ),
            font=('Arial', 12),
            fg="gray"
        )
        self.label3.pack(pady=20)

    def _create_menu(self):
        """Создает главное меню"""
        self.menu_bar = tk.Menu(self.root)
        # Меню Файл
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label=self.lang.get_text("menu_file_create"), command = self.create_file)
        self.file_menu.add_command(label = self.lang.get_text("menu_file_open"), command = self.open_file)
        self.file_menu.add_command(label = self.lang.get_text("menu_file_delete"), command = self.del_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label = self.lang.get_text("menu_file_exit"), command = self.exit_app)

        self.data_menu = tk.Menu(self.menu_bar, tearoff=0)   # Меню "Данные"
        self.data_menu.add_command(label = self.lang.get_text("menu_data_clients"), command = self.show_clients)
        self.data_menu.add_command(label=self.lang.get_text("menu_data_add"), command=self.add_client)
        self.data_menu.add_command(label=self.lang.get_text("menu_data_edit"), command=self.edit_client)
        self.data_menu.add_command(label=self.lang.get_text("menu_data_delete"), command=self.delete_client)
        self.data_menu.add_command(label=self.lang.get_text("menu_data_search"), command=self.search_client)

        self.help_menu = tk.Menu(self.menu_bar, tearoff =0)
        self.help_menu.add_command(label = self.lang.get_text("menu_help_about"), command = self.about_prog)


        # Меню Настройки с подменю Язык
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.settings_menu.add_command(label=self.lang.get_text("menu_settings_param"), command=self.show_settings)
        # Подменю выбора языка
        self.lang_menu = tk.Menu(self.settings_menu, tearoff=0)
        for lang_code in self.lang.get_supported_languages():
            self.lang_menu.add_command(
                label=self.lang.get_text(f"lang_{lang_code}"),
                command=lambda lc=lang_code: self.change_language(lc)
            )

        self.settings_menu.add_cascade(
            label=self.lang.get_text("menu_language"),
            menu=self.lang_menu
        )

        self.menu_bar.add_cascade(label = self.lang.get_text("menu_file"), menu = self.file_menu)
        self.menu_bar.add_cascade(label=self.lang.get_text("menu_data"), menu=self.data_menu)
        self.menu_bar.add_cascade(label=self.lang.get_text("menu_settings"), menu=self.settings_menu)
        self.menu_bar.add_cascade(label = self.lang.get_text("menu_help"), menu = self.help_menu)

        self.root.config(menu = self.menu_bar)

        # self.label1 = tk.Label(root, text="Hello world", font=('Arial', 14))
        # self.label1.pack(pady=50)
        # self.label2 = tk.Label(root, text="PostgreSQL", font=('Arial', 14))
        # self.label2.pack(pady=50)

        # Статус подключения
        self.status_label = tk.Label(self.root, text=self.lang.get_text("status_disconnected"), fg="red")
        self.status_label.pack()

    def _create_status_bar(self):
        """Создает строку статуса"""
        status_text = ""
        if self.db and self.db_connection:
            status_text = self.lang.get_text("status_connected").format(
                dbname=self.db._dbname
            )
            fg_color = "green"
        else:
            status_text = self.lang.get_text("status_disconnected")
            fg_color = "red"

        if hasattr(self, 'status_label'):
            self.status_label.config(text=status_text, fg=fg_color)
        else:
            self.status_label = tk.Label(
                self.root,
                text=status_text,
                fg=fg_color,
                bd=1,
                relief=tk.SUNKEN,
                anchor=tk.W
            )
            self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def change_language(self, lang_code):
        """Меняет язык интерфейса"""
        self.lang.set_language(lang_code)

        # Закрываем все дочерние окна
        for child in self.root.winfo_children():
            if isinstance(child, tk.Toplevel):
                child.destroy()

        # Переинициализируем интерфейс
        self._init_ui()

        # # Обновляем статус подключения
        # if self.db_connection:
        #     dbname = self.db._dbname
        #     self.status_label.config(
        #         text=self.lang.get_text("status_connected").format(dbname=dbname),
        #         fg="green"
        #     )

    def create_file(self):
        """Создание новой базы данных с использованием класса ClientsDb"""
        db_name = simpledialog.askstring("Создание БД", "Введите имя новой базы данных:")
        if db_name:
            try:
                # Создаем временное подключение для создания БД
                temp_db = ClientsDb()

                # Создаем новую БД и таблицы
                if temp_db.create_db(db_name):
                    messagebox.showinfo("Успех", f"База данных {db_name} успешно создана!")

                    # Подключаемся к новой БД
                    self.db = ClientsDb(dbname=db_name)
                    self.db_connection = self.db.conn
                    self.status_label.config(text=f"Подключено к БД: {db_name}", fg="green")
                else:
                    messagebox.showerror("Ошибка", "Не удалось создать базу данных")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать базу данных:\n{e}")
            finally:
                # Закрываем временное подключение
                if 'temp_db' in locals():
                    del temp_db

    def open_file(self):
        """Подключение к существующей базе данных"""
        db_name = simpledialog.askstring("Открытие БД", "Введите имя базы данных для подключения:")
        if db_name:
            try:
                # Закрываем предыдущее подключение, если оно есть
                if self.db:
                    del self.db

                # Создаем новое подключение
                self.db = ClientsDb(dbname=db_name)
                self.db_connection = self.db.conn

                # Проверяем существование таблиц
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name='clients');")
                if not cursor.fetchone()[0]:
                    messagebox.showwarning("Предупреждение", "В базе данных отсутствуют необходимые таблицы!")

                messagebox.showinfo("Успех", f"Успешное подключение к базе данных {db_name}!")
                self.status_label.config(text=f"Подключено к БД: {db_name}", fg="green")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось подключиться к базе данных:\n{e}")
                self.db = None
                self.status_label.config(text="Не подключено к БД", fg="red")

    def del_file(self):
        """Удаление базы данных"""
        db_name = simpledialog.askstring("Удаление БД", "Введите имя базы данных для удаления:")
        if db_name:
            if messagebox.askyesno("Подтверждение",
                                   f"Вы уверены, что хотите удалить базу данных {db_name}?\nЭто действие нельзя отменить!"):
                try:
                    # Создаем временное подключение для удаления БД
                    temp_db = ClientsDb()

                    if temp_db.drop_db(db_name):
                        messagebox.showinfo("Успех", f"База данных {db_name} успешно удалена!")

                        # Если удаляли текущую БД, обновляем статус
                        if self.db and self.db._dbname == db_name:
                            del self.db
                            self.db = None
                            self.db_connection = None
                            self.status_label.config(text="Не подключено к БД", fg="red")
                    else:
                        messagebox.showerror("Ошибка", "Не удалось удалить базу данных")

                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось удалить базу данных:\n{e}")
                finally:
                    if 'temp_db' in locals():
                        del temp_db

    def exit_app(self):
        """Выход из приложения"""
        # askokcancel - кнопки не lang, изменить
        if messagebox.askokcancel(self.lang.get_text("menu_file_exit"), self.lang.get_text("confirm_exit")):
            if self.db:
                del self.db  # Вызовет __del__ и закроет соединение
            self.root.destroy()

    def show_clients(self):
        """Все клиенты"""
        if not self.db or not self.db_connection:
            messagebox.showwarning("Предупреждение", "Сначала подключитесь к базе данных!")
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT id, name, second_name, email FROM clients;")
            clients = cursor.fetchall()

            # Создаем окно для отображения клиентов
            clients_window = tk.Toplevel(self.root)
            clients_window.title("Список клиентов")

            parent_x = self.root.winfo_x()
            parent_y = self.root.winfo_y()
            clients_window.geometry("500x300")
            clients_window.geometry(f"+{parent_x + 50}+{parent_y + 50}")

            # Создаем текстовое поле с прокруткой
            text_frame = tk.Frame(clients_window)
            text_frame.pack(fill=tk.BOTH, expand=True)

            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            text_area = tk.Text(text_frame, yscrollcommand=scrollbar.set)
            text_area.pack(fill=tk.BOTH, expand=True)
            scrollbar.config(command=text_area.yview)

            # Добавляем данные в текстовое поле
            if clients:
                w1, w2, w3, w4 =4, 10, 10, 30
                c1 = self._set_len('ID', w1, ' ')
                c2 = self._set_len('Имя', w2, ' ')
                c3 = self._set_len('Фамилия', w3, ' ')
                c4 = self._set_len('Email', w4, ' ')
                text_area.insert(tk.END, f"{c1} | {c2} | {c3} | {c4}\n")
                text_area.insert(tk.END, "-" * 50 + "\n")
                for client in clients:
                    c1 = self._set_len(client[0], w1,' ')
                    c2 = self._set_len(client[1], w2, ' ')
                    c3 = self._set_len(client[2], w3, ' ')
                    c4 = self._set_len(client[3], w4, ' ')
                    text_area.insert(tk.END, f"{c1} | {c2} | {c3} | {c4}\n")
            else:
                text_area.insert(tk.END, "В базе данных нет клиентов")

            text_area.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить список клиентов:\n{e}")

    def _set_len(self, s, max_length, padding_char):
        return (str(s) + padding_char * max_length)[:max_length]

    def about_prog(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("О программе")

        parent_x = self.root.winfo_x()  # Получаем X-координату главного окна
        parent_y = self.root.winfo_y()  # Получаем Y-координату главного окна
        about_window.geometry("300x200")
        about_window.geometry(f"+{parent_x + 50}+{parent_y + 50}")  # Смещение на 50 пикселей вправо и вниз

        tk.Label(about_window, text="Менеджер базы данных Клиенты\nВерсия 1.0 TsvetkovAV\n\nPostgreSQL Client\n© 2025",
                 font=('Arial', 12)).pack(pady=20)
        tk.Button(about_window, text="Закрыть",
                  command=about_window.destroy).pack(pady=10)


    def add_client(self):
        """Добавление клиента"""
        if not self.db or not self.db_connection:
            messagebox.showwarning("Предупреждение", "Сначала подключитесь к базе данных!")
            return

        # Создаем окно для ввода данных клиента

        client_window = tk.Toplevel(self.root)
        client_window.title("Добавить клиента")
        client_window.geometry("400x300")
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        client_window.geometry(f"+{parent_x + 50}+{parent_y + 50}")

        # Поля для ввода данных
        tk.Label(client_window, text="Имя:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        name_entry = tk.Entry(client_window)
        name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        tk.Label(client_window, text="Фамилия:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        second_name_entry = tk.Entry(client_window)
        second_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        tk.Label(client_window, text="Email:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        email_entry = tk.Entry(client_window)
        email_entry.grid(row=2, column=1, padx=5, pady=5, sticky="we")

        # Таблица для телефонов
        tk.Label(client_window, text="Телефоны:").grid(row=3, column=0, columnspan=2, pady=5)

        phone_frame = tk.Frame(client_window)
        phone_frame.grid(row=4, column=0, columnspan=2, padx=5, sticky="nsew")

        phone_tree = ttk.Treeview(phone_frame, columns=("number",), show="headings", height=4)
        phone_tree.heading("number", text="Номер телефона")
        phone_tree.column("number", width=250)
        phone_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(phone_frame, orient="vertical", command=phone_tree.yview)
        scrollbar.pack(side="right", fill="y")
        phone_tree.configure(yscrollcommand=scrollbar.set)

        # Кнопки управления телефонами
        phone_btn_frame = tk.Frame(client_window)
        phone_btn_frame.grid(row=5, column=0, columnspan=2, pady=5)

        def add_phone():
            phone = simpledialog.askstring("Добавить телефон", "Введите номер телефона:")
            if phone:
                phone_tree.insert("", "end", values=(phone,))

        def remove_phone():
            selected = phone_tree.selection()
            if selected:
                phone_tree.delete(selected)

        tk.Button(phone_btn_frame, text="Добавить телефон", command=add_phone).pack(side="left", padx=5)
        tk.Button(phone_btn_frame, text="Удалить телефон", command=remove_phone).pack(side="left", padx=5)

        # Кнопка сохранения
        def save_client():
            name = name_entry.get()
            second_name = second_name_entry.get()
            email = email_entry.get()
            phones = [phone_tree.item(item)["values"][0] for item in phone_tree.get_children()]

            if not name or not second_name or not email:
                messagebox.showwarning("Ошибка", "Заполните все обязательные поля!")
                return

            try:
                # Добавляем клиента через метод класса ClientsDb
                client_id = self.db.add_client_record(name, second_name, email, phones)
                if client_id:
                    messagebox.showinfo("Успех", f"Клиент успешно добавлен (ID: {client_id})")
                    client_window.destroy()
                else:
                    messagebox.showerror("Ошибка", "Не удалось добавить клиента")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить клиента:\n{e}")

        tk.Button(client_window, text="Сохранить", command=save_client).grid(row=6, column=0, columnspan=2, pady=10)

    def edit_client(self):
        """Редактирование существующего клиента"""
        if not self.db or not self.db_connection:
            messagebox.showwarning("Предупреждение", "Сначала подключитесь к базе данных!")
            return

        # Получаем список клиентов для выбора
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT id, name, second_name, email FROM clients ORDER BY id;")
            clients = cursor.fetchall()

            if not clients:
                messagebox.showinfo("Информация", "В базе нет клиентов для редактирования")
                return

            # Окно выбора клиента
            select_window = tk.Toplevel(self.root)
            select_window.title("Выберите клиента")
            select_window.geometry("600x400")
            parent_x = self.root.winfo_x()
            parent_y = self.root.winfo_y()
            select_window.geometry(f"+{parent_x + 50}+{parent_y + 50}")

            # Таблица с клиентами
            tree = ttk.Treeview(select_window, columns=("id", "name", "second_name", "email"), show="headings")
            tree.heading("id", text="ID")
            tree.heading("name", text="Имя")
            tree.heading("second_name", text="Фамилия")
            tree.heading("email", text="Email")
            tree.column("id", width=50)
            tree.column("name", width=150)
            tree.column("second_name", width=150)
            tree.column("email", width=200)

            for client in clients:
                tree.insert("", "end", values=client)

            tree.pack(fill="both", expand=True, padx=5, pady=5)

            def on_select():
                selected = tree.focus()
                if not selected:
                    return

                client_data = tree.item(selected)["values"]
                select_window.destroy()
                self._show_edit_client_dialog(client_data[0], client_data[1], client_data[2], client_data[3])

            tk.Button(select_window, text="Выбрать", command=on_select).pack(pady=5)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить список клиентов:\n{e}")


    def _show_edit_client_dialog(self, client_id, name, second_name, email):
        """Показывает диалоговое окно редактирования клиента"""
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Редактирование клиента ID: {client_id}")
        edit_window.geometry("450x400")

        # Поля для редактирования данных
        tk.Label(edit_window, text="Имя:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        name_entry = tk.Entry(edit_window)
        name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        name_entry.insert(0, name)

        tk.Label(edit_window, text="Фамилия:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        second_name_entry = tk.Entry(edit_window)
        second_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        second_name_entry.insert(0, second_name)

        tk.Label(edit_window, text="Email:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        email_entry = tk.Entry(edit_window)
        email_entry.grid(row=2, column=1, padx=5, pady=5, sticky="we")
        email_entry.insert(0, email)

        # Таблица телефонов
        tk.Label(edit_window, text="Телефоны:").grid(row=3, column=0, columnspan=2, pady=5)

        phone_frame = tk.Frame(edit_window)
        phone_frame.grid(row=4, column=0, columnspan=2, padx=5, sticky="nsew")

        phone_tree = ttk.Treeview(phone_frame, columns=("number",), show="headings", height=4)
        phone_tree.heading("number", text="Номер телефона")
        phone_tree.column("number", width=300)

        scrollbar = ttk.Scrollbar(phone_frame, orient="vertical", command=phone_tree.yview)
        scrollbar.pack(side="right", fill="y")
        phone_tree.configure(yscrollcommand=scrollbar.set)
        phone_tree.pack(side="left", fill="both", expand=True)

        # Загружаем текущие телефоны клиента
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT ntel FROM tel WHERE client_id = %s;", (client_id,))
            for phone in cursor.fetchall():
                phone_tree.insert("", "end", values=phone)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить телефоны клиента:\n{e}")

        # Кнопки управления телефонами
        phone_btn_frame = tk.Frame(edit_window)
        phone_btn_frame.grid(row=5, column=0, columnspan=2, pady=5)

        def add_phone():
            phone = simpledialog.askstring("Добавить телефон", "Введите номер телефона:")
            if phone:
                phone_tree.insert("", "end", values=(phone,))

        def remove_phone():
            selected = phone_tree.selection()
            if selected:
                phone_tree.delete(selected)

        tk.Button(phone_btn_frame, text="Добавить телефон", command=add_phone).pack(side="left", padx=5)
        tk.Button(phone_btn_frame, text="Удалить телефон", command=remove_phone).pack(side="left", padx=5)

        # Кнопки сохранения/отмены
        btn_frame = tk.Frame(edit_window)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)

        def save_changes():
            new_name = name_entry.get()
            new_second_name = second_name_entry.get()
            new_email = email_entry.get()
            new_phones = [phone_tree.item(item)["values"][0] for item in phone_tree.get_children()]

            if not new_name or not new_second_name or not new_email:
                messagebox.showwarning("Ошибка", "Заполните все обязательные поля!")
                return

            try:
                if self.db.update_client_record(client_id, new_name, new_second_name, new_email, new_phones):
                    messagebox.showinfo("Успех", "Данные клиента успешно обновлены")
                    edit_window.destroy()
                else:
                    messagebox.showerror("Ошибка", "Не удалось обновить данные клиента")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить данные клиента:\n{e}")

        tk.Button(btn_frame, text="Сохранить", command=save_changes).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Отмена", command=edit_window.destroy).pack(side="left", padx=10)


    def delete_client(self):
        """Удаление клиента из базы данных"""
        if not self.db or not self.db_connection:
            messagebox.showwarning("Предупреждение", "Сначала подключитесь к базе данных!")
            return

        # Получаем список клиентов для выбора
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT id, name, second_name, email FROM clients ORDER BY id;")
            clients = cursor.fetchall()

            if not clients:
                messagebox.showinfo("Информация", "В базе нет клиентов для удаления")
                return

            # Окно выбора клиента
            delete_window = tk.Toplevel(self.root)
            delete_window.title("Удаление клиента")
            delete_window.geometry("600x400")
            parent_x = self.root.winfo_x()
            parent_y = self.root.winfo_y()
            delete_window.geometry(f"+{parent_x + 50}+{parent_y + 50}")

            # Таблица с клиентами
            tree = ttk.Treeview(delete_window, columns=("id", "name", "second_name", "email"), show="headings")
            tree.heading("id", text="ID")
            tree.heading("name", text="Имя")
            tree.heading("second_name", text="Фамилия")
            tree.heading("email", text="Email")
            tree.column("id", width=50)
            tree.column("name", width=150)
            tree.column("second_name", width=150)
            tree.column("email", width=200)

            for client in clients:
                tree.insert("", "end", values=client)

            tree.pack(fill="both", expand=True, padx=5, pady=5)

            def on_delete():
                selected = tree.focus()
                if not selected:
                    return

                client_data = tree.item(selected)["values"]
                client_id = client_data[0]
                client_name = f"{client_data[1]} {client_data[2]}"

                # Подтверждение удаления
                if messagebox.askyesno(
                        "Подтверждение удаления",
                        f"Вы точно хотите удалить клиента {client_name} (ID: {client_id})?\n"
                        "Это действие нельзя отменить!"):

                    try:
                        if self.db.delete_client_record(client_id):
                            messagebox.showinfo("Успех", f"Клиент {client_name} успешно удалён")
                            delete_window.destroy()
                        else:
                            messagebox.showerror("Ошибка", "Не удалось удалить клиента")
                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Не удалось удалить клиента:\n{e}")

            tk.Button(delete_window, text="Удалить выбранного", command=on_delete).pack(pady=5)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить список клиентов:\n{e}")


    def search_client(self):
        """Поиск клиента с фильтрацией"""
        if not self.db or not self.db_connection:
            messagebox.showwarning("Предупреждение", "Сначала подключитесь к базе данных!")
            return

        # Создаем окно поиска
        search_window = tk.Toplevel(self.root)
        search_window.title("Поиск клиента")
        search_window.geometry("680x600")
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        search_window.geometry(f"+{parent_x + 50}+{parent_y + 50}")

        # Фрейм для фильтров
        filter_frame = tk.LabelFrame(search_window, text="Фильтры поиска", padx=5, pady=5)
        filter_frame.pack(fill="x", padx=5, pady=5)

        # Поля для фильтрации
        tk.Label(filter_frame, text="Имя:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        name_entry = tk.Entry(filter_frame)
        name_entry.grid(row=0, column=1, padx=5, pady=2, sticky="we")

        tk.Label(filter_frame, text="Фамилия:").grid(row=1, column=0, padx=5, pady=2, sticky="e")
        second_name_entry = tk.Entry(filter_frame)
        second_name_entry.grid(row=1, column=1, padx=5, pady=2, sticky="we")

        tk.Label(filter_frame, text="Email:").grid(row=2, column=0, padx=5, pady=2, sticky="e")
        email_entry = tk.Entry(filter_frame)
        email_entry.grid(row=2, column=1, padx=5, pady=2, sticky="we")

        tk.Label(filter_frame, text="Телефон:").grid(row=3, column=0, padx=5, pady=2, sticky="e")
        phone_entry = tk.Entry(filter_frame)
        phone_entry.grid(row=3, column=1, padx=5, pady=2, sticky="we")

        # Кнопка поиска
        def perform_search():
            filters = {
                'name': name_entry.get().strip(),
                'second_name': second_name_entry.get().strip(),
                'email': email_entry.get().strip(),
                'phone': phone_entry.get().strip()
            }
            self._show_search_results(search_window, filters)

        search_btn = tk.Button(filter_frame, text="Поиск", command=perform_search)
        search_btn.grid(row=4, column=0, columnspan=2, pady=5)

        # Таблица с результатами
        results_frame = tk.Frame(search_window)
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.search_tree = ttk.Treeview(results_frame, columns=("id", "name", "second_name", "email", "phones"),
                                        show="headings", height=15)

        # Настройка столбцов
        self.search_tree.heading("id", text="ID")
        self.search_tree.heading("name", text="Имя")
        self.search_tree.heading("second_name", text="Фамилия")
        self.search_tree.heading("email", text="Email")
        self.search_tree.heading("phones", text="Телефоны")

        self.search_tree.column("id", width=50, anchor="center")
        self.search_tree.column("name", width=120)
        self.search_tree.column("second_name", width=120)
        self.search_tree.column("email", width=150)
        self.search_tree.column("phones", width=200)

        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.search_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.search_tree.configure(yscrollcommand=scrollbar.set)
        self.search_tree.pack(fill="both", expand=True)

        # Фрейм для кнопок под таблицей
        button_frame = tk.Frame(search_window)
        button_frame.pack(pady=10)

        # Кнопка "Добавить запись"
        add_btn = tk.Button(
            button_frame,
            text="Добавить запись",
            #command=lambda: [search_window.destroy(), self.add_client()],
            command=lambda: [self.add_client(), perform_search()],
            width=15
        )
        add_btn.pack(side="left", padx=10)

        # Кнопка "Удалить"
        def delete_selected():
            selected = self.search_tree.focus()
            if not selected:
                messagebox.showwarning("Предупреждение", "Выберите клиента для удаления!")
                return

            client_data = self.search_tree.item(selected)["values"]
            client_id = client_data[0]
            client_name = f"{client_data[1]} {client_data[2]}"

            if messagebox.askyesno(
                    "Подтверждение удаления",
                    f"Вы точно хотите удалить клиента {client_name} (ID: {client_id})?\n"
                    "Это действие нельзя отменить!"):

                try:
                    if self.db.delete_client_record(client_id):
                        messagebox.showinfo("Успех", f"Клиент {client_name} успешно удалён")
                        perform_search()  # Обновляем список после удаления
                    else:
                        messagebox.showerror("Ошибка", "Не удалось удалить клиента")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось удалить клиента:\n{e}")

        delete_btn = tk.Button(
            button_frame,
            text="Удалить",
            command=delete_selected,
            width=15
        )
        delete_btn.pack(side="left", padx=10)

        # Кнопка "Закрыть"
        close_btn = tk.Button(
            button_frame,
            text="Закрыть",
            command=search_window.destroy,
            width=15
        )
        close_btn.pack(side="right", padx=10)

        # Кнопка "Редактировать"
        edit_btn = tk.Button(
            button_frame,
            text="Редактировать",
            command=lambda: on_double_click(None),
            width=15
        )
        edit_btn.pack(side="left", padx=10)

        # Двойной клик для редактирования
        def on_double_click(event):
            item = self.search_tree.focus()
            if item:
                client_data = self.search_tree.item(item)["values"]
                #search_window.destroy()
                self._show_edit_client_dialog(*client_data[:4])  # ID, name, second_name, email

        self.search_tree.bind("<Double-1>", on_double_click)

        # # Кнопка редактирования
        # edit_btn = tk.Button(search_window, text="Редактировать выбранного",
        #                      command=lambda: on_double_click(None))
        # edit_btn.pack(pady=5, anchor="sw", side="left")
        # # Кнопка удаления
        # edit_btn = tk.Button(search_window, text="Удалить выбранного",
        #                      command=on_delete)
        # edit_btn.pack(pady=5, anchor="sw", side="right")

    def _show_search_results(self, parent_window, filters):
        """Отображает результаты поиска в таблице"""
        try:
            # Получаем отфильтрованных клиентов
            clients = self.db.search_clients(
                name=filters['name'],
                second_name=filters['second_name'],
                email=filters['email'],
                phone=filters['phone']
            )

            # Очищаем предыдущие результаты
            for item in self.search_tree.get_children():
                self.search_tree.delete(item)

            # Добавляем новые результаты
            for client in clients:
                phones = ", ".join(phone[0] for phone in client['phones'])
                self.search_tree.insert("", "end", values=(
                    client['id'],
                    client['name'],
                    client['second_name'],
                    client['email'],
                    phones
                ))

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить поиск:\n{e}")

    def show_settings(self):
        """Отображает окно настроек"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Параметры подключения")
        settings_window.geometry("400x300")
        px= root.winfo_x()
        py= root.winfo_y()
        settings_window.geometry(f"+{px+50}+{py+50}")

        # Получаем текущие настройки
        current_config = self.config.get_db_config()

        # Параметры подключения
        tk.Label(settings_window, text="Имя базы данных:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        dbname_entry = tk.Entry(settings_window)
        dbname_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        dbname_entry.insert(0, current_config['dbname'])

        tk.Label(settings_window, text="Хост:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        host_entry = tk.Entry(settings_window)
        host_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        host_entry.insert(0, current_config['host'])

        tk.Label(settings_window, text="Пользователь:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        user_entry = tk.Entry(settings_window)
        user_entry.grid(row=2, column=1, padx=5, pady=5, sticky="we")
        user_entry.insert(0, current_config['user'])

        tk.Label(settings_window, text="Пароль:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        password_entry = tk.Entry(settings_window, show="*")
        password_entry.grid(row=3, column=1, padx=5, pady=5, sticky="we")
        password_entry.insert(0, current_config['password'])

        tk.Label(settings_window, text="Порт:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        port_entry = tk.Entry(settings_window)
        port_entry.grid(row=4, column=1, padx=5, pady=5, sticky="we")
        port_entry.insert(0, current_config['port'])

        # Выбор языка
        tk.Label(settings_window, text=self.lang.get_text("menu_language")).grid(row=5, column=0, sticky="e", padx=6)
        lang_var = tk.StringVar(value=self.lang.current_lang)

        for i, lang_code in enumerate(self.lang.get_supported_languages()):
            rb = tk.Radiobutton(
                settings_window,
                text=self.lang.get_text(f"lang_{lang_code}"),
                variable=lang_var,
                value=lang_code,
                command=lambda: self.change_language(lang_var.get())
            )
            rb.grid(row=6 + i, column=1, columnspan=2, sticky="w")

        def save_settings():
            """Сохранение настроек"""
            new_config = {
                'dbname': dbname_entry.get(),
                'host': host_entry.get(),
                'user': user_entry.get(),
                'password': password_entry.get(),
                'port': int(port_entry.get())
            }

            self.config.update_db_config(**new_config)

            # Пробуем подключиться с новыми параметрами
            if self._connect_to_db(new_config):
                messagebox.showinfo("Успех", "Настройки сохранены и подключение обновлено!")
                settings_window.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось подключиться с новыми параметрами")

        # Кнопки
        btn_frame = tk.Frame(settings_window)
        btn_frame.grid(row=10, column=0, columnspan=2, pady=10)

        tk.Button(btn_frame, text="Сохранить", command=save_settings).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Отмена", command=settings_window.destroy).pack(side="left", padx=10)

    def __del__(self):
        pass


def print_hi(name):
    print(f'Hi, {name}')  #


if __name__ == '__main__':
    print_hi('H1!')
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()
