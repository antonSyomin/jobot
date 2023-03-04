import sqlite3


class DB:
    """
    Класс, реализующий обмен данными c БД.

    Arg:
        db_name(str): название базы данных
    """
    def __init__(self, db_name="user_logs.db"):
        self._db_name = db_name

    def create_table(self) -> None:
        """
        Метод, который создает единственную в БД таблицу Logs.
        """
        create_table = "CREATE TABLE IF NOT EXISTS " \
                       "Logs(" \
                       "id INTEGER PRIMARY KEY, " \
                       "command TEXT, " \
                       "date DATE, time TIME)"
        with sqlite3.connect(self._db_name) as connection:
            cursor = connection.cursor()
            cursor.execute(create_table)

    def get_history(self) -> list:
        """
        Метод, получающий последние 10 запросов к чат-боту.

        :return: history
        """
        with sqlite3.connect(self._db_name) as connection:
            cursor = connection.cursor()
            query = "SELECT command, date, time FROM Logs ORDER BY id DESC LIMIT 10"
            result = cursor.execute(query)
            return result.fetchall()

    def log_request(self, command: str) -> None:
        """
        Метод, который сохраняет запрос к чат-боту.

        :param command: команда, которую отправил пользователь
        """

        with sqlite3.connect(self._db_name) as connection:
            cursor = connection.cursor()
            insert = "INSERT INTO Logs (command, date, time) VALUES(" \
                     "'{}', date('now'), time('now'))".format(command)
            cursor.execute(insert)
