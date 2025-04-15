import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timezone
from db_handler import CRUDOperations


class SalesManagementWindow:
    def __init__(self, parent, crud: CRUDOperations):
        self.parent = parent
        self.crud = crud
        self.selected_shop = None
        self.selected_book = None

        self.window = tk.Toplevel(parent)
        self.window.title("Управление продажами книг")
        self.window.geometry("1000x700")

        # выбор магазина и книги
        self._create_selection_frame()

        # таблица продаж книг
        self._create_sales_table()

        # управление продажами
        self._create_controls_frame()

        # Загружаем начальные данные
        self._load_shops()
        self._load_sales()

    def _create_selection_frame(self):
        """Создает область выбора магазина и книги"""
        frame = tk.LabelFrame(self.window, text="Выбор магазина и книги", padx=5, pady=5)
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

        # Выбор магазина
        tk.Label(combo_frame, text="Магазин:").grid(row=0, column=0, padx=5, sticky="e")
        self.shop_combobox = ttk.Combobox(combo_frame, state="readonly", width=40)
        self.shop_combobox.grid(row=0, column=1, padx=5, sticky="w")
        self.shop_combobox.bind("<<ComboboxSelected>>", self._on_shop_selected)

        # Выбор книги
        tk.Label(combo_frame, text="Книга:").grid(row=1, column=0, padx=5, sticky="e")
        self.book_combobox = ttk.Combobox(combo_frame, state="readonly", width=40)
        self.book_combobox.grid(row=1, column=1, padx=5, sticky="w")
        self.book_combobox.bind("<<ComboboxSelected>>", self._on_book_selected)

        # Кнопка обновления
        tk.Button(combo_frame, text="Обновить", command=self._load_sales).grid(row=0, column=2, rowspan=2, padx=10)


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
                    # Находим сток для выбранного магазина (если он задан)
                    stock = self.crud.get_stock(book_id, self.selected_shop.id) if self.selected_shop else None
                    if stock:
                        self.selected_book = stock
                        self.book_combobox.set(f"{book.title} (ID: {book.id}, в наличии: {stock.count})")

            self._load_sales()
            self._update_buttons_state()

        except ValueError:
            messagebox.showwarning("Ошибка", "ID должны быть числами")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {str(e)}")


    def _create_sales_table(self):
        """Создает таблицу с продажами"""
        frame = tk.Frame(self.window)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Таблица с вертикальной прокруткой
        scrollbar = ttk.Scrollbar(frame, orient="vertical")
        self.tree = ttk.Treeview(
            frame,
            columns=("id", "title", "shop", "price", "quantity", "date", "stock_id"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)

        # Настройка столбцов
        columns = [
            ("id", "ID", 50),
            ("title", "Название книги", 200),
            ("shop", "Магазин", 150),
            ("price", "Цена", 80),
            ("quantity", "Кол-во", 60),
            ("date", "Дата продажи", 120),
            ("stock_id", "ID стока", 80)
        ]

        for col_id, heading, width in columns:
            self.tree.heading(col_id, text=heading)
            self.tree.column(col_id, width=width,
                             anchor="center" if col_id in ("id", "price", "quantity", "stock_id") else "w")

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Привязываем событие выбора
        self.tree.bind("<<TreeviewSelect>>", self._on_sale_selected)

    def _create_controls_frame(self):
        """Создает элементы управления продажами"""
        frame = tk.Frame(self.window)
        frame.pack(fill="x", padx=10, pady=10)

        # Поля для ввода данных
        tk.Label(frame, text="Цена:").grid(row=0, column=0, padx=5)
        self.price_var = tk.DoubleVar()
        self.price_entry = tk.Entry(frame, textvariable=self.price_var, width=10)
        self.price_entry.grid(row=0, column=1, padx=5)

        tk.Label(frame, text="Количество:").grid(row=0, column=2, padx=5)
        self.quantity_var = tk.IntVar(value=1)
        self.quantity_entry = tk.Entry(frame, textvariable=self.quantity_var, width=5)
        self.quantity_entry.grid(row=0, column=3, padx=5)

        # Кнопки управления
        self.add_btn = tk.Button(
            frame,
            text="Добавить продажу",
            command=self._add_sale,
            state="disabled"
        )
        self.add_btn.grid(row=0, column=4, padx=5)

        self.cancel_btn = tk.Button(
            frame,
            text="Отменить продажу",
            command=self._cancel_sale,
            state="disabled",
            fg="red"
        )
        self.cancel_btn.grid(row=0, column=5, padx=5)

    def _load_shops(self):
        """Загружает список магазинов в комбобокс"""
        shops = self.crud.read_shops()
        self.shops = {f"{shop.name} (ID: {shop.id})": shop for shop in shops}
        self.shop_combobox["values"] = list(self.shops.keys())

    def _load_books(self, shop_id=None):
        """Загружает список книг для выбранного магазина"""
        if shop_id is None:
            self.books = {}
            self.book_combobox["values"] = []
            return

        stocks = self.crud.read_stock_by_shop(shop_id)
        self.books = {
            f"{stock.book.title} (ID: {stock.book.id}, в наличии: {stock.count})": stock
            for stock in stocks
        }
        self.book_combobox["values"] = list(self.books.keys())

    def _load_sales(self):
        """Загружает список продаж"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        shop_id = self.selected_shop.id if self.selected_shop else None
        book_id = self.selected_book.id_book if self.selected_book else None

        sales = self.crud.read_sales(shop_id=shop_id, book_id=book_id)

        for sale in sales:
            # Преобразуем datetime в строку с учетом часового пояса
            sale_date = sale.sale_date.replace(tzinfo=None) if sale.sale_date else ""
            date_str = sale_date.strftime("%Y-%m-%d %H:%M") if sale_date else ""

            self.tree.insert("", "end",
                             values=(
                                 sale.id,
                                 sale.stock.book.title,
                                 sale.stock.shop.name,
                                 sale.price,
                                 sale.quantity,
                                 #sale.sale_date.strftime("%Y-%m-%d %H:%M"),
                                 date_str,
                                 sale.id_stock
                             ),
                             tags=("sale",)
                             )

    def _on_shop_selected(self, event):
        """Обработчик выбора магазина"""
        shop_name = self.shop_combobox.get()
        self.selected_shop = self.shops.get(shop_name)
        self._load_books(self.selected_shop.id if self.selected_shop else None)
        self._update_buttons_state()

    def _on_book_selected(self, event):
        """Обработчик выбора книги"""
        book_name = self.book_combobox.get()
        self.selected_book = self.books.get(book_name)
        self._update_buttons_state()
        if self.selected_book:
            self.price_var.set(self._get_default_price())
            self.quantity_var.set(1)

    def _on_sale_selected(self, event):
        """Обработчик выбора продажи"""
        self._update_buttons_state()

    def _update_buttons_state(self):
        """Обновляет состояние кнопок"""
        has_selection = bool(self.tree.selection())
        has_book = bool(self.selected_book)

        self.add_btn.config(state="normal" if has_book else "disabled")
        self.cancel_btn.config(state="normal" if has_selection else "disabled")

    def _get_default_price(self):
        """Возвращает цену по умолчанию для выбранной книги"""
        # Здесь можно реализовать логику определения цены
        # Например, средняя цена последних продаж или фиксированная цена
        return 500.0  # Пример фиксированной цены

    def _add_sale(self):
        """Добавляет новую продажу"""
        if not self.selected_book:
            return

        try:
            price = self.price_var.get()
            quantity = self.quantity_var.get()

            if price <= 0:
                messagebox.showwarning("Ошибка", "Цена должна быть больше 0")
                return

            if quantity <= 0:
                messagebox.showwarning("Ошибка", "Количество должно быть больше 0")
                return

            sale = self.crud.create_sale(
                stock_id=self.selected_book.id,
                price=price,
                quantity=quantity
            )

            messagebox.showinfo("Успех", "Продажа успешно добавлена")
            self._load_sales()
            self._load_books(self.selected_shop.id)

        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить продажу: {e}")

    def _cancel_sale(self):
        """Отменяет выбранную продажу"""
        selected = self.tree.selection()
        if not selected:
            return

        sale_id = self.tree.item(selected[0])["values"][0]

        if not messagebox.askyesno(
                "Подтверждение",
                "Вы уверены, что хотите отменить эту продажу?"
        ):
            return

        try:
            if self.crud.delete_sale(sale_id):
                messagebox.showinfo("Успех", "Продажа отменена")
                self._load_sales()
                self._load_books(self.selected_shop.id)
            else:
                messagebox.showerror("Ошибка", "Не удалось отменить продажу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при отмене продажи: {e}")
