import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from config_handler import ConfigHandler
from language_handler import LanguageHandler
from db_handler import DBSession, CRUDOperations

from users_win import UsersManagementWindow
from lessons_window import LessonsManagementWindow
from phrases_win import PhrasesManagementWindow

#from dic_window import DicManagementWindow
from  bot import LanguageBot

class MainApp:
    def __init__(self, root):

        self.config = ConfigHandler()
        self.db_config = self.config.get_db_config()
        self.bot_config = self.config.get_bot_set()

        # Инициализация подключения к БД
        self.db = None
        self.session = None
        self.crud = None
        self.language_bot = None

        # Инициализация
        #self.db = DBSession("postgresql://postgres:5432@localhost/postgres")
        #self.db = DBSession(dbname = "postgres", host = "127.0.0.1", user = "postgres", password = "****", port = 5432)
        #self.crud = CRUDOperations(self.db)

        self.root = root
        self.lang = LanguageHandler()
        print('winfo_screenwidth()=', root.winfo_screenwidth())
        print('winfo_reqwidth()=', root.winfo_reqwidth())
        print('winfo_screenheight()=', root.winfo_screenheight())
        print('winfo_reqheight()=', root.winfo_reqheight())

        x= root.winfo_screenwidth() // 2
        y = root.winfo_screenheight()//2

        w = 600
        h = 400

        self.root.geometry(f"{w}x{h}+{x-w//2}+{y-h//2}")
        self._connect_to_db(self.db_config)
        #elf.db_url = self._get_db_url()

        self.botkey = self.config.get_bot_set()['key']
        # Создаем экземпляр бота
        print(self.db_url)
        print(self.botkey)

        self.language_bot = LanguageBot(self.botkey, self.db_url)

        self._init_ui()


    # def _get_db_url(self):
    #     self.db_url = self.db.db_url

    def _connect_to_db(self, db_config):
        """Подключиться к БД с указанными параметрами"""
        try:
            print(db_config)
            self.db = DBSession(**db_config)
            self.db_url = self.db.db_url
            if not self.db.is_connected():
                print("Ошибка: Нет подключения к БД!")
                if hasattr(self, 'status_label'):
                    self.status_label.config(text="Не подключено к БД", fg="red")
            else:
                self.crud = CRUDOperations(self.db.db_url)
                #self.db_connection = self.db.conn
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
        current_config = self.config.get_db_config()
        self.label3 = tk.Label(
            main_frame,
            text=self.lang.get_text("current_db_status").format(
                dbname=current_config['dbname'] if current_config['dbname'] else "N/A"
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
        self.file_menu.add_command(label = self.lang.get_text("menu_file_existdb"), command = self.exist_file)
        self.file_menu.add_command(label = self.lang.get_text("menu_file_open"), command = self.open_file)
        self.file_menu.add_command(label = self.lang.get_text("menu_file_delete"), command = self.del_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.lang.get_text("menu_file_create_tables"), command = self.create_tables)
        self.file_menu.add_command(label=self.lang.get_text("menu_file_drop_tables"), command = self.drop_tables)
        self.file_menu.add_separator()
        self.file_menu.add_command(label = self.lang.get_text("menu_file_exit"), command = self.exit_app)

        self.bot_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.bot_menu.add_command(label=self.lang.get_text("menu_bot_start"), command = self.start_bot)
        self.bot_menu.add_command(label = self.lang.get_text("menu_bot_stop"), command = self.stop_bot)
        self.bot_menu.add_command(label = self.lang.get_text("menu_bot_status"), command = self.status_bot)

        self.data_menu = tk.Menu(self.menu_bar, tearoff=0)   # Меню "Данные"
        self.data_menu.add_command(label=self.lang.get_text("menu_data_lessons"), command=self.show_lessons_window)
        self.data_menu.add_command(label=self.lang.get_text("menu_data_users"), command=self.show_users_window)
        self.data_menu.add_command(label=self.lang.get_text("menu_data_phrases"), command=self.show_phrases_window)

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
        self.menu_bar.add_cascade(label=self.lang.get_text("menu_bot"), menu=self.bot_menu)
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
        if self.db.is_connected():
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


    def create_file(self):
        """Создание новой базы данных с использованием класса ClientsDb"""
        db_name = simpledialog.askstring("Создание БД", "Введите имя новой базы данных:")
        if db_name:
            try:
                # Создаем временное подключение для создания БД
                if  self.session:
                    self.db.close()
                if self.db:
                    del self.db
                    self.db = None

                temp_db = DBSession()

                # Создаем новую БД и таблицы
                if temp_db.create_db(db_name):
                    messagebox.showinfo("Успех", f"База данных {db_name} успешно создана!")

                    # Подключаемся к новой БД
                    self.db = DBSession(dbname=db_name)
                    #self.db_connection = self.db.conn
                    self.status_label.config(text=f"Подключено к БД: {db_name}", fg="green")
                else:
                    messagebox.showerror("Ошибка", "Не удалось создать базу данных")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать базу данных:\n{e}")
            finally:
                # Закрываем временное подключение
                if 'temp_db' in locals():
                    del temp_db

    def exist_file(self):
        db_name = simpledialog.askstring("Создание БД", "Введите имя базы данных:")
        if db_name:
            try:
                if not self.db:
                    self.db = DBSession()
                if self.db.db_exists(db_name):
                    print('БД существует')
                else:
                    print('БД не существует')
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть базу данных:\n{e}")


    def open_file(self):
        """Подключение к существующей базе данных"""
        db_name = simpledialog.askstring("Открытие БД", "Введите имя базы данных для подключения:")
        if db_name:
            try:
                # Закрываем предыдущее подключение, если оно есть
                if self.db:
                    self.db.close()
                    del self.db

                # Создаем новое подключение
                self.db = DBSession(dbname=db_name)

                # Проверяем существование таблиц
                #cursor = self.db_connection.cursor()
                #cursor.execute("SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name='clients');")
                #if not cursor.fetchone()[0]:
                #    messagebox.showwarning("Предупреждение", "В базе данных отсутствуют необходимые таблицы!")

                self.status_label.config(text=f"Подключено к БД: {db_name}", fg="green")
                messagebox.showinfo("Успех", f"Успешное подключение к базе данных {db_name}!")

            except Exception as e:
                self.db = None
                self.status_label.config(text="Не подключено к БД", fg="red")
                messagebox.showerror("Ошибка", f"Не удалось подключиться к базе данных:\n{e}")


    def del_file(self):
        """Удаление базы данных"""
        db_name = simpledialog.askstring("Удаление БД", "Введите имя базы данных для удаления:")
        if db_name:
            if messagebox.askyesno("Подтверждение",
                                   f"Вы уверены, что хотите удалить базу данных {db_name}?\nЭто действие нельзя отменить!"):
                try:
                    # Создаем временное подключение для удаления БД
                    temp_db = DBSession()

                    if temp_db.drop_db(db_name):
                        messagebox.showinfo("Успех", f"База данных {db_name} успешно удалена!")

                        # Если удаляли текущую БД, обновляем статус
                        if self.db and self.db._dbname == db_name:
                            del self.db
                            self.db = None
                            self.session = None
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
        # askokcancel - кнопки не lang, доработать
        if messagebox.askokcancel(self.lang.get_text("menu_file_exit"), self.lang.get_text("confirm_exit")):
            if self.db:
                self.db.close()
                del self.db  # Вызовет __del__ и закроет соединение
            self.root.destroy()

    def create_tables(self):
        """Создание всех таблиц по моделям"""
        # askokcancel - кнопки не lang, изменить
        if messagebox.askokcancel(self.lang.get_text("menu_file_create_tables"), self.lang.get_text("menu_file_create_tables")):
            self.db.create_tables()

    def drop_tables(self):
        """Удаление всех таблиц по моделям"""
        # askokcancel - кнопки не lang, изменить
        if messagebox.askokcancel(self.lang.get_text("menu_file_drop_tables"), self.lang.get_text("menu_file_drop_tables")):
            self.db.drop_tables()

    # def show_publishers_window2(self):
    #     #db = DBSession(**self.db_config)
    #     #crud = CRUDOperations(db)
    #     publishers_window = PublishersWindow(root, self.crud)
    #
    # def show_books_window(self):
    #     BooksWindow(root, self.crud)
    #

    def show_lessons_window(self):
        db = DBSession(**self.db_config)
        print(db.db_url)
        LessonsManagementWindow(root, db.db_url)

    def show_users_window(self):
        # TODO: переделать
        db = DBSession(**self.db_config)
        print(db.db_url)
        main_window_pos = (self.root.winfo_x(), self.root.winfo_y())
        users_window = tk.Toplevel(self.root)
        UsersManagementWindow(users_window, db.db_url, main_window_pos)

    def show_phrases_window(self):
        db = DBSession(**self.db_config)
        print(db.db_url)
        main_window_pos = (self.root.winfo_x(), self.root.winfo_y())
        users_window = tk.Toplevel(self.root)
        PhrasesManagementWindow(users_window, db.db_url, main_window_pos)

    def start_bot(self):
        result = self.language_bot.start_bot()
        print(result)

    def stop_bot(self):
        result = self.language_bot.stop_bot()
        print(result)

    def status_bot(self):
        status = self.language_bot.get_bot_status()
        print(status)


    def about_prog(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("О программе")

        parent_x = self.root.winfo_x()  # Получаем X-координату главного окна
        parent_y = self.root.winfo_y()  # Получаем Y-координату главного окна
        about_window.geometry("300x200")
        about_window.geometry(f"+{parent_x + 50}+{parent_y + 50}")  # Смещение на 50 пикселей вправо и вниз

        tk.Label(about_window, text="Менеджер базы данных тбота TBLE\nВерсия 1.0 TsvetkovAV\n\nPostgreSQL TBLearnEng\n© 2025",
                 font=('Arial', 12)).pack(pady=20)
        tk.Button(about_window, text="Закрыть",
                  command=about_window.destroy).pack(pady=10)

    def _show_edit_client_dialog(self, client_id, name, second_name, email):
        pass

    def _show_search_results(self, parent_window, filters):
        pass

    def show_settings(self):
        """Отображает окно настроек"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Параметры подключения")
        settings_window.geometry("400x350")
        px = root.winfo_x()
        py = root.winfo_y()
        settings_window.geometry(f"+{px + 50}+{py + 50}")

        # Получаем текущие настройки
        current_config = self.config.get_db_config()
        bot_config = self.config.get_bot_set()
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

        tk.Label(settings_window, text="Ключ бот:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        key_entry = tk.Entry(settings_window)
        key_entry.grid(row=5, column=1, padx=5, pady=5, sticky="we")
        key_entry.insert(0, bot_config['key'])

        tk.Label(settings_window, text="Имя бота:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
        name_entry = tk.Entry(settings_window)
        name_entry.grid(row=6, column=1, padx=5, pady=5, sticky="we")
        name_entry.insert(0, bot_config['name'])

        # Выбор языка
        tk.Label(settings_window, text=self.lang.get_text("menu_language")).grid(row=7, column=0, sticky="e",
                                                                                 padx=6)
        lang_var = tk.StringVar(value=self.lang.current_lang)

        for i, lang_code in enumerate(self.lang.get_supported_languages()):
            rb = tk.Radiobutton(
                settings_window,
                text=self.lang.get_text(f"lang_{lang_code}"),
                variable=lang_var,
                value=lang_code,
                command=lambda: self.change_language(lang_var.get())
            )
            rb.grid(row=7 + i, column=1, columnspan=2, sticky="w")

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
            self.config.update_bot_set(key_entry.get(), name_entry.get())

            self._init_ui()
            # Пробуем подключиться с новыми параметрами
            self.db_config = self.config.get_db_config()
            self.bot_config = self.config.get_bot_set()
            if self._connect_to_db(self.db_config):
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
    print(f'Hi, {name}')  # тест


if __name__ =='__main__':
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
