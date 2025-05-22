import threading
import random
import logging
import time
from telebot import types, TeleBot, custom_filters, util
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from sqlalchemy import func
from datetime import datetime, timezone
from typing import Optional, Dict, List, Union, Tuple

from db_handler import CRUDOperations
from models import User, Phrase, UserWord, Lesson
from language_handler import LanguageHandler

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LanguageBot:
    def __init__(self, token: str, db_url: str):
        self.token = token
        self.db_url = db_url
        self.bot: Optional[TeleBot] = None
        self.polling_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.shutdown_event = threading.Event()
        # self.crud = CRUDOperations(db_url)
        self.known_users = []
        self.user_steps = {}
        self.current_buttons = []
        try:
            self.crud = CRUDOperations(db_url)
            self.lang = LanguageHandler()
            self.Command = self._init_commands(ui_lang=self.lang.current_lang)  # Язык по умолчанию
            self.user_cache: Dict[int, Dict] = {}  # Кэш данных пользователей
            logger.info("LanguageBot Запустился успешно")
        except Exception as e:
            logger.error(f"LanguageBot Ошибка инициализации: {str(e)}")
            raise

        # self.bot = TeleBot(token, state_storage=StateMemoryStorage())
        # self.setup_handlers()
        # self.bot.add_custom_filter(custom_filters.StateFilter(self.bot))

    class MyStates(StatesGroup):
        target_word = State()
        translate_word = State()
        another_words = State()
        select_lesson = State()
        select_target_language = State()
        select_ui_language = State()
        learning_mode = State()

    def start_bot(self):
        """Запускает бота в отдельном потоке"""
        if self.is_running:
            msg1 = "Бот уже запущен"
            logger.warning(msg1)
            return msg1
        msg2 = 'Бот успешно запущен'
        try:
            self.bot = TeleBot(self.token, state_storage=StateMemoryStorage())
            self.setup_handlers()
            self.bot.add_custom_filter(custom_filters.StateFilter(self.bot))

            self.is_running = True
            self.shutdown_event.clear()
            self.polling_thread = threading.Thread(target=self._start_polling)
            self.polling_thread.start()
            logger.info(msg2)
            return msg2
        except Exception as e:
            logger.error(f"Ошибка при старте бота: {str(e)}")
            return f"Ошибка при старте бота: {str(e)}"

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

    def stop_bot(self) -> str:
        """Останавливает работу бота"""
        msg_bot_stopped = 'Бот уже остановлен'
        msg_bot_ok_stopped = 'Бот успешно остановлен'
        if not self.is_running:
            logger.warning(msg_bot_stopped)
            return msg_bot_stopped
        try:
            self.is_running = False
            self.shutdown_event.set()
            if self.bot:
                try:
                    self.bot.stop_polling()
                except Exception as e:
                    logger.error(f"Ошибка стоп бот polling: {str(e)}")
            if self.polling_thread and self.polling_thread.is_alive():
                self.polling_thread.join(timeout=5)
            self.bot = None
            logger.info(msg_bot_ok_stopped)
            return msg_bot_ok_stopped
        except Exception as e:
            logger.error(f"Ошибка при остановке: {str(e)}")
            return f"Ошибка: {str(e)}"

    def get_bot_status(self):
        """Возвращает статус бота"""
        return "Бот работает" if self.is_running else "Бот остановлен"

    class Command:
        ADD_WORD = 'Добавить слово ➕'
        DELETE_WORD = 'Удалить слово 🔙'
        NEXT = 'Дальше ⏭'
        SELECT_LESSON = 'Выбрать урок 📚'
        SELECT_TARGET_LANG = 'Изменить изучаемый язык 🌐'
        SELECT_UI_LANG = 'Изменить язык интерфейса 🖥️'
        MAIN_MENU = 'Главное меню 🏠'

    def _init_commands(self, ui_lang='ru'):
        """ Инициализирует кнопки с учетом текущего языка """
        cmd = self.Command
        cmd.ADD_WORD = f'{self.lang.get_text("bot_add_word", lang=ui_lang)} ➕'
        cmd.DELETE_WORD = f'{self.lang.get_text("bot_delete_word", lang=ui_lang)} 🔙'
        cmd.NEXT = f'{self.lang.get_text("bot_next", lang=ui_lang)} ⏭'
        cmd.SELECT_LESSON = f'{self.lang.get_text("bot_select_lesson", lang=ui_lang)} 📚'
        cmd.SELECT_TARGET_LANG = f'{self.lang.get_text("bot_select_target_lang", lang=ui_lang)} 🌐'
        cmd.SELECT_UI_LANG = f'{self.lang.get_text("bot_select_ui_lang", lang=ui_lang)} 🖥️'
        cmd.MAIN_MENU = f'{self.lang.get_text("bot_main_menu", lang=ui_lang)} 🏠'
        return cmd

    def setup_handlers(self):
        """Настройка обработчиков команд"""

        @self.bot.message_handler(commands=['start', 'menu', 'help'])
        def handle_start(message: types.Message) -> None:
            try:
                self.show_main_menu(message)
            except Exception as e:
                logger.error(f"Ошибка: {str(e)}")
                self._send_error_message(message.chat.id)

        @self.bot.message_handler(func=lambda message: message.text == self.Command.NEXT)
        def handle_next(message: types.Message) -> None:
            try:
                # self.create_cards(message)
                self.create_learning_card(message)
            except Exception as e:
                logger.error(f"Ошибка: {str(e)}")
                self._send_error_message(message.chat.id)

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

    def show_main_menu(self, message: types.Message) -> None:
        """Показывает главное меню с кнопками управления"""
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id

            # Получаем или создаем пользователя через CRUDOperations
            user, error = self.crud.get_or_create_user(
                telegram_id=str(user_id),
                username=message.from_user.username,
                ui_language='ru',
                target_language='en'
            )

            if error or not user:
                self._send_error_message(chat_id)
                return

            # Обновляем кэш пользователя
            self.user_cache[user_id] = {
                'ui_language': user.ui_language,
                'target_language': user.target_language,
                'current_lesson_id': user.current_lesson_id
            }

            # Получаем статистику пользователя через CRUDOperations
            stats, error = self.crud.get_user_stats(user.id)
            if error:
                stats = {'word_count': 0, 'learned_words': 0}

            # Формируем сообщение
            welcome_msg = self._format_welcome_message(user, stats)

            # Отправляем меню
            self.bot.send_message(
                chat_id,
                welcome_msg,
                reply_markup=self._get_main_menu_markup(user.ui_language)
            )
        except Exception as e:
            logger.error(f"Error in show_main_menu: {str(e)}")
            self._send_error_message(message.chat.id)

    def create_learning_card(self, message: types.Message, chat_id: int = 0, user_id: int = 0) -> None:
        """Создает карточку для изучения слов"""
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id
            lang = self._get_user_lang_from_cache(user_id) or 'ru'

            # Получаем пользователя
            user, error = self.crud.get_user_by_telegram_id(str(user_id))
            if error or not user:
                self._send_error_message(chat_id)
                return

            # Получаем данные для обучения
            learning_data, error = self.crud.get_learning_data(
                user_id=user.id,
                lesson_id=user.current_lesson_id
            )

            if error or not learning_data:
                error_msg = self.lang.get_text(
                    'no_words_to_learn' if not learning_data else 'database_error',
                    lang=lang
                )
                self.bot.send_message(chat_id, error_msg)
                return

            # Получаем данные фразы
            current_phrase = learning_data['current_phrase']
            other_phrases = learning_data['other_phrases']

            # Формируем данные карточки
            card_data = {
                'target_word': current_phrase[f"text_{user.target_language}"],
                'translate_word': current_phrase[f"text_{user.ui_language}"],
                'other_words': [p[f"text_{user.target_language}"] for p in other_phrases],
                'phrase_id': current_phrase['id'],
                'user_id': user.id
            }

            # Создаем варианты ответов
            answer_buttons = self._generate_answer_options(
                card_data['target_word'],
                card_data['other_words']
            )

            # Добавляем основные кнопки
            commands = self._init_commands(ui_lang=lang)
            action_buttons = [
                types.KeyboardButton(commands.NEXT),
                types.KeyboardButton(commands.ADD_WORD),
                types.KeyboardButton(commands.DELETE_WORD),
                types.KeyboardButton(commands.MAIN_MENU)
            ]

            # Создаем клавиатуру
            markup = self._create_learning_markup(
                answer_buttons + action_buttons,
                row_width=2
            )

            # Сохраняем данные в состоянии
            with self.bot.retrieve_data(user_id, chat_id) as data:
                data.update(card_data)

            # Устанавливаем состояние обучения
            self.bot.set_state(user_id, self.MyStates.learning_mode, chat_id)

            # Отправляем карточку
            self.bot.send_message(
                chat_id,
                f"{self.lang.get_text('select_translation', lang=lang)}\n{card_data['translate_word']}",
                reply_markup=markup
            )

        except Exception as e:
            logger.error(f"Error in create_learning_card: {str(e)}")
            self._send_error_message(message.chat.id)

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

    def handle_lesson_selection(self, message: types.Message) -> None:
        """Обрабатывает выбор урока пользователем"""
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id
            lang = self._get_user_lang_from_cache(user_id) or 'ru'
            uid = self.crud.get_user_by_telegram_id(str(user_id))

            if message.text == self.Command.MAIN_MENU:
                self.show_main_menu(message)
                return

            try:
                lesson_id = int(message.text.split(':')[0].replace('✓', '').strip())
            except (ValueError, IndexError):
                error_msg = self.lang.get_text('invalid_lesson_format', lang=lang)
                self.bot.send_message(chat_id, error_msg)
                return

            # Обновляем урок через CRUDOperations
            result, error = self.crud.update_user_lesson(
                telegram_id=str(user_id),
                lesson_id=lesson_id
            )

            if error:
                error_msg = self.lang.get_text('db_error', lang=lang) + f": {error}"
                self.bot.send_message(chat_id, error_msg)
                return

            # Обновляем кэш
            if user_id in self.user_cache:
                self.user_cache[user_id]['current_lesson_id'] = lesson_id

            # Формируем сообщение об успехе
            success_msg = (
                f"{self.lang.get_text('lesson_selected', lang=lang)}: "
                f"{result.get('lesson_title', 'Unknown')}"
            )
            self.bot.send_message(chat_id, success_msg)

        except Exception as e:
            logger.error(f"Error in handle_lesson_selection: {str(e)}")
            self._send_error_message(message.from_user.id)

    def get_main_menu_markup(self):
        markup = types.ReplyKeyboardMarkup(row_width=2)
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

        current_state = self.bot.get_state(user_id, cid)
        # print(f"Current state: {current_state}")
        logger.debug(f"Current state: {current_state}")

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
        # Получаем данные состояния
        with self.bot.retrieve_data(user_id, cid) as data:
            if not data or 'phrase_id' not in data:
                logger.warning("Сессия устарела")
                self._recreate_learning_card(user_id, cid)
                return

            target_word = data.get('target_word')
            if not target_word:
                self._recreate_learning_card(message, user_id, cid)
                return

            # Проверяем ответ пользователя
            if text == target_word:
                self._handle_correct_answer(user_id, cid, data)
            else:
                self._handle_wrong_answer(user_id, cid, data)

    # -
    def _recreate_learning_card(self, message, user_id: int, chat_id: int):
        """Создает новую карточку при устаревших данных"""
        lang = self._get_user_lang_from_cache(user_id) or 'ru'
        self.bot.send_message(chat_id,
                              self.lang.get_text('session_restarted', lang=lang))
        self.create_learning_card(message, chat_id, user_id)

    def _handle_correct_answer(self, user_id: int, chat_id: int, data: dict):
        """Обрабатывает правильный ответ"""
        lang = self._get_user_lang_from_cache(user_id) or 'ru'

        # Обновляем прогресс
        success, error = self.crud.update_user_word_progress(
            user_id=data['user_id'],
            phrase_id=data['phrase_id']
        )

        if error:
            logger.error(f"Failed to update progress: {error}")

        # Формируем сообщение
        hint = f"{self.lang.get_text('correct_answer', lang=lang)} ✅\n" \
               f"{data['target_word']} -> {data['translate_word']}"

        # Создаем клавиатуру с вариантами ответов и кнопками
        answer_buttons = self._generate_answer_options(
            data['target_word'],
            data['other_words']
        )
        # Создаем клавиатуру 1
        commands = self._init_commands(ui_lang=lang)
        action_buttons = [
            types.KeyboardButton(commands.NEXT),
            types.KeyboardButton(commands.DELETE_WORD),
            types.KeyboardButton(commands.MAIN_MENU)
        ]

        markup = self._create_learning_markup(
            # answer_buttons + action_buttons,
            action_buttons,
            row_width=2
        )

        self.bot.send_message(chat_id, hint, reply_markup=markup)

    def _handle_wrong_answer(self, user_id: int, chat_id: int, data: dict):
        """Обрабатывает неправильный ответ"""
        lang = self._get_user_lang_from_cache(user_id) or 'ru'
        # Формируем сообщение
        hint = f"{self.lang.get_text('wrong_answer', lang=lang)} ❌\n" \
               f"{data['translate_word']} -> {data['target_word']}"

        # Создаем клавиатуру 2
        commands = self._init_commands(ui_lang=lang)
        action_buttons = [
            types.KeyboardButton(commands.NEXT),
            types.KeyboardButton(commands.ADD_WORD),
            types.KeyboardButton(commands.MAIN_MENU)
        ]

        markup = self._create_learning_markup(
            action_buttons,
            row_width=2
        )

        self.bot.send_message(chat_id, hint, reply_markup=markup)

    def _generate_answer_options(self, target_word: str, other_words: List[str]) -> List[types.KeyboardButton]:
        """Генерирует варианты ответов для клавиатуры"""
        buttons = [types.KeyboardButton(target_word)]
        buttons.extend([types.KeyboardButton(word) for word in other_words])
        random.shuffle(buttons)
        return buttons

    def get_user_lang(self, user_id):
        """Получаем язык пользователя из БД"""
        with self.crud.Session() as session:
            user = session.query(User).filter(User.telegram_id == str(user_id)).first()
            return user.ui_language if user else 'ru'

    # Вспомогательные методы
    def _send_error_message(self, chat_id: int) -> None:
        """Отправляет сообщение об ошибке пользователю"""
        lang = self._get_user_lang_from_cache(chat_id) or 'ru'
        error_msg = self.lang.get_text('error_occurred', lang=lang)
        try:
            self.bot.send_message(
                chat_id,
                error_msg,
                reply_markup=self._get_main_menu_markup(lang)
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {str(e)}")

    def _get_user_lang_from_cache(self, user_id: int) -> Optional[str]:
        """Получает язык интерфейса пользователя из кэша"""
        return self.user_cache.get(user_id, {}).get('ui_language')

    def _get_main_menu_markup(self, lang: str) -> types.ReplyKeyboardMarkup:
        """Создает клавиатуру главного меню для указанного языка"""
        commands = self._init_commands(ui_lang=lang)
        markup = types.ReplyKeyboardMarkup(row_width=2)

        buttons = [
            types.KeyboardButton(commands.SELECT_LESSON),
            types.KeyboardButton(commands.SELECT_TARGET_LANG),
            types.KeyboardButton(commands.SELECT_UI_LANG),
            types.KeyboardButton(commands.ADD_WORD),
            types.KeyboardButton(commands.NEXT)
        ]

        markup.add(*buttons)
        return markup

    def _create_learning_markup_v3(self, target_word: str, other_words: List[str],
                                   lang: str) -> types.ReplyKeyboardMarkup:
        """Создает клавиатуру для режима обучения"""
        markup = types.ReplyKeyboardMarkup(row_width=2)

        # Добавляем варианты ответов
        buttons = [types.KeyboardButton(target_word)]
        buttons.extend([types.KeyboardButton(word) for word in other_words])
        random.shuffle(buttons)

        # Добавляем основные кнопки
        commands = self._init_commands(ui_lang=lang)
        buttons.extend([
            types.KeyboardButton(commands.NEXT),
            types.KeyboardButton(commands.ADD_WORD),
            types.KeyboardButton(commands.DELETE_WORD),
            types.KeyboardButton(commands.MAIN_MENU)
        ])

        markup.add(*buttons)
        return markup

    def _create_learning_markup(self, buttons: List[types.KeyboardButton],
                                row_width: int = 2) -> types.ReplyKeyboardMarkup:
        """Создает клавиатуру из готовых кнопок"""
        markup = types.ReplyKeyboardMarkup(row_width=row_width)
        markup.add(*buttons)
        return markup

    def _format_welcome_message(self, user: User, stats: Dict) -> str:
        """Формирует приветственное сообщение с информацией о пользователе"""
        lang = user.ui_language
        lines = [
            self.lang.get_text('bot_welcome_msg', lang=lang),
            "",
            f"{self.lang.get_text('user_dict_size', lang=lang)}: {stats.get('word_count', 0)}",
            f"{self.lang.get_text('learned_words', lang=lang)}: {stats.get('learned_words', 0)}",
            f"{self.lang.get_text('target_language', lang=lang)}: {user.target_language}"
        ]

        if user.current_lesson_id:
            lines.append(
                f"{self.lang.get_text('current_lesson', lang=lang)}: {stats.get('current_lesson_title', 'Unknown')}"
            )
        else:
            lines.append(self.lang.get_text('no_lesson_selected', lang=lang))

        return "\n".join(lines)

    def run(self):
        print('Бот запущен...')
        self.bot.infinity_polling(skip_pending=True)


if __name__ == '__main__':
    TOKEN = '***'
    DB_URL = 'postgresql://postgres:***@localhost/lfl'

    bot = LanguageBot(TOKEN, DB_URL)
    # bot.run()
    # Запуск бота
    print(bot.start_bot())

    # Проверка статуса
    print(bot.get_bot_status())

    # Остановка бота через 60 секунд
    # time.sleep(60)
    # print(bot.stop_bot())
