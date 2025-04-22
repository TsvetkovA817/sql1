import configparser
import os


class ConfigHandler:
    def __init__(self, config_file = 'config.ini'):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        # Создаем файл конфигурации, если он не существует
        if not os.path.exists(self.config_file):
            self._create_default_config()
        else:
            self.config.read(self.config_file)

    def _create_default_config(self):
        """Создает конфиг с настройками по умолчанию"""
        self.config['Database'] = {
            'dbname': 'postgres',
            'host': '127.0.0.1',
            'user': 'postgres',
            'password': '****',
            'port': '5432',
        }
        self.config['General'] = {
            'language': 'ru',
        }
        self.config['Bot'] = {
            'key': '****',
            'name': 'testbot',
        }

        with open(self.config_file, 'w') as cf:
            self.config.write(cf)

    def get_db_config(self):
        """Возвращает настройки подключения к БД"""
        return {
            'dbname': self.config.get('Database', 'dbname', fallback='postgres'),
            'host': self.config.get('Database', 'host', fallback='127.0.0.1'),
            'user': self.config.get('Database', 'user', fallback='postgres'),
            'password': self.config.get('Database', 'password', fallback='****'),
            'port': self.config.getint('Database', 'port', fallback=5432),
        }

    def update_db_config(self, dbname, host, user, password, port):
        """Обновляет настройки подключения к БД"""
        self.config['Database'] = {
            'dbname': dbname,
            'host': host,
            'user': user,
            'password': password,
            'port': str(port)
        }
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def get_language(self):
        """Возвращает текущий язык из конфига"""
        return self.config.get('General', 'language', fallback='ru')

    def update_language(self, lang_code):
        """Обновляет язык в конфиге"""
        if not self.config.has_section('General'):
            self.config.add_section('General')
        self.config.set('General', 'language', lang_code)
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def get_bot_set(self):
        """Возвращает настройки бота"""
        return {
            'key': self.config.get('Bot','key', fallback=None),
            'name': self.config.get('Bot','name', fallback=None)
        }

    def update_bot_set(self, key, name):
        if not self.config.has_section('Bot'):
            self.config.add_section('Bot')
        self.config.set('Bot','key', key)
        self.config.set('Bot', 'name', name)
        with open(self.config_file, 'w') as cf:
            self.config.write(cf)
