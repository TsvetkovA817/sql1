import tkinter as tk
from tkinter import ttk, messagebox
from db_handler import CRUDOperations  # Импорт CRUD


class PublishersWindow:
    def __init__(self, parent, crud: CRUDOperations):
        self.parent = parent
        self.crud = crud

        self.window = tk.Toplevel(parent)
        self.window.title("Справочник издателей")
        self.window.geometry("800x600")

        # Переменные для поиска
        self.search_id_var = tk.StringVar()
        self.search_name_var = tk.StringVar()

        self._create_search_frame()
        self._create_results_table()
        self._create_buttons()

        # Загружаем все издателей при открытии
        self.search_publishers()

    def _create_search_frame(self):
        """Создает область поиска"""
        search_frame = tk.LabelFrame(self.window, text="Поиск издателей", padx=5, pady=5)
        search_frame.pack(fill="x", padx=5, pady=5)

        # Поле для поиска по ID
        tk.Label(search_frame, text="ID:").grid(row=0, column=0, padx=5, sticky="e")
        tk.Entry(search_frame, textvariable=self.search_id_var, width=10).grid(row=0, column=1, padx=5, sticky="w")

        # Поле для поиска по имени
        tk.Label(search_frame, text="Название:").grid(row=0, column=2, padx=5, sticky="e")
        tk.Entry(search_frame, textvariable=self.search_name_var, width=30).grid(row=0, column=3, padx=5, sticky="w")

        # Кнопка поиска
        tk.Button(search_frame, text="Поиск", command=self.search_publishers).grid(row=0, column=4, padx=10)

    def _create_results_table(self):
        """Создает таблицу с результатами"""
        frame = tk.Frame(self.window)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Таблица с вертикальной прокруткой
        scrollbar = ttk.Scrollbar(frame, orient="vertical")
        self.tree = ttk.Treeview(
            frame,
            columns=("id", "name"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)

        # Настройка столбцов
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Название издательства")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=300)

        # Размещение таблицы и скроллбара
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Обработчик двойного клика для редактирования
        self.tree.bind("<Double-1>", self._edit_selected_publisher)

    def _create_buttons(self):
        """Создает кнопки управления"""
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(fill="x", padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="Добавить издателя",
            command=self._add_publisher
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="Редактировать",
            command=self._edit_selected_publisher
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="Удалить",
            command=self._delete_selected_publisher,
            fg="red"
        ).pack(side="left", padx=5)

    def search_publishers(self):
        """Выполняет поиск издателей по критериям"""
        # Очищаем предыдущие результаты
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Получаем параметры поиска
        search_id = self.search_id_var.get().strip()
        search_name = self.search_name_var.get().strip()

        # Формируем фильтры
        filters = {}
        if search_id:
            try:
                filters["id"] = int(search_id)
            except ValueError:
                messagebox.showwarning("Ошибка", "ID должен быть числом")
                return

        if search_name:
            filters["name"] = search_name

        # Получаем издателей через CRUD
        publishers = self.crud.read_publishers(**filters)

        # Заполняем таблицу
        for pub in publishers:
            self.tree.insert("", "end", values=(pub.id, pub.name))

    def _add_publisher(self):
        """Открывает форму добавления нового издателя"""
        add_window = tk.Toplevel(self.window)
        add_window.title("Добавить издателя")

        tk.Label(add_window, text="Название:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = tk.Entry(add_window, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Ошибка", "Введите название издательства")
                return

            try:
                self.crud.create_publisher(name)
                messagebox.showinfo("Успех", "Издатель успешно добавлен")
                add_window.destroy()
                self.search_publishers()  # Обновляем список
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить издателя: {e}")

        tk.Button(
            add_window,
            text="Сохранить",
            command=save
        ).grid(row=1, columnspan=2, pady=5)

    def _edit_selected_publisher(self, event=None):
        """Открывает форму редактирования выбранного издателя"""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите издателя для редактирования")
            return

        publisher_data = self.tree.item(selected)["values"]
        pub_id, pub_name = publisher_data

        edit_window = tk.Toplevel(self.window)
        edit_window.title(f"Редактирование издателя ID: {pub_id}")

        tk.Label(edit_window, text="Название:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = tk.Entry(edit_window, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.insert(0, pub_name)

        def save():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("Ошибка", "Введите название издательства")
                return

            try:
                if self.crud.update_publisher(pub_id, new_name):
                    messagebox.showinfo("Успех", "Данные издателя обновлены")
                    edit_window.destroy()
                    self.search_publishers()  # Обновляем список
                else:
                    messagebox.showerror("Ошибка", "Не удалось обновить издателя")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при обновлении: {e}")

        tk.Button(
            edit_window,
            text="Сохранить",
            command=save
        ).grid(row=1, columnspan=2, pady=5)

    def _delete_selected_publisher(self):
        """Удаляет выбранного издателя"""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите издателя для удаления")
            return

        publisher_data = self.tree.item(selected)["values"]
        pub_id, pub_name = publisher_data

        if not messagebox.askyesno(
                "Подтверждение",
                f"Вы уверены, что хотите удалить издателя?\nID: {pub_id}\nНазвание: {pub_name}"
        ):
            return

        try:
            if self.crud.delete_publisher(pub_id):
                messagebox.showinfo("Успех", "Издатель успешно удален")
                self.search_publishers()  # Обновляем список
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить издателя")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении: {e}\nВозможно, есть связанные книги.")