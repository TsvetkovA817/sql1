import tkinter as tk
from tkinter import ttk, messagebox
from db_handler import CRUDOperations


class LessonsManagementWindow:
    def __init__(self, parent, db_url):
        self.master = parent  # win
        self.crud = CRUDOperations(db_url)

        self.setup_ui()
        self.load_lessons()

    def setup_ui(self):
        self.master.title("Управление уроками")
        self.master.geometry("800x600")

        # Frame для фильтров
        filter_frame = ttk.LabelFrame(self.master, text="Фильтры", padding=10)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        # Поля фильтрации
        ttk.Label(filter_frame, text="Название:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.title_filter = ttk.Entry(filter_frame)
        self.title_filter.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)

        ttk.Label(filter_frame, text="Уровень сложности:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.difficulty_filter = ttk.Combobox(filter_frame, values=["", "1", "2", "3", "4", "5"])
        self.difficulty_filter.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)

        # Кнопка применения фильтров
        filter_btn = ttk.Button(filter_frame, text="Применить фильтры", command=self.apply_filters)
        filter_btn.grid(row=2, column=0, columnspan=2, pady=5)

        # Таблица уроков
        self.tree_frame = ttk.Frame(self.master)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("id", "title", "description", "difficulty", "created"),
            show="headings"
        )

        # Настройка столбцов
        self.tree.heading("id", text="ID", anchor=tk.W)
        self.tree.heading("title", text="Название", anchor=tk.W)
        self.tree.heading("description", text="Описание", anchor=tk.W)
        self.tree.heading("difficulty", text="Уровень", anchor=tk.W)
        self.tree.heading("created", text="Дата создания", anchor=tk.W)

        self.tree.column("id", width=50, stretch=tk.NO)
        self.tree.column("title", width=150)
        self.tree.column("description", width=300)
        self.tree.column("difficulty", width=70, stretch=tk.NO)
        self.tree.column("created", width=120, stretch=tk.NO)

        # скролл
        scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # двойной клик
        self.tree.bind("<Double-1>", self.on_double_click)

        # рамка для кнопок CRUD
        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="Добавить", command=self.add_lesson).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Редактировать", command=self.edit_lesson).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_lesson).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Обновить", command=self.load_lessons).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Закрыть", command=self.master.destroy).pack(side=tk.RIGHT, padx=5)

    def load_lessons(self, filters=None):
        """Загрузка уроков в таблицу"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        lessons = self.crud.get_all_lessons()

        for lesson in lessons:
            self.tree.insert("", tk.END, values=(
                lesson.id,
                lesson.title,
                lesson.description,
                lesson.difficulty_level,
                lesson.create_date.strftime("%Y-%m-%d %H:%M") if lesson.create_date else ""
            ))

    def apply_filters(self):
        """Применение фильтров"""
        title = self.title_filter.get().strip()
        difficulty = self.difficulty_filter.get().strip()

        # TODO: Здесь добавить логику фильтрации
        # Пока просто загружаем все уроки
        self.load_lessons()

    def add_lesson(self):
        """Открытие окна добавления урока"""
        self.lesson_dialog = tk.Toplevel(self.master)
        self.lesson_dialog.title("Добавить урок")

        self.setup_lesson_form(self.lesson_dialog, None)

    def edit_lesson(self):
        """Редактирование выбранного урока"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите урок для редактирования")
            return

        lesson_id = self.tree.item(selected[0], "values")[0]
        lesson = self.crud.get_lesson_by_id(lesson_id)

        if not lesson:
            messagebox.showerror("Ошибка", "Урок не найден")
            return

        self.lesson_dialog = tk.Toplevel(self.master)
        self.lesson_dialog.title("Редактировать урок")

        self.setup_lesson_form(self.lesson_dialog, lesson)

    def on_double_click(self, event):
        """двойной клик по уроку"""
        self.edit_lesson()

    def setup_lesson_form(self, parent, lesson):
        """Форма урока (добавление/редактирование)"""
        is_edit = lesson is not None

        ttk.Label(parent, text="Название:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        title_entry = ttk.Entry(parent, width=40)
        title_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(parent, text="Описание:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        desc_entry = tk.Text(parent, width=40, height=5)
        desc_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(parent, text="Уровень сложности:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        difficulty_entry = ttk.Combobox(parent, values=[1, 2, 3, 4, 5])
        difficulty_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        if is_edit:
            title_entry.insert(0, lesson.title)
            desc_entry.insert("1.0", lesson.description or "")
            difficulty_entry.set(lesson.difficulty_level)

        # Frame для кнопок
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(
            btn_frame,
            text="Сохранить",
            command=lambda: self.save_lesson(
                lesson.id if is_edit else None,
                title_entry.get(),
                desc_entry.get("1.0", tk.END).strip(),
                difficulty_entry.get()
            )
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Отмена",
            command=parent.destroy
        ).pack(side=tk.LEFT, padx=5)

    def save_lesson(self, lesson_id, title, description, difficulty):
        """Сохранение урока (добавление или обновление)"""
        if not title:
            messagebox.showwarning("Предупреждение", "Введите название урока")
            return

        try:
            difficulty = int(difficulty) if difficulty else 1
        except ValueError:
            difficulty = 1

        if lesson_id:  # Редактирование
            lesson = self.crud.update_lesson(
                lesson_id=lesson_id,
                title=title,
                description=description,
                difficulty_level=difficulty
            )
            messagebox.showinfo("Успех", "Урок успешно обновлен")
        else:  # Добавление
            lesson = self.crud.create_lesson(
                title=title,
                description=description,
                difficulty_level=difficulty
            )
            messagebox.showinfo("Успех", "Урок успешно добавлен")

        self.load_lessons()
        self.lesson_dialog.destroy()

    def delete_lesson(self):
        """Удаление выбранного урока"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите урок для удаления")
            return

        lesson_id = self.tree.item(selected[0], "values")[0]

        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить этот урок?"):
            return

        #  TODO:  Здесь должна быть проверка на связанные записи (фразы, прогресс)
        # Для простоты пока так
        try:
            #  TODO:  В CRUD нет метода delete_lesson, сделать
            #  self.crud.delete_lesson(lesson_id)
            messagebox.showinfo("Успех", "Нажали кнопку удалить урок")
            self.load_lessons()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить урок: {str(e)}")


# тест
if __name__ == "__main__":
    root = tk.Tk()
    db_url = "postgresql://postgres:****@localhost/lfl"
    app = LessonsManagementWindow(root, db_url)
    root.mainloop()
