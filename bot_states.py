from enum import Enum
import config


class States(Enum):
    """ Перечисление, описывающее состояния бота """
    S_READY = 1
    S_LOW = 2
    S_HIGH = 3
    S_CUSTOM = 4
    S_INTERNSHIP = 5
    S_LANGUAGE_ENTERED = 6
    S_RANGE_ENTERED = 7


class BotFSM:
    """
    Класс, реализующий поведение конечного автомата (finite state machine).
    """
    def __init__(self):
        self._state = States.S_READY
        self.frst_command = None
        self.lang = None
        self.top_salary = None
        self.low_salary = None

    def set_state(self, state="") -> None:
        """
        Сеттер, устанавливающий бота в состояние state.

        :param state: состояние;
        """
        if state == "/low":
            self._state = States.S_LOW
        elif state == "/high":
            self._state = States.S_HIGH
        elif state == "/custom":
            self._state = States.S_CUSTOM
        elif state == "/internships":
            self._state = States.S_INTERNSHIP
        elif state in config.languages:
            self._state = States.S_LANGUAGE_ENTERED
        elif state == "range":
            self._state = States.S_RANGE_ENTERED
        else:
            self._state = States.S_READY

    def get_current_state(self) -> States:
        """
        Геттер, возвращающий текущее состояние бота.

        :return self._state: состояние бота.
        """
        return self._state

    def set_frst_command(self, command: str) -> None:
        """
        Сеттер, сохраняющий одну из команд /low, /high или /custom,
        введенных пользователем.

        :param command: название команды.
        """
        if command == "/low":
            self.frst_command = States.S_LOW
        elif command == "/high":
            self.frst_command = States.S_HIGH
        elif command == "/custom":
            self.frst_command = States.S_CUSTOM
        elif command == "/internships":
            self.frst_command = States.S_INTERNSHIP

    def get_frst_command(self) -> States:
        """
        Возвращает имя команды, которую ввел пользователь.
        :return self.frst_command: имя команды.
        """
        return self.frst_command

    def set_lang(self, lang: str) -> None:
        """
        Сохраняет язык, по которому будет производиться поиск вакансий.

        :param lang: язык;
        """
        self.lang = lang

    def get_lang(self) -> str:
        """
        Возвращает язык программирования, по которому нужно
        произвести поиск вакансий.

        :return self.lang: язык программирования.
        """
        return self.lang

    def set_to_salary(self, salary: int) -> None:
        """
        Устанавливает верхнюю границу диапазона зарплат для команды custom.

        :param salary: уровень зарплаты.
        """
        self.top_salary = salary

    def get_to_salary(self) -> int:
        """
        Возвращает верхнюю границу диапазона зарплат для команды custom.

        :return self.top_salary:
        """
        return self.top_salary

    def set_from_salary(self, salary: int):
        """
        Устанавливает нижнюю границу диапазона зарплат для команды custom.

        :param salary: уровень зарплаты.
        """
        self.low_salary = salary

    def get_from_salary(self) -> int:
        """
        Возвращает нижнюю границу диапазона зарплат для команды custom.

        :return self.top_salary:
        """
        return self.low_salary
