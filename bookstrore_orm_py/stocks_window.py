import tkinter as tk
from tkinter import ttk, messagebox
from db_handler import CRUDOperations


class StockManagementWindow:
    def __init__(self, parent, crud: CRUDOperations):
        self.parent = parent
        self.crud = crud
        self.selected_shop = None
        self.selected_book = None

        self.window = tk.Toplevel(parent)
        self.window.title("Управление стоком книг")
        self.window.geometry("900x600")

        # Верхняя часть - выбор магазина
        #self._create_shop_selection()
        self._create_selection_frame()

        # Средняя часть - таблица книг в стоке
        self._create_stock_table()

        # Нижняя часть - управление стоком
        self._create_management_controls()

        # Загружаем список магазинов
        self._load_shops()

    # прежний вариант, не используется
    def _create_shop_selection(self):
        """область выбора магазина"""
        shop_frame = tk.LabelFrame(self.window, text="Выбор магазина", padx=5, pady=5)
        shop_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(shop_frame, text="Магазин:").pack(side="left", padx=5)

        self.shop_combobox = ttk.Combobox(shop_frame, state="readonly", width=50)
        self.shop_combobox.pack(side="left", padx=5)
        self.shop_combobox.bind("<<ComboboxSelected>>", self._on_shop_selected)

        self.shop_info_label = tk.Label(shop_frame, text="Выберите магазин")
        self.shop_info_label.pack(side="left", padx=10)

    # новый
    def _create_selection_frame(self):
        """область выбора магазина и книги"""
        frame = tk.LabelFrame(self.window, text="Фильтр стоков", padx=5, pady=5)
        frame.pack(fill="x", padx=10, pady=5)

        # Верхняя строка - выбор через ID
        id_frame = tk.Frame(frame)
        id_frame.pack(fill="x", pady=5)

        tk.Label(id_frame, text="ID магазина:").pack(side="left", padx=5)
        self.shop_id_var = tk.StringVar()
        tk.Entry(id_frame, textvariable=self.shop_id_var, width=10).pack(side="left", padx=5)

        tk.Label(id_frame, text="ID книги:").pack(side="left", padx=5)
        self.book_id_var = tk.StringVar()
        tk.Entry(id_frame, textvariable=self.book_id_var, width=10).pack(side="left", padx=5)

        tk.Button(
            id_frame,
            text="Загрузить по ID",
            command=self._load_by_ids
        ).pack(side="left", padx=10)

        # Нижняя строка - выбор через комбобоксы
        combo_frame = tk.Frame(frame)
        combo_frame.pack(fill="x", pady=5)

        tk.Label(combo_frame, text="Магазин:").grid(row=0, column=0, padx=5, sticky="e")
        self.shop_combobox = ttk.Combobox(combo_frame, state="readonly", width=40)
        self.shop_combobox.grid(row=0, column=1, padx=5, sticky="w")
        self.shop_combobox.bind("<<ComboboxSelected>>", self._on_shop_selected)

        tk.Label(combo_frame, text="Книга:").grid(row=1, column=0, padx=5, sticky="e")
        self.book_combobox = ttk.Combobox(combo_frame, state="readonly", width=40)
        self.book_combobox.grid(row=1, column=1, padx=5, sticky="w")
        self.book_combobox.bind("<<ComboboxSelected>>", self._on_book_selected)

        tk.Button(combo_frame, text="Обновить", command=self._load_stock).grid(row=0, column=2, rowspan=2, padx=10)

    def _load_by_ids(self):
        """Загружает данные по введенным ID"""
        try:
            shop_id = int(self.shop_id_var.get()) if self.shop_id_var.get() else None
            book_id = int(self.book_id_var.get()) if self.book_id_var.get() else None

            if shop_id:
                shop = self.crud.get_shop_by_id(shop_id)
                if shop:
                    self.selected_shop = shop
                    self.shop_combobox.set(f"{shop.name} (ID: {shop.id})")

            if book_id:
                book = self.crud.get_book_by_id(book_id)
                if book:
                    # Для стока нужен и магазин и книга
                    if self.selected_shop:
                        stock = self.crud.get_stock(book_id, self.selected_shop.id)
                        if stock:
                            self.selected_book = stock
                            self.book_combobox.set(f"{book.title} (ID: {book.id}, в наличии: {stock.count})")

            self._load_stock()
            self._update_buttons_state()

        except ValueError:
            messagebox.showwarning("Ошибка", "ID должны быть числами")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {str(e)}")


    def _create_stock_table(self):
        """Создает таблицу с книгами в стоке"""
        table_frame = tk.Frame(self.window)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Таблица с вертикальной прокруткой
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        self.stock_tree = ttk.Treeview(
            table_frame,
            #columns=("id", "title", "author", "count"),
            columns=("id", "title", "count"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.stock_tree.yview)

        # Настройка столбцов
        self.stock_tree.heading("id", text="ID")
        self.stock_tree.heading("title", text="Название книги")
        #self.stock_tree.heading("author", text="Автор")
        self.stock_tree.heading("count", text="Количество")

        self.stock_tree.column("id", width=50, anchor="center")
        self.stock_tree.column("title", width=300)
        #self.stock_tree.column("author", width=200)
        self.stock_tree.column("count", width=100, anchor="center")

        self.stock_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Привязываем событие выбора
        self.stock_tree.bind("<<TreeviewSelect>>", self._on_book_selected)

    def _create_management_controls(self):
        """Создает элементы управления стоком"""
        control_frame = tk.Frame(self.window)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Поля для ввода количества
        tk.Label(control_frame, text="Количество:").grid(row=0, column=0, padx=5)
        self.count_var = tk.IntVar(value=1)
        self.count_entry = tk.Entry(control_frame, textvariable=self.count_var, width=10)
        self.count_entry.grid(row=0, column=1, padx=5)

        # Кнопки управления
        self.add_btn = tk.Button(
            control_frame,
            text="Добавить в сток",
            command=self._add_to_stock,
            state="disabled"
        )
        self.add_btn.grid(row=0, column=2, padx=5)

        self.update_btn = tk.Button(
            control_frame,
            text="Обновить количество",
            command=self._update_stock,
            state="disabled"
        )
        self.update_btn.grid(row=0, column=3, padx=5)

        self.remove_btn = tk.Button(
            control_frame,
            text="Удалить из стока",
            command=self._remove_from_stock,
            state="disabled",
            fg="red"
        )
        self.remove_btn.grid(row=0, column=4, padx=5)

        # Кнопка обновления данных
        tk.Button(control_frame, text="Обновить", command=self._load_stock).grid(row=0, column=5, padx=5)

    def _load_shops(self):
        """Загружает список магазинов в комбобокс"""
        shops = self.crud.read_shops()
        self.shops = {shop.name: shop for shop in shops}
        self.shop_combobox["values"] = list(self.shops.keys())

    def _on_shop_selected(self, event):
        """Обработчик выбора магазина"""
        shop_name = self.shop_combobox.get()
        self.selected_shop = self.shops.get(shop_name)

        if self.selected_shop:
            # self.shop_info_label.config(
            #     text=f"Выбран: {self.selected_shop.name} (ID: {self.selected_shop.id})"
            # )
            self._load_stock()
            self._update_buttons_state()

    def _load_stock(self):
        """Загружает книги в стоке выбранного магазина"""
        if not self.selected_shop:
            return

        # Очищаем таблицу
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)

        # Получаем сток для выбранного магазина
        stocks = self.crud.read_stock_by_shop(self.selected_shop.id)
        # Получаем сток для выбранного магазина с явным join книг
        # stocks = (self.session.query(Stock)
        #           .filter_by(id_shop=self.selected_shop.id)
        #           .join(Book)
        #           .all())

        # Заполняем таблицу
        for stock in stocks:
            self.stock_tree.insert("", "end",
                                   values=(
                                       stock.id_book,
                                       stock.book.title,
                                       #stock.book.author  if hasattr(stock.book, 'author') else "Не указан",
                                       stock.count
                                   ),
                                   tags=("stock",)
                                   )

    def _on_book_selected(self, event):
        """Обработчик выбора книги в таблице"""
        self._update_buttons_state()

    def _update_buttons_state(self):
        """Обновляет состояние кнопок в зависимости от выбора"""
        selected = self.stock_tree.selection()
        has_selection = bool(selected)
        shop_selected = bool(self.selected_shop)

        self.add_btn.config(state="normal" if shop_selected else "disabled")
        self.update_btn.config(state="normal" if (has_selection and shop_selected) else "disabled")
        self.remove_btn.config(state="normal" if (has_selection and shop_selected) else "disabled")

    def _add_to_stock(self):
        """Добавляет книгу в сток магазина"""
        try:
            # Получаем ID магазина (из выпадающего списка или ручного ввода)
            shop_id = None
            if self.selected_shop:
                shop_id = self.selected_shop.id
            elif self.shop_id_var.get():
                shop_id = int(self.shop_id_var.get())

            if not shop_id:
                messagebox.showwarning("Ошибка", "Укажите магазин (выбором или ID)")
                return

            # Получаем ID книги (из выпадающего списка или ручного ввода)
            book_id = None
            if self.selected_book:
                book_id = self.selected_book.id_book
            elif self.book_id_var.get():
                book_id = int(self.book_id_var.get())

            if not book_id:
                messagebox.showwarning("Ошибка", "Укажите книгу (выбором или ID)")
                return

            # Получаем количество
            count = self.count_var.get()
            if count <= 0:
                messagebox.showwarning("Ошибка", "Количество должно быть больше 0")
                return

            # Проверяем существование магазина и книги
            shop = self.crud.get_shop_by_id(shop_id)
            book = self.crud.get_book_by_id(book_id)

            if not shop:
                messagebox.showwarning("Ошибка", f"Магазин с ID {shop_id} не найден")
                return

            if not book:
                messagebox.showwarning("Ошибка", f"Книга с ID {book_id} не найдена")
                return

            # Добавляем/обновляем сток
            existing_stock = self.crud.get_stock(book_id, shop_id)
            if existing_stock:
                # Если сток уже существует - обновляем количество
                new_count = existing_stock.count + count
                self.crud.update_book_count_in_shop(book_id, shop_id, new_count)
                message = f"Количество обновлено. Новое количество: {new_count}"
            else:
                # Если стока нет - создаем новую запись
                self.crud.add_book_to_shop(book_id, shop_id, count)
                message = "Книга добавлена в сток"

            messagebox.showinfo("Успех", message)
            self._load_stock()

        except ValueError:
            messagebox.showerror("Ошибка", "ID магазина и книги должны быть числами")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось изменить сток: {str(e)}")


    def _update_stock(self):
        """Обновляет количество выбранной книги в стоке"""
        selected = self.stock_tree.selection()
        if not selected or not self.selected_shop:
            return

        item = self.stock_tree.item(selected[0])
        book_id = item["values"][0]

        try:
            new_count = self.count_var.get()
            if new_count <= 0:
                messagebox.showwarning("Ошибка", "Количество должно быть больше 0")
                return

            if self.crud.update_book_count_in_shop(book_id, self.selected_shop.id, new_count):
                messagebox.showinfo("Успех", "Количество обновлено")
                self._load_stock()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить количество")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при обновлении: {e}")


    def _remove_from_stock(self):
        """Удаляет выбранную книгу из стока или по указанным ID"""
        try:
            # Вариант 1: Есть выбранная запись в таблице
            selected = self.stock_tree.selection()
            if selected:
                item = self.stock_tree.item(selected[0])
                book_id = item["values"][0]  # ID книги в первом столбце
                shop_id = self.selected_shop.id if self.selected_shop else None

                if not shop_id and self.shop_id_var.get():
                    shop_id = int(self.shop_id_var.get())

                if not shop_id:
                    messagebox.showwarning("Ошибка", "Укажите магазин (выбором или ID)")
                    return

                if not messagebox.askyesno(
                        "Подтверждение",
                        f"Удалить книгу ID {book_id} из стока магазина ID {shop_id}?"
                ):
                    return

                if self.crud.remove_book_from_shop(book_id, shop_id):
                    messagebox.showinfo("Успех", "Книга удалена из стока")
                    self._load_stock()
                else:
                    messagebox.showerror("Ошибка", "Не удалось удалить книгу")
                return

            # Вариант 2: Удаление по введенным ID
            if not self.book_id_var.get() or not self.shop_id_var.get():
                messagebox.showwarning("Ошибка", "Выберите запись или укажите ID книги и магазина")
                return

            book_id = int(self.book_id_var.get())
            shop_id = int(self.shop_id_var.get())

            if not messagebox.askyesno(
                    "Подтверждение",
                    f"Удалить книгу ID {book_id} из стока магазина ID {shop_id}?"
            ):
                return

            if self.crud.remove_book_from_shop(book_id, shop_id):
                messagebox.showinfo("Успех", "Книга удалена из стока")
                self._load_stock()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить книгу")

        except ValueError:
            messagebox.showerror("Ошибка", "ID магазина и книги должны быть числами")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении: {str(e)}")
