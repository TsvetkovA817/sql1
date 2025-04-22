import threading
import random
import logging
import time
from telebot import types, TeleBot, custom_filters, util
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from sqlalchemy import func
from datetime import datetime, timezone

from db_handler import CRUDOperations
from models import User, Phrase, UserWord, Lesson
from language_handler import LanguageHandler


class LanguageBot:
    def __init__(self, token, db_url):
        self.token = token
        self.db_url = db_url
        self.bot = None
        self.polling_thread = None
        self.is_running = False

        self.crud = CRUDOperations(db_url)
        self.known_users = []
        self.user_steps = {}
        self.current_buttons = []
        self.lang = LanguageHandler()
        # self.ui_lang = self.lang.current_lang
        self.Command = self._init_commands(ui_lang=self.lang.current_lang)

        #self.bot = TeleBot(token, state_storage=StateMemoryStorage())
        #self.setup_handlers()
        #self.bot.add_custom_filter(custom_filters.StateFilter(self.bot))

    def start_bot(self):
        """Запускает бота в отдельном потоке"""
        if self.is_running:
            return "Бот уже запущен"

        self.bot = TeleBot(self.token, state_storage=StateMemoryStorage())
        self.setup_handlers()
        self.bot.add_custom_filter(custom_filters.StateFilter(self.bot))

        self.is_running = True
        self.polling_thread = threading.Thread(target=self._start_polling)
        self.polling_thread.start()

        return "Бот успешно запущен"

    def _start_polling(self):
        """Внутренний метод для запуска polling в отдельном потоке"""
        while self.is_running:
            try:
                self.bot.infinity_polling(skip_pending=True)
            except Exception as e:
                print(f"Ошибка в работе бота: {e}")
                time.sleep(5)
                if self.is_running:
                    continue
                else:
                    break

    def stop_bot(self):
        """Останавливает работу бота"""
        if not self.is_running:
            return "Бот уже остановлен"
        try:
            if self.bot:
                self.bot.stop_polling()
        except Exception as e:
            self.logger.error(f"Ошибка при остановке polling: {e}")


        if self.polling_thread and self.polling_thread.is_alive():
            self.polling_thread.join(timeout=5)

        self.is_running = False
        self.bot = None
        return "Бот успешно остановлен"

    def get_bot_status(self):
        """Возвращает статус бота"""
        return "Бот работает" if self.is_running else "Бот остановлен"

    class MyStates(StatesGroup):
        target_word = State()
        translate_word = State()
        another_words = State()
        select_lesson = State()
        select_target_language = State()
        select_ui_language = State()
        learning_mode = State()

    class Command:
        ADD_WORD = 'Добавить слово ➕'
        DELETE_WORD = 'Удалить слово 🔙'
        NEXT = 'Дальше ⏭'
        SELECT_LESSON = 'Выбрать урок 📚'
        SELECT_TARGET_LANG = 'Изменить изучаемый язык 🌐'
        SELECT_UI_LANG = 'Изменить язык интерфейса 🖥️'
        MAIN_MENU = 'Главное меню 🏠'

    def _init_commands(self, ui_lang = 'ru'):
        """ Инициализирует кнопки с учетом текущего языка """
        cmd = self.Command
        cmd.ADD_WORD = f'{self.lang.get_text("bot_add_word",lang=ui_lang)} ➕'
        cmd.DELETE_WORD = f'{self.lang.get_text("bot_delete_word",lang=ui_lang)} 🔙'
        cmd.NEXT = f'{self.lang.get_text("bot_next",lang=ui_lang)} ⏭'
        cmd.SELECT_LESSON = f'{self.lang.get_text("bot_select_lesson",lang=ui_lang)} 📚'
        cmd.SELECT_TARGET_LANG = f'{self.lang.get_text("bot_select_target_lang",lang=ui_lang)} 🌐'
        cmd.SELECT_UI_LANG = f'{self.lang.get_text("bot_select_ui_lang",lang=ui_lang)} 🖥️'
        cmd.MAIN_MENU = f'{self.lang.get_text("bot_main_menu",lang=ui_lang)} 🏠'
        return cmd

    def setup_handlers(self):
        """Настройка обработчиков команд"""
        @self.bot.message_handler(commands=['start', 'menu'])
        def handle_start(message):
            self.show_main_menu(message)

        @self.bot.message_handler(func=lambda message: message.text == self.Command.NEXT)
        def handle_next(message):
            self.create_cards(message)

        @self.bot.message_handler(func=lambda message: message.text == self.Command.DELETE_WORD)
        def handle_delete_word(message):
            self.delete_word(message)

        @self.bot.message_handler(func=lambda message: message.text == self.Command.ADD_WORD)
        def handle_add_word(message):
            self.add_word(message)

        @self.bot.message_handler(func=lambda message: message.text == self.Command.SELECT_LESSON)
        def handle_select_lesson(message):
            self.select_lesson(message)

        @self.bot.message_handler(func=lambda message: message.text == self.Command.SELECT_TARGET_LANG)
        def handle_select_target_lang(message):
            self.select_target_language(message)

        @self.bot.message_handler(func=lambda message: message.text == self.Command.SELECT_UI_LANG)
        def handle_select_ui_lang(message):
            self.select_ui_language(message)

        @self.bot.message_handler(func=lambda message: message.text == self.Command.MAIN_MENU)
        def handle_main_menu(message):
            self.show_main_menu(message)

        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            # Обработка выбора урока
            if self.bot.get_state(message.from_user.id, message.chat.id) == self.MyStates.select_lesson:
                self.handle_lesson_selection(message)
                return
            # ... обработка других команд ...

            self.handle_user_response(message)

    def show_main_menu(self, message):
        """Показывает главное меню с кнопками управления"""
        cid = message.chat.id
        user_id = message.from_user.id
        lang = self.get_user_lang(user_id) # Получаем язык пользователя из БД
        #self.ui_lang = lang
        commands = self._init_commands(ui_lang=lang) # Создаем команды с нужным языком

        # Отправляем меню
        markup = types.ReplyKeyboardMarkup(row_width=2)
        status = self.get_bot_status()

        buttons = [
            types.KeyboardButton(commands.SELECT_LESSON),
            types.KeyboardButton(commands.SELECT_TARGET_LANG),
            types.KeyboardButton(commands.SELECT_UI_LANG),
            types.KeyboardButton(commands.ADD_WORD),
            types.KeyboardButton(commands.NEXT)
        ]

        markup.add(*buttons)

        self.bot.send_message(
            message.chat.id,
            f"{status}\n{self.lang.get_text('bot_main_menu', lang=lang)}",
            reply_markup=markup
        )

        with self.crud.Session() as session:
            # нашли юзера
            user = session.query(User).filter(User.telegram_id == str(cid)).first()
            # не нашли
            if not user:
                user = User(
                    telegram_id=str(cid),
                    username=message.from_user.username,
                    ui_language='ru',
                    target_language='en',
                    current_lesson_id=None  # Инициализируем текущий урок
                )
                session.add(user)
                session.commit()
                #welcome_msg = "Добро пожаловать! Я помогу вам изучать языки.\n Главное меню"
                welcome_msg = f"{self.lang.get_text('bot_first_msg', lang=lang)}"
            else:
                welcome_msg = f"{self.lang.get_text('bot_welcome_msg', lang=lang)}"

            # Получаем информацию о текущем уроке
            current_lesson = None
            if user.current_lesson_id:
                current_lesson = session.query(Lesson).filter(Lesson.id == user.current_lesson_id).first()

            word_count = session.query(UserWord).filter(UserWord.user_id == user.id).count()
            welcome_msg += f"\n\n{self.lang.get_text('bot_user_dict', lang=lang)} {word_count} {self.lang.get_text('words', lang=lang)}"
            welcome_msg += f"\n{self.lang.get_text('target_language', lang=lang)} {user.target_language}"
            if current_lesson:
                welcome_msg += f"\n{self.lang.get_text('current_lesson', lang=lang)} {current_lesson.title}"
            else:
                welcome_msg += f"\n{self.lang.get_text('no_lesson_selected', lang=lang)}"
            # отсылаем стартовое сообщение
            self.bot.send_message(
                cid,
                welcome_msg,
                reply_markup=markup
            )

    def select_lesson(self, message):
        cid = message.chat.id
        user_id = message.from_user.id
        lang = self.get_user_lang(user_id)

        with self.crud.Session() as session:
            # Получаем текущего пользователя
            user = session.query(User).filter(User.telegram_id == str(cid)).first()
            if not user:
                self.show_main_menu(message)
                return

            lessons = session.query(Lesson).all()

            if not lessons:
                self.bot.send_message(
                    cid,
                    f"{self.lang.get_text('no_lessons_available', lang=lang)}",
                    reply_markup=self.get_main_menu_markup()
                )
                return

            markup = types.ReplyKeyboardMarkup(row_width=1)
            for lesson in lessons:
                # Помечаем текущий выбранный урок
                if user.current_lesson_id == lesson.id:
                    btn_text = f"✓ {lesson.id}: {lesson.title}"
                else:
                    btn_text = f"{lesson.id}: {lesson.title}"
                markup.add(types.KeyboardButton(btn_text))
            markup.add(types.KeyboardButton(self.Command.MAIN_MENU))

            self.bot.send_message(
                cid,
                f"{self.lang.get_text('select_lesson_prompt', lang=lang)}",
                reply_markup=markup
            )
            self.bot.set_state(message.from_user.id, self.MyStates.select_lesson, message.chat.id)

    def handle_lesson_selection(self, message):
        cid = message.chat.id
        user_id = message.from_user.id
        lang = self.get_user_lang(user_id)
        text = message.text

        if text == self.Command.MAIN_MENU:
            self.show_main_menu(message)
            return

        try:
            # Извлекаем ID урока из текста (формат "ID: Название")
            lesson_id = int(text.split(':')[0].replace('✓', '').strip())

            with self.crud.Session() as session:
                # Обновляем текущий урок пользователя
                user = session.query(User).filter(User.telegram_id == str(cid)).first()
                if user:
                    user.current_lesson_id = lesson_id
                    session.commit()

                    # Получаем название урока для сообщения
                    lesson = session.query(Lesson).filter(Lesson.id == lesson_id).first()
                    lesson_title = lesson.title if lesson else f"{self.lang.get_text('unknown_lesson', lang=lang)}"

                    self.bot.send_message(
                        cid,
                        f"{self.lang.get_text('lesson_selected', lang=lang)} {lesson_title}",
                        reply_markup=self.get_main_menu_markup()
                    )
                else:
                    self.bot.send_message(
                        cid,
                        f"{self.lang.get_text('user_not_found', lang=lang)}",
                        reply_markup=self.get_main_menu_markup()
                    )
        except ValueError:
            self.bot.send_message(
                cid,
                f"{self.lang.get_text('select_lesson_from_list', lang=lang)}",
                reply_markup=self.get_main_menu_markup()
            )

    def create_cards(self, message):
        """Создает карточки для изучения слов из текущего урока"""
        cid = message.chat.id
        user_id = message.from_user.id
        lang = self.get_user_lang(user_id)
        # Устанавливаем состояние перед началом
        self.bot.set_state(user_id, self.MyStates.learning_mode, cid)

        with self.crud.Session() as session:
            user = session.query(User).filter(User.telegram_id == str(cid)).first()
            if not user:
                self.show_main_menu(message)
                return

            # user_words = session.query(UserWord).filter(UserWord.user_id == user.id).all()
            #
            # if not user_words:
            #     self.bot.send_message(
            #         cid,
            #         "Ваш словарь пуст. Выберите урок или добавьте слова вручную.",
            #         reply_markup=self.get_main_menu_markup()
            #     )
            #     return

            # Получаем слова для изучения в зависимости от выбранного урока
            if user.current_lesson_id:
                # Берем только слова из текущего урока, которые есть у пользователя
                user_words = session.query(UserWord) \
                    .join(Phrase, UserWord.phrase_id == Phrase.id) \
                    .filter(
                    UserWord.user_id == user.id,
                    Phrase.lesson_id == user.current_lesson_id
                ) \
                    .all()

                if not user_words:
                    self.bot.send_message(
                        cid,
                        f"{self.lang.get_text('no_words_in_lesson', lang=lang)}",
                        reply_markup=self.get_main_menu_markup()
                    )
                    return
            else:
                # Берем все слова пользователя, если урок не выбран
                user_words = session.query(UserWord) \
                    .filter(UserWord.user_id == user.id) \
                    .all()

                if not user_words:
                    self.bot.send_message(
                        cid,
                        f"{self.lang.get_text('empty_dictionary', lang=lang)}",
                        reply_markup=self.get_main_menu_markup()
                    )
                    return

            word_to_learn = random.choice(user_words)
            phrase = session.query(Phrase).filter(Phrase.id == word_to_learn.phrase_id).first()

            translate = getattr(phrase, f"text_{user.ui_language}")
            target_word = getattr(phrase, f"text_{user.target_language}")

            # other_phrases = session.query(Phrase) \
            #     .filter(Phrase.id != phrase.id) \
            #     .order_by(func.random()) \
            #     .limit(3) \
            #     .all()

            # Получаем другие варианты ответов из того же набора слов
            other_words = random.sample(
                [uw for uw in user_words if uw.phrase_id != phrase.id],
                min(3, len(user_words) - 1)
            )
            other_phrases = session.query(Phrase) \
                .filter(Phrase.id.in_([uw.phrase_id for uw in other_words])) \
                .all()

            others = [getattr(p, f"text_{user.target_language}") for p in other_phrases]

        markup = types.ReplyKeyboardMarkup(row_width=2)
        buttons = [types.KeyboardButton(target_word)]
        buttons.extend([types.KeyboardButton(word) for word in others])
        random.shuffle(buttons)

        # Добавляем основные кнопки
        # TODO: переделать кнопки
        buttons.extend([
            types.KeyboardButton(self.Command.NEXT),
            types.KeyboardButton(self.Command.ADD_WORD),
            types.KeyboardButton(self.Command.DELETE_WORD),
            types.KeyboardButton(self.Command.MAIN_MENU)
        ])

        markup.add(*buttons)

        with self.bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['target_word'] = target_word
            data['translate_word'] = translate
            data['other_words'] = others
            data['phrase_id'] = phrase.id
            data['user_id'] = user.id  #  ID пользователя

        self.bot.send_message(
            cid,
            f"{self.lang.get_text('select_translation')}\n{translate}",
            reply_markup=markup
        )


    def get_main_menu_markup(self):
        markup = types.ReplyKeyboardMarkup(row_width=2)
        # TODO: переделать кнопки
        buttons = [
            types.KeyboardButton(self.Command.SELECT_LESSON),
            types.KeyboardButton(self.Command.SELECT_TARGET_LANG),
            types.KeyboardButton(self.Command.SELECT_UI_LANG),
            types.KeyboardButton(self.Command.ADD_WORD),
            types.KeyboardButton(self.Command.NEXT)
        ]
        markup.add(*buttons)
        return markup

    # def select_lesson(self, message):
    #     cid = message.chat.id
    #
    #     with self.crud.Session() as session:
    #         lessons = session.query(Lesson).all()
    #
    #         if not lessons:
    #             self.bot.send_message(
    #                 cid,
    #                 "Нет доступных уроков.",
    #                 reply_markup=self.get_main_menu_markup()
    #             )
    #             return
    #
    #         markup = types.ReplyKeyboardMarkup(row_width=1)
    #         for lesson in lessons:
    #             markup.add(types.KeyboardButton(f"{lesson.id}: {lesson.title}"))
    #         markup.add(types.KeyboardButton(self.Command.MAIN_MENU))
    #
    #         self.bot.send_message(
    #             cid,
    #             "Выберите урок:",
    #             reply_markup=markup
    #         )
    #         self.bot.set_state(message.from_user.id, self.MyStates.select_lesson, message.chat.id)

    def select_target_language(self, message):
        cid = message.chat.id
        markup = types.ReplyKeyboardMarkup(row_width=2)

        buttons = [
            types.KeyboardButton("Английский 🇬🇧"),
            types.KeyboardButton("Китайский 🇨🇳"),
            types.KeyboardButton(self.Command.MAIN_MENU)
        ]
        markup.add(*buttons)

        self.bot.send_message(
            cid,
            f"{self.lang.get_text('select_target_language')}",
            reply_markup=markup
        )
        self.bot.set_state(message.from_user.id, self.MyStates.select_target_language, message.chat.id)

    def select_ui_language(self, message):
        cid = message.chat.id
        markup = types.ReplyKeyboardMarkup(row_width=2)

        buttons = [
            types.KeyboardButton("Русский 🇷🇺"),
            types.KeyboardButton("Английский 🇬🇧"),
            types.KeyboardButton("Китайский 🇨🇳"),
            types.KeyboardButton(self.Command.MAIN_MENU)
        ]
        markup.add(*buttons)

        self.bot.send_message(
            cid,
            f"{self.lang.get_text('select_ui_language')}",
            reply_markup=markup
        )
        self.bot.set_state(message.from_user.id, self.MyStates.select_ui_language, message.chat.id)

    def add_word(self, message):
        cid = message.chat.id

        with self.crud.Session() as session:
            user = session.query(User).filter(User.telegram_id == str(cid)).first()

            # Получаем случайную фразу, которой нет у пользователя
            user_phrase_ids = [uw.phrase_id for uw in session.query(UserWord)
                .filter(UserWord.user_id == user.id).all()]

            phrase = session.query(Phrase) \
                .filter(~Phrase.id.in_(user_phrase_ids)) \
                .order_by(func.random()) \
                .first()

            if not phrase:
                self.bot.send_message(
                    cid,
                    f"{self.lang.get_text('all_words_added')}",
                    reply_markup=self.get_main_menu_markup()
                )
                return

            # Добавляем слово в словарь пользователя
            user_word = UserWord(
                user_id=user.id,
                phrase_id=phrase.id,
                last_review=datetime.now(timezone.utc)
            )
            session.add(user_word)
            session.commit()

            # Показываем добавленное слово
            word = getattr(phrase, f"text_{user.ui_language}")
            self.bot.send_message(
                cid,
                f"{self.lang.get_text('new_word_added')} {word}",
                reply_markup=self.get_main_menu_markup()
            )

    def delete_word(self, message):
        cid = message.chat.id

        with self.bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if 'phrase_id' not in data:
                self.bot.send_message(
                    cid,
                    f"{self.lang.get_text('word_not_found')}",
                    reply_markup=self.get_main_menu_markup()
                )
                return

            with self.crud.Session() as session:
                user = session.query(User).filter(User.telegram_id == str(cid)).first()
                session.query(UserWord) \
                    .filter(UserWord.user_id == user.id, UserWord.phrase_id == data['phrase_id']) \
                    .delete()
                session.commit()

                self.bot.send_message(
                    cid,
                    f"{self.lang.get_text('word_deleted')}",
                    reply_markup=self.get_main_menu_markup()
                )

    def handle_user_response(self, message):
        cid = message.chat.id
        user_id = message.from_user.id
        text = message.text

        current_state = self.bot.get_state(message.from_user.id, message.chat.id)
        print(f"Current state: {current_state}")

        # Обработка выбора урока
        if current_state == self.MyStates.select_lesson.name:
            if text == self.Command.MAIN_MENU:
                self.show_main_menu(message)
                return

            try:
                lesson_id = int(text.split(':')[0])
                with self.crud.Session() as session:
                    user = session.query(User).filter(User.telegram_id == str(cid)).first()
                    lesson = session.query(Lesson).filter(Lesson.id == lesson_id).first()

                    if lesson:
                        phrases = session.query(Phrase).filter(Phrase.lesson_id == lesson_id).all()
                        added = 0
                        for phrase in phrases:
                            # Проверяем, есть ли уже это слово у пользователя
                            exists = session.query(UserWord) \
                                .filter(UserWord.user_id == user.id, UserWord.phrase_id == phrase.id) \
                                .first()
                            if not exists:
                                user_word = UserWord(
                                    user_id=user.id,
                                    phrase_id=phrase.id,
                                    last_review=datetime.now(timezone.utc)
                                )
                                session.add(user_word)
                                added += 1

                        session.commit()
                        self.bot.send_message(
                            cid,
                            f"{self.lang.get_text('added_count')} {added} \
                                {self.lang.get_text('words_from_lesson')} '{lesson.title}'",
                            reply_markup=self.get_main_menu_markup()
                        )
                    else:
                        self.bot.send_message(
                            cid,
                            f"{self.lang.get_text('lesson_not_found')}",
                            reply_markup=self.get_main_menu_markup()
                        )
            except ValueError:
                self.bot.send_message(
                    cid,
                    f"{self.lang.get_text('select_lesson_from_list')}",
                    reply_markup=self.get_main_menu_markup()
                )
            return

        # Обработка выбора изучаемого языка
        elif current_state == self.MyStates.select_target_language.name:
            if text == self.Command.MAIN_MENU:
                self.show_main_menu(message)
                return

            lang_map = {
                "Английский 🇬🇧": "en",
                "Китайский 🇨🇳": "zh"
            }

            if text in lang_map:
                with self.crud.Session() as session:
                    user = session.query(User).filter(User.telegram_id == str(cid)).first()
                    user.target_language = lang_map[text]
                    session.commit()

                    self.bot.send_message(
                        cid,
                        f"{self.lang.get_text('now_learning')} {text}",
                        reply_markup=self.get_main_menu_markup()
                    )
            else:
                self.bot.send_message(
                    cid,
                    f"{self.lang.get_text('select_lesson_from_list')}",
                    reply_markup=self.get_main_menu_markup()
                )
            return

        # Обработка выбора языка интерфейса
        elif current_state == self.MyStates.select_ui_language.name:
            if text == self.Command.MAIN_MENU:
                self.show_main_menu(message)
                return

            lang_map = {
                "Русский 🇷🇺": "ru",
                "Английский 🇬🇧": "en",
                "Китайский 🇨🇳": "zh"
            }

            if text in lang_map:
                with self.crud.Session() as session:
                    user = session.query(User).filter(User.telegram_id == str(cid)).first()
                    user.ui_language = lang_map[text]
                    session.commit()

                    user_id = message.from_user.id
                    lang = self.get_user_lang(user_id)
                    self.ui_lang = lang
                    self.Command = self._init_commands()
                    self.show_main_menu(message)
                    self.bot.send_message(
                        cid,
                        f"Язык интерфейса изменен на: {text}",
                        reply_markup=self.get_main_menu_markup()
                    )
            else:
                self.bot.send_message(
                    cid,
                    f"{self.lang.get_text('select_lesson_from_list')}",
                    reply_markup=self.get_main_menu_markup()
                )
            return

        # Обработка основного режима карточек
        if current_state != self.MyStates.learning_mode.name:
            self.show_main_menu(message)
            return
        # Получаем данные
        with self.bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if not data:
                self.bot.send_message(cid, "Сессия устарела, начинаем заново")
                self.create_cards(message)
                return
            if 'target_word' not in data:
                self.show_main_menu(message)
                return

            target_word = data['target_word']
            markup = types.ReplyKeyboardMarkup(row_width=2)

            if text == target_word:
                # Обновляем прогресс изучения слова
                with self.crud.Session() as session:
                    user = session.query(User).filter(User.telegram_id == str(cid)).first()
                    user_word = session.query(UserWord) \
                        .filter(UserWord.user_id == user.id, UserWord.phrase_id == data['phrase_id']) \
                        .first()

                    if user_word:
                        user_word.repetition_count += 1
                        user_word.last_review = datetime.now(timezone.utc)
                        session.commit()

                hint = f"Правильно! ✅\n{target_word} -> {data['translate_word']}"
                buttons = [
                    types.KeyboardButton(self.Command.NEXT),
                    types.KeyboardButton(self.Command.ADD_WORD),
                    types.KeyboardButton(self.Command.DELETE_WORD),
                    types.KeyboardButton(self.Command.MAIN_MENU)
                ]
            else:
                hint = f"Неверно! ❌\nПравильный ответ: {data['translate_word']} -> {target_word}"
                buttons = [
                    types.KeyboardButton(self.Command.NEXT),
                    types.KeyboardButton(self.Command.MAIN_MENU)
                ]

            markup.add(*buttons)
            self.bot.send_message(cid, hint, reply_markup=markup)

    def get_user_lang(self, user_id):
        """Получаем язык пользователя из БД"""
        with self.crud.Session() as session:
            user = session.query(User).filter(User.telegram_id == str(user_id)).first()
            return user.ui_language if user else 'ru'


    def run(self):
        print('Бот запущен...')
        self.bot.infinity_polling(skip_pending=True)

# тест
if __name__ == '__main__':
    TOKEN = '****'
    DB_URL = 'postgresql://postgres:****@localhost/lfl'

    bot = LanguageBot(TOKEN, DB_URL)
    #bot.run()
    # Запуск бота
    print(bot.start_bot())

    # Проверка статуса
    print(bot.get_bot_status())

    # Остановка бота через 60 секунд
    #time.sleep(60)
    #print(bot.stop_bot())