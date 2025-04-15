import tkinter as tk
from tkinter import ttk, messagebox
from db_handler import CRUDOperations  # Импорт CRUD


class BooksWindow:
    def __init__(self, parent, crud: CRUDOperations):

        self.parent = parent
        self.crud = crud

        self.window = tk.Toplevel(parent)
        self.window.title("Справочник книг")
        self.window.geometry("800x600")

        # Переменные для поиска
        self.search_id_var = tk.StringVar()
        self.search_name_var = tk.StringVar()

        self._create_search_frame()
        self._create_results_table()
        self._create_buttons()

        # Загружаем издателей при открытии
        self.search_books()

    def _create_search_frame(self):
        """Создает область поиска"""
        search_frame = tk.LabelFrame(self.window, text="Поиск", padx=5, pady=5)
        search_frame.pack(fill="x", padx=5, pady=5)

        # Поле для поиска по ID
        tk.Label(search_frame, text="ID:").grid(row=0, column=0, padx=5, sticky="e")
        tk.Entry(search_frame, textvariable=self.search_id_var, width=10).grid(row=0, column=1, padx=5, sticky="w")

        # Поле для поиска по имени
        tk.Label(search_frame, text="Название:").grid(row=0, column=2, padx=5, sticky="e")
        tk.Entry(search_frame, textvariable=self.search_name_var, width=30).grid(row=0, column=3, padx=5, sticky="w")

        # Кнопка поиска
        tk.Button(search_frame, text="Поиск", command=self.search_books).grid(row=0, column=4, padx=10)

    def _create_results_table(self):
        """Создает таблицу с результатами"""
        frame = tk.Frame(self.window)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Таблица с вертикальной прокруткой
        scrollbar = ttk.Scrollbar(frame, orient="vertical")
        self.tree = ttk.Treeview(
            frame,
            columns=("id", "name", "publisher"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)

        # Настройка столбцов
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Название")
        self.tree.heading("publisher", text="Издатель")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=300)
        self.tree.column("publisher", width=150)

        # Размещение таблицы и скроллбара
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Обработчик двойного клика для редактирования
        self.tree.bind("<Double-1>", self._edit_selected_book)

    def _create_buttons(self):
        """Создает кнопки управления"""
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(fill="x", padx=5, pady=5)

        tk.Button(
            btn_frame,
            text=" Добавить ",
            command=self._add_book
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="Редактировать",
            command=self._edit_selected_book
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="Удалить",
            command=self._delete_selected_book,
            fg="red"
        ).pack(side="left", padx=5)

    def search_books(self):
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
            filters["title"] = search_name

        # Получаем через CRUD
        books = self.crud.read_books(**filters)

        # Заполняем таблицу
        for book in books:
            publisher_name = book.publisher.name if book.publisher else "Не указан"
            self.tree.insert("", "end", values=(book.id, book.title, publisher_name))


    def _add_book(self):
        """Открывает форму добавления нового """
        add_window = tk.Toplevel(self.window)
        add_window.title("Добавить")

        tk.Label(add_window, text="Название:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = tk.Entry(add_window, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        # Выбор издателя
        tk.Label(add_window, text="Издатель:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        publisher_combobox = ttk.Combobox(add_window, width=27)
        publisher_combobox.grid(row=2, column=1, padx=5, pady=5)

        # Заполняем комбобокс издателями
        publishers = self.crud.read_publishers()
        publisher_names = [p.name for p in publishers]
        publisher_combobox['values'] = publisher_names
        if publisher_names:
            publisher_combobox.current(0)

        def save():
            name = name_entry.get().strip()
            publisher_name = publisher_combobox.get().strip()
            if not name:
                messagebox.showwarning("Ошибка", "Введите название ")
                return

            try:
                # Находим издателя по имени
                publisher = next((p for p in publishers if p.name == publisher_name), None)
                if not publisher:
                    messagebox.showwarning("Ошибка", "Выберите издателя из списка")
                    return

                #self.crud.create_book(title = name, publisher_id = publisher.id)
                self.crud.create_book(name, publisher_id=publisher.id)
                messagebox.showinfo("Успех", "Успешно добавлено")
                add_window.destroy()
                self.search_books()  # Обновляем список
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить: {e}")

        tk.Button(
            add_window,
            text="Сохранить",
            command=save
        ).grid(row=1, columnspan=2, pady=5)


    def _edit_selected_book(self, event=None):
        """Открывает форму редактирования выбранную книгу"""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите строку для редактирования")
            return

        book_data = self.tree.item(selected)["values"]
        book_id, book_name, book_pub_id = book_data
        #book_id = book_data[0]

        # Получаем полные данные о книге
        book = self.crud.get_book_by_id(book_id)
        if not book:
            messagebox.showerror("Ошибка", "Книга не найдена")
            return

        edit_window = tk.Toplevel(self.window)
        edit_window.title(f"Редактирование ID: {book_id}")

        tk.Label(edit_window, text="Название:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = tk.Entry(edit_window, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.insert(0, book_name)

        # Выбор издателя
        tk.Label(edit_window, text="Издатель:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        publisher_combobox = ttk.Combobox(edit_window, width=27)
        publisher_combobox.grid(row=2, column=1, padx=5, pady=5)

        # Заполняем комбобокс издателями
        publishers = self.crud.read_publishers()
        publisher_names = [p.name for p in publishers]
        publisher_combobox['values'] = publisher_names

        # Устанавливаем текущего издателя
        if book.publisher:
            publisher_combobox.set(book.publisher.name)
        elif publisher_names:
            publisher_combobox.current(0)

        def save():
            new_name = name_entry.get().strip()
            new_publisher_name = publisher_combobox.get().strip()

            if not new_name:
                messagebox.showwarning("Ошибка", "Введите название ")
                return

            try:
                # Находим нового издателя по имени
                new_publisher = next((p for p in publishers if p.name == new_publisher_name), None)
                if not new_publisher:
                    messagebox.showwarning("Ошибка", "Выберите издателя из списка")
                    return

                if self.crud.update_book(book_id, new_title=new_name, new_publisher_id=new_publisher.id ):
                    messagebox.showinfo("Успех", "Данные обновлены")
                    edit_window.destroy()
                    self.search_books()  # Обновляем список
                else:
                    messagebox.showerror("Ошибка", "Не удалось обновить ")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при обновлении: {e}")

        tk.Button(
            edit_window,
            text="Сохранить",
            command=save
        ).grid(row=1, columnspan=2, pady=5)


    def _delete_selected_book(self):
        """Удаляет выбранного """
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите строку для удаления")
            return

        book_data = self.tree.item(selected)["values"]
        book_id, book_name = book_data

        if not messagebox.askyesno(
                "Подтверждение",
                f"Вы уверены, что хотите удалить?\nID: {book_id}\nНазвание: {book_name}"
        ):
            return

        try:
            if self.crud.delete_book(book_id):
                messagebox.showinfo("Успех", "Успешно удалено")
                self.search_books()  # Обновляем список
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить ")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении: {e}\nВозможно, есть связанные данные.")
