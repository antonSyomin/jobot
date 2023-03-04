import sqlite3
import db
import telebot  # type: ignore
import bot_states
import re
import config
import hh_api


bot = telebot.TeleBot(config.tg_token)
botFSM = bot_states.BotFSM()


@bot.message_handler(commands=["help"])
def get_help(message):
    """
    Выводит список команд чат-бота,
    когда пользователь вводит /help.

    :param message: объект «сообщение», который вводит пользователь.
    """
    help_str = "Доступные команды:\n\n" \
               "/low — вакансии с наименьшей зарплатой\n\n" \
               "/high — вакансии с наибольшей зарплатой\n\n" \
               "/custom — задать диапазон зарплат\n\n" \
               "/internships — получить список стажировок в IT\n\n" \
               "/history — история запросов"
    bot.send_message(message.chat.id, help_str)


@bot.message_handler(commands=["hello_world", "start"])
def hello_world(message):
    """
    Выводит приветствие,
    когда пользователь вводит /hello_world или «Привет».
    :param message: объект «сообщение», который вводит пользователь.
    """
    answer = \
        "***Привет! Я Jobot — Telegram-бот для быстрого поиска работы в IT.\n***" \
        "\nЯ могу найти самые высоко- и низкооплачиваемые вакансии для разработчиков," \
        "а также подобрать работу для программистов без опыта." \
        "\n\n***Чтобы узнать список моих команд, напиши /help***"
    bot.send_message(message.chat.id, answer, parse_mode="Markdown")


@bot.message_handler(
        func=lambda command:
        botFSM.get_current_state() == bot_states.States.S_READY,
        commands=["low", "high", "custom"])
def enter_command(command):
    """
    Срабатывает, когда пользователь вводит /low, /high или /custom,
    когда бот находится в состоянии S_READY (см. State);
    Приглашает ко вводу языка программирования.

    :param command: объект «сообщение», который вводит пользователь.
    """
    try:
        botFSM.set_state(command.text)
        botFSM.set_frst_command(command.text)
        db_connection.log_request(command.text)
        bot.send_message(command.chat.id,
                         "Введите язык программирования.\nНапример: python")
    except sqlite3.Error as err:
        print(err)
        bot.send_message(command.chat.id,
                         "Уп-с... Кажется, что-то пошло не так. "
                         "Мы уже работаем над проблемой!")


@bot.message_handler(
    func=lambda msg: botFSM.get_current_state()
    in [
        bot_states.States.S_LOW,
        bot_states.States.S_HIGH
     ])
def enter_language(message):
    """
    Вызывается после того, как пользователь ввел язык программирования:
    - если чат-бот находится в состоянии S_LOW или S_HIGH,
      спрашивает, сколько вакансий показать.

    :param message: объект «сообщение», который вводит пользователь.
    """
    if message.text.lower() in config.languages:  # если язык есть в словаре
        botFSM.set_lang(message.text.lower())
        botFSM.set_state(message.text.lower())
        bot.send_message(message.chat.id, "Сколько вакансий показать?")
    else:
        bot.send_message(message.chat.id,
                         "Не нашли вакансии по такому языку в нашей базе :(")
        botFSM.set_state()  # скинуть состояние до S_READY


@bot.message_handler(
    func=lambda msg:
    botFSM.get_current_state() == bot_states.States.S_CUSTOM)
def enter_language_custom(message):
    """
    Вызывается после того, как пользователь ввел язык программирования,
    если чат-бот находится в состоянии S_CUSTOM,
    и предлагает ввести диапазон зарплат.

    :param message: объект «сообщение», который вводит пользователь.
    """
    if message.text.lower() in config.languages:  # если язык есть в словаре
        botFSM.set_lang(message.text)
        botFSM.set_state(message.text)
        bot.send_message(message.chat.id,
                         "Введите диапазон зарплат: "
                         "[нач. сумма] [кон. сумма]")
    else:
        bot.send_message(message.chat.id,
                         "Не нашли вакансии по такому языку в нашей базе :(")
        botFSM.set_state()  # скинуть состояние до S_READY


@bot.message_handler(
    func=lambda command:
    botFSM.get_current_state() == bot_states.States.S_LANGUAGE_ENTERED
    and botFSM.get_frst_command() == bot_states.States.S_CUSTOM)  # если была введена команда /custom
def input_range(message):
    """
    Срабатывает, когда пользователь вводит диапазон зарплат,
    а чат-бот находится в состоянии S_LANGUAGE_ENTERED.

    :param message: объект «сообщение», который вводит пользователь.
    """
    try:
        db_connection.log_request("enter sal_range")
        sal_range = re.split(" |,|;|-|—", message.text)
        int_range = tuple(int(sal) for sal in sal_range)
        botFSM.set_to_salary(int_range[0])
        botFSM.set_from_salary(int_range[1])
        botFSM.set_state("range")
        bot.send_message(message.chat.id, "Сколько вакансий показать?")
    except ValueError as val_err:
        bot.send_message(message.chat.id,
                         "Неверный формат ввода. Введите два целых числа: "
                         "[нач. сумма] [кон. сумма]")
        botFSM.set_state()  # скинуть состояние до S_READY
        print(val_err)
    except sqlite3.DatabaseError as err:
        print(err)
        bot.send_message(message.chat.id,
                         "Уп-с... Кажется, что-то пошло не так. "
                         "Мы уже работаем над проблемой!")


@bot.message_handler(
        func=lambda command:
        botFSM.get_current_state() == bot_states.States.S_READY,
        commands=["internships"])
def internships(command):
    """
       Срабатывает, когда пользователь вводит /internships,
       когда бот находится в состоянии S_READY (см. State);
       Показывает, сколько стажировок было найдено и по каким направлениям.

       :param command: объект «сообщение», который вводит пользователь.
       """
    try:
        num_of_internships = hh_api.get_num_of_internships()
        categories = hh_api.get_list_of_intern_categories()
        answer = "Jobot нашёл {} вакансий без опыта работы. Выберите категорию".format(num_of_internships)
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        for category_name, data in categories.items():
            if data["counter"] > 0:
                btn = telebot.types.KeyboardButton("{} ({})".format(category_name, data["counter"]))
                markup.add(btn)
        markup.add(telebot.types.KeyboardButton("Назад"))
        bot.send_message(command.chat.id, answer, reply_markup=markup)
        botFSM.set_state(command.text)
        db_connection.log_request(command.text)
        print(botFSM.get_current_state())
    except sqlite3.Error as err:
        print(err)
        bot.send_message(command.chat.id,
                         "Уп-с... Кажется, что-то пошло не так. "
                         "Мы уже работаем над проблемой!")


@bot.message_handler(
        func=lambda message:
        botFSM.get_current_state() == bot_states.States.S_INTERNSHIP,
        content_types=["text"])
def get_internships(message):
    try:
        if message.text == "Назад":
            bot.send_message(message.from_user.id, "Введите команду", reply_markup=telebot.types.ReplyKeyboardRemove())
            botFSM.set_state()
            return
        category = " ".join(message.text.split(" ")[:-1])
        internships_list = hh_api.get_list_of_intern_categories()[category]
        answer = ""
        for i, vacancy in enumerate(internships_list["items"]):
            if len(answer)+len(vacancy['name']+vacancy['url'])+6 > 4096:
                bot.send_message(message.chat.id, answer)
                answer = ""
            answer += "{}. {}\n{}\n\n".format(i + 1, vacancy['name'], vacancy['url'])
        bot.send_message(message.chat.id, answer)
        db_connection.log_request(message.text)
    except sqlite3.Error as err:
        print(err)
        bot.send_message(message.chat.id,
                         "Уп-с... Кажется, что-то пошло не так. "
                         "Мы уже работаем над проблемой!")


@bot.message_handler(
    func=lambda msg: botFSM.get_current_state()
    in [
            bot_states.States.S_LANGUAGE_ENTERED,
            bot_states.States.S_RANGE_ENTERED
        ])
def input_max(message):
    """
    Вызывается после того, как пользователь ввёл язык программирования,
    Когда бот находится в состоянии S_LANGUAGE_ENTERED (см. States).

    :param message: объект «сообщение», который вводит пользователь.
    """
    try:
        max_num_of_vacancies = int(message.text)
        vacancy_str = ""
        if botFSM.get_frst_command() == bot_states.States.S_LOW:
            vacancy_list = hh_api.get_min_salary_vacancies(
                    botFSM.get_lang(),
                    max_num_of_vacancies)
        elif botFSM.get_frst_command() == bot_states.States.S_HIGH:
            vacancy_list = hh_api.get_max_salary_vacancies(
                botFSM.get_lang(), max_num_of_vacancies)
        else:
            vacancy_list = hh_api.get_vacancies_in_salary_range(
                botFSM.get_lang(),
                max_num_of_vacancies,
                botFSM.get_from_salary(),
                botFSM.get_to_salary())
        for i, vacancy in enumerate(vacancy_list):
            if len(vacancy_str)+len(vacancy['name']+vacancy['url'])+6 > 4096:
                bot.send_message(message.chat.id, vacancy_str)
                vacancy_str = ""
            vacancy_str += "{}. {}\n{}\n\n".format(i+1, vacancy['name'], vacancy['url'])

        bot.send_message(message.chat.id, vacancy_str)
        botFSM.set_state()
        db_connection.log_request("enter max_num")
    except ValueError as err:
        print("Ошибка:", err)
        bot.send_message(message.chat.id,
                         "Кажется, вы ввели что-то не то...")
    except sqlite3.Error as err:
        print("Ошибка:", err)
    finally:
        botFSM.set_state()


@bot.message_handler(commands=["history"])
def history(message):
    """
    Показывает историю введенных команд (первые 10 команд).

    :param message: объект «сообщение», который вводит пользователь.
    """
    try:
        history_dump = db_connection.get_history()
        history_str = ""
        # складываем историю в одну строку
        for row in reversed(history_dump):
            history_str += "{}  {}  {}\n".format(row[0], row[1], row[2])
        bot.send_message(message.chat.id, history_str)
    except sqlite3.DatabaseError as err:
        print(err)
        return None


@bot.message_handler(content_types=["text"])
def any_other_text(message):
    """
    Вызывается, когда пользователь вводит «Привет»
    или слово/команду, которой нет в чат-боте.

    :param message: объект «сообщение», который вводит пользователь.
    """
    if message.text.lower() == "привет":
        hello_world(message)
    else:
        bot.send_message(message.chat.id,
                         "Jobot не знает такой команды. "
                         "Чтобы посмотреть список доступных команд, введите /help")


db_connection = db.DB()
db_connection.create_table()
