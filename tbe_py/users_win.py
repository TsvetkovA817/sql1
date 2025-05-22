import tkinter as tk
from tkinter import ttk, messagebox
from db_handler import CRUDOperations


class UsersManagementWindow:
    def __init__(self, master, db_url, main_window_pos):
        self.master = master
        self.crud = CRUDOperations(db_url)

        # Позиционирование окна на 50 пикселей ниже и правее главного окна
        x = main_window_pos[0] + 50
        y = main_window_pos[1] + 50
        self.master.geometry(f"900x600+{x}+{y}")

        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        self.master.title("Управление пользователями")

        # Frame для фильтров
        filter_frame = ttk.LabelFrame(self.master, text="Фильтры", padding=10)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        # Поля фильтрации
        ttk.Label(filter_frame, text="ID Telegram:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.telegram_id_filter = ttk.Entry(filter_frame)
        self.telegram_id_filter.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)

        ttk.Label(filter_frame, text="Имя пользователя:").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        self.username_filter = ttk.Entry(filter_frame)
        self.username_filter.grid(row=0, column=3, padx=5, pady=2, sticky=tk.EW)

        ttk.Label(filter_frame, text="Язык интерфейса:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.ui_lang_filter = ttk.Combobox(filter_frame, values=["", "ru", "en", "zh"])
        self.ui_lang_filter.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)

        ttk.Label(filter_frame, text="Целевой язык:").grid(row=1, column=2, padx=5, pady=2, sticky=tk.W)
        self.target_lang_filter = ttk.Combobox(filter_frame, values=["", "en", "zh"])
        self.target_lang_filter.grid(row=1, column=3, padx=5, pady=2, sticky=tk.EW)

        # Кнопка применения фильтров
        filter_btn = ttk.Button(filter_frame, text="Применить фильтры", command=self.apply_filters)
        filter_btn.grid(row=2, column=0, columnspan=4, pady=5)

        # Таблица пользователей
        self.tree_frame = ttk.Frame(self.master)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("id", "telegram_id", "username", "ui_lang", "target_lang", "created", "last_active"),
            show="headings"
        )

        # Настройка столбцов
        columns = [
            ("id", "ID", 50),
            ("telegram_id", "Telegram ID", 120),
            ("username", "Имя пользователя", 150),
            ("ui_lang", "Язык интерфейса", 100),
            ("target_lang", "Целевой язык", 100),
            ("created", "Дата регистрации", 120),
            ("last_active", "Последняя активность", 120)
        ]

        for col_id, col_text, col_width in columns:
            self.tree.heading(col_id, text=col_text, anchor=tk.W)
            self.tree.column(col_id, width=col_width, stretch=tk.NO if col_width else tk.YES)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Bind double click for edit
        self.tree.bind("<Double-1>", self.on_double_click)

        # Frame для кнопок CRUD
        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="Добавить", command=self.add_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Редактировать", command=self.edit_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Обновить", command=self.load_users).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Закрыть", command=self.master.destroy).pack(side=tk.RIGHT, padx=5)

    def load_users(self, filters=None):
        """Загрузка пользователей в таблицу"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        users = self.crud.get_all_users()  # метод в CRUDOperations ok

        for user in users:
            self.tree.insert("", tk.END, values=(
                user.id,
                user.telegram_id,
                user.username,
                user.ui_language,
                user.target_language,
                user.create_date.strftime("%Y-%m-%d") if user.create_date else "",
                user.last_active_date.strftime("%Y-%m-%d") if user.last_active_date else ""
            ))

    def apply_filters(self):
        """Применение фильтров"""
        # TODO: Здесь реализовать фильтрацию
        # Пока просто загружаем всех пользователей
        self.load_users()

    def add_user(self):
        """Открытие окна добавления пользователя"""
        self.user_dialog = tk.Toplevel(self.master)
        self.user_dialog.title("Добавить пользователя")

        self.setup_user_form(self.user_dialog, None)

    def edit_user(self):
        """Редактирование выбранного пользователя"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите пользователя для редактирования")
            return

        user_id = self.tree.item(selected[0], "values")[0]
        user = self.crud.get_user_by_id(user_id)  # метод в CRUDOperations

        if not user:
            messagebox.showerror("Ошибка", "Пользователь не найден")
            return

        self.user_dialog = tk.Toplevel(self.master)
        self.user_dialog.title("Редактировать пользователя")

        self.setup_user_form(self.user_dialog, user)

    def on_double_click(self, event):
        """Обработка двойного клика по пользователю"""
        self.edit_user()

    def setup_user_form(self, parent, user):
        """Настройка формы пользователя (добавление/редактирование)"""
        is_edit = user is not None

        # Основные поля
        ttk.Label(parent, text="Telegram ID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        telegram_id_entry = ttk.Entry(parent)
        telegram_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(parent, text="Имя пользователя:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        username_entry = ttk.Entry(parent)
        username_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(parent, text="Язык интерфейса:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        ui_lang_combobox = ttk.Combobox(parent, values=["ru", "en", "zh"])
        ui_lang_combobox.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(parent, text="Целевой язык:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        target_lang_combobox = ttk.Combobox(parent, values=["en", "zh"])
        target_lang_combobox.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

        if is_edit:
            telegram_id_entry.insert(0, user.telegram_id)
            username_entry.insert(0, user.username)
            ui_lang_combobox.set(user.ui_language)
            target_lang_combobox.set(user.target_language)

        # Frame для кнопок
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(
            btn_frame,
            text="Сохранить",
            command=lambda: self.save_user(
                user.id if is_edit else None,
                telegram_id_entry.get(),
                username_entry.get(),
                ui_lang_combobox.get(),
                target_lang_combobox.get()
            )
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Отмена",
            command=parent.destroy
        ).pack(side=tk.LEFT, padx=5)

    def save_user(self, user_id, telegram_id, username, ui_language, target_language):
        """Сохранение пользователя (добавление или обновление)"""
        if not telegram_id:
            messagebox.showwarning("Предупреждение", "Введите Telegram ID")
            return

        try:
            if user_id:  # Редактирование
                # TODO: crud.update_user
                # user = self.crud.update_user(
                #     user_id=user_id,
                #     telegram_id=telegram_id,
                #     username=username,
                #     ui_language=ui_language,
                #     target_language=target_language
                # )
                # messagebox.showinfo("Успех", "Пользователь успешно обновлен")
                messagebox.showinfo("Успех", "Нажата кнопка обновления")
            else:  # Добавление
                user = self.crud.create_user(
                    telegram_id=telegram_id,
                    username=username,
                    ui_language=ui_language,
                    target_language=target_language
                )
                messagebox.showinfo("Успех", "Пользователь успешно добавлен")

            self.load_users()
            self.user_dialog.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить пользователя: {str(e)}")

    def delete_user(self):
        """Удаление выбранного пользователя"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите пользователя для удаления")
            return

        user_id = self.tree.item(selected[0], "values")[0]

        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить этого пользователя?"):
            return

        try:
            # TODO: В CRUD нет метода delete_user,  добавить
            # предположим, что он есть
            # self.crud.delete_user(user_id)
            # messagebox.showinfo("Успех", "Пользователь успешно удален")
            messagebox.showinfo("Успех", "Нажата кнопка удаления")
            self.load_users()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить пользователя: {str(e)}")


# тест
if __name__ == "__main__":
    root = tk.Tk()
    db_url = "postgresql://postgres:****@localhost/lfl"
    main_window_pos = (100, 100)  # Позиция главного окна
    app = UsersManagementWindow(root, db_url, main_window_pos)
    root.mainloop()
