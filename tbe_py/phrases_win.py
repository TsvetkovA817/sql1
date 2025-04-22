# vocabulary
import tkinter as tk
from tkinter import ttk, messagebox
from db_handler import CRUDOperations


class PhrasesManagementWindow:
    def __init__(self, master, db_url, main_window_pos):
        self.master = master
        self.crud = CRUDOperations(db_url)

        # окно на 50 пикселей ниже и правее главного окна
        x = main_window_pos[0] + 50
        y = main_window_pos[1] + 50
        self.master.geometry(f"900x700+{x}+{y}")

        self.setup_ui()
        self.load_phrases()

    def setup_ui(self):
        self.master.title("Управление фразами")

        # Frame для фильтров
        filter_frame = ttk.LabelFrame(self.master, text="Фильтры", padding=10)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        # Поля фильтрации
        ttk.Label(filter_frame, text="ID урока:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.lesson_id_filter = ttk.Entry(filter_frame, width=10)
        self.lesson_id_filter.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)

        ttk.Label(filter_frame, text="Текст (RU):").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        self.text_ru_filter = ttk.Entry(filter_frame)
        self.text_ru_filter.grid(row=0, column=3, padx=5, pady=2, sticky=tk.EW)

        ttk.Label(filter_frame, text="Текст (EN):").grid(row=0, column=4, padx=5, pady=2, sticky=tk.W)
        self.text_en_filter = ttk.Entry(filter_frame)
        self.text_en_filter.grid(row=0, column=5, padx=5, pady=2, sticky=tk.EW)

        ttk.Label(filter_frame, text="Категория:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.category_filter = ttk.Combobox(filter_frame,
                                            values=["", "быт", "работа", "путешествия", "еда", "знакомства"])
        self.category_filter.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)

        # Кнопка применения фильтров
        filter_btn = ttk.Button(filter_frame, text="Применить фильтры", command=self.apply_filters)
        filter_btn.grid(row=2, column=0, columnspan=6, pady=5)

        # Таблица фраз
        self.tree_frame = ttk.Frame(self.master)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("id", "lesson_id", "text_ru", "text_en", "text_zh", "category"),
            show="headings"
        )

        # Столбцы
        columns = [
            ("id", "ID", 50),
            ("lesson_id", "ID урока", 70),
            ("text_ru", "Текст (RU)", 100),
            ("text_en", "Текст (EN)", 100),
            ("text_zh", "Текст (ZH)", 100),
            ("category", "Категория", 100)
        ]

        for col_id, col_text, col_width in columns:
            self.tree.heading(col_id, text=col_text, anchor=tk.W)
            self.tree.column(col_id, width=col_width, stretch=tk.NO if col_width else tk.YES)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Привязка double click for edit
        self.tree.bind("<Double-1>", self.on_double_click)

        # Frame для кнопок CRUD
        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="Добавить", command=self.add_phrase).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Редактировать", command=self.edit_phrase).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_phrase).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Обновить", command=self.load_phrases).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Закрыть", command=self.master.destroy).pack(side=tk.RIGHT, padx=5)

    def load_phrases(self, filters=None):
        """Загрузка фраз в таблицу"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        phrases = self.crud.get_all_phrases()  #  метод в CRUDOperations

        for phrase in phrases:
            self.tree.insert("", tk.END, values=(
                phrase.id,
                phrase.lesson_id,
                phrase.text_ru,
                phrase.text_en,
                phrase.text_zh,
                phrase.category
            ))

    def apply_filters(self):
        """Применение фильтров"""
        lesson_id = self.lesson_id_filter.get().strip()
        text_ru = self.text_ru_filter.get().strip()
        text_en = self.text_en_filter.get().strip()
        category = self.category_filter.get().strip()

        # TODO: реализовать фильтрацию
        # Пока загружаем все фразы
        self.load_phrases()

    def add_phrase(self):
        """Открытие окна добавления фразы"""
        self.phrase_dialog = tk.Toplevel(self.master)
        self.phrase_dialog.title("Добавить фразу")

        self.setup_phrase_form(self.phrase_dialog, None)

    def edit_phrase(self):
        """Редактирование выбранной фразы"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите фразу для редактирования")
            return

        phrase_id = self.tree.item(selected[0], "values")[0]
        phrase = self.crud.get_phrase_by_id(phrase_id)

        if not phrase:
            messagebox.showerror("Ошибка", "Фраза не найдена")
            return

        self.phrase_dialog = tk.Toplevel(self.master)
        self.phrase_dialog.title("Редактировать фразу")

        self.setup_phrase_form(self.phrase_dialog, phrase)

    def on_double_click(self, event):
        """Обработка двойного клика по фразе"""
        self.edit_phrase()

    def setup_phrase_form(self, parent, phrase):
        """Настройка формы фразы (добавление/редактирование)"""
        is_edit = phrase is not None

        # Основные поля
        ttk.Label(parent, text="ID урока:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        lesson_id_entry = ttk.Entry(parent)
        lesson_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(parent, text="Текст (RU):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        text_ru_entry = ttk.Entry(parent)
        text_ru_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(parent, text="Текст (EN):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        text_en_entry = ttk.Entry(parent)
        text_en_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(parent, text="Текст (ZH):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        text_zh_entry = ttk.Entry(parent)
        text_zh_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(parent, text="Категория:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        category_combobox = ttk.Combobox(parent, values=["быт", "работа", "путешествия", "еда", "знакомства"])
        category_combobox.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(parent, text="Пример использования:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        usage_example_text = tk.Text(parent, height=4, width=40)
        usage_example_text.grid(row=5, column=1, padx=5, pady=5, sticky=tk.EW)

        if is_edit:
            lesson_id_entry.insert(0, str(phrase.lesson_id))
            text_ru_entry.insert(0, phrase.text_ru)
            text_en_entry.insert(0, phrase.text_en)
            text_zh_entry.insert(0, phrase.text_zh)
            category_combobox.set(phrase.category)
            usage_example_text.insert("1.0", phrase.usage_example or "")

        # Frame для кнопок
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)

        ttk.Button(
            btn_frame,
            text="Сохранить",
            command=lambda: self.save_phrase(
                phrase.id if is_edit else None,
                lesson_id_entry.get(),
                text_ru_entry.get(),
                text_en_entry.get(),
                text_zh_entry.get(),
                category_combobox.get(),
                usage_example_text.get("1.0", tk.END).strip()
            )
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Отмена",
            command=parent.destroy
        ).pack(side=tk.LEFT, padx=5)

    def save_phrase(self, phrase_id, lesson_id, text_ru, text_en, text_zh, category, usage_example):
        """Сохранение фразы (добавление или обновление)"""
        if not all([lesson_id, text_ru, text_en, text_zh]):
            messagebox.showwarning("Предупреждение", "Заполните все обязательные поля")
            return

        try:
            lesson_id = int(lesson_id)
        except ValueError:
            messagebox.showwarning("Предупреждение", "ID урока должен быть числом")
            return

        try:
            if phrase_id:  # Редактирование
                phrase = self.crud.update_phrase(
                    phrase_id=phrase_id,
                    lesson_id=lesson_id,
                    text_ru=text_ru,
                    text_en=text_en,
                    text_zh=text_zh,
                    category=category,
                    usage_example=usage_example
                )
                messagebox.showinfo("Успех", "Фраза успешно обновлена")
            else:  # Добавление
                phrase = self.crud.create_phrase(
                    lesson_id=lesson_id,
                    text_ru=text_ru,
                    text_en=text_en,
                    text_zh=text_zh,
                    category=category,
                    usage_example=usage_example
                )
                messagebox.showinfo("Успех", "Фраза успешно добавлена")

            self.load_phrases()
            self.phrase_dialog.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить фразу: {str(e)}")

    def delete_phrase(self):
        """Удаление выбранной фразы"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите фразу для удаления")
            return

        phrase_id = self.tree.item(selected[0], "values")[0]

        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту фразу?"):
            return

        try:
            # TODO: В CRUD  нет delete_phrase
            #self.crud.delete_phrase(phrase_id)
            #messagebox.showinfo("Успех", "Фраза успешно удалена")
            messagebox.showinfo("Успех", "Нажата кн удаления фразы")
            self.load_phrases()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить фразу: {str(e)}")


# тест
if __name__ == "__main__":
    root = tk.Tk()
    db_url = "postgresql://postgres:****@localhost/lfl"
    main_window_pos = (100, 100)  # Позиция главного окна
    app = PhrasesManagementWindow(root, db_url, main_window_pos)
    root.mainloop()
