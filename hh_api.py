import requests
import json
from math import inf
import config


def make_request(params: dict) -> dict:
    req = requests.get("https://api.hh.ru/vacancies", params)
    data = req.content.decode("utf-8")
    data_obj = json.loads(data)
    return data_obj


def get_num_of_vacancies(name: str, with_salary=True) -> int:
    """
    Возвращает кол-во вакансий, в которых упоминается технология/навык.

    :param name: язык программирования, технология или навык.
    :param with_salary: только вакансии с указанной зарплатой;
    :return: data_obj["pages"] — кол-во вакансий.
    """
    params = {
        'text': 'NAME:{}'.format(name),
        'page': 1,
        'per_page': 1,
        'only_with_salary': with_salary
    }

    return int(make_request(params)["found"])


def get_num_of_pages(name=""):
    if name:
        num_of_vacancies = get_num_of_vacancies(name)
    else:
        num_of_vacancies = get_num_of_internships()
    num_of_pages = num_of_vacancies // 100
    if num_of_vacancies % 100:
        num_of_pages += 1
    return num_of_pages


def get_vacancies_in_salary_range(
            name: str,
            max_vac_num: int,
            from_salary: int,
            to_salary: int) -> list[dict]:
    """
    Возвращает список вакансий с зарплатами,
    которые входят в заданный диапазон.

    :param name: название языка программирования или навыка;
    :param max_vac_num: максимальное кол-во ссылок, которое нужно показать;
    :param from_salary: нижняя граница зарплаты;
    :param to_salary: верхняя граница зарплаты.
    :return:
    """
    params = {
        'text': name,
        'page': 0,
        'per_page': 100,
        'only_with_salary': True,
        'order_by': "salary_asc"
    }

    result = list()
    for i_page in range(get_num_of_pages(params)):
        params["page"] = i_page
        data = make_request(params)["items"]
        for vacancy in data["items"]:
            if vacancy["salary"]["from"]:
                salary_from = int(vacancy["salary"]["from"]) \
                              * config.currencies[vacancy["salary"]["currency"]]
            else:
                salary_from = 0
            if vacancy["salary"]["to"]:
                salary_to = int(vacancy["salary"]["to"]) \
                            * config.currencies[vacancy["salary"]["currency"]]
            else:
                salary_to = inf
            if to_salary >= salary_from and salary_to >= from_salary:
                result.append({'url': vacancy["alternate_url"], 'name': vacancy['name']})

    return result[:max_vac_num]


def get_vacancies_list(name: str, max_vac_num, order="salary_asc") -> list:
    """
    Функция, которая возвращает список ссылок на вакансии,
    отсортированный в порядке, заданном параметром list_order.

    :param name: название языка программирования, фреймворка и т.д.;
    :param max_vac_num: максимальное количество вакансий;
    :param order: порядок сортировки вакансий;
    :return: result(list) — список ссылок.
    """
    params = {
        'text': name,
        'page': 0,
        'per_page': 100,
        'only_with_salary': True,
        'order_by': order
    }

    # Проходим по каждой странице
    # и складываем ссылки на вакансии в список result
    # до тех пор, пока их количество не достигнет max_vac_num
    # или они не закончатся
    result: list = []
    for i_page in range(get_num_of_pages(name)):
        params["page"] = i_page
        data = make_request(params)["items"]
        for vacancy in data:
            if len(result) < max_vac_num:
                result.append({'url': vacancy["alternate_url"], 'name': vacancy['name']})
            else:
                break
    return result


def get_max_salary_vacancies(name: str, max_vac_num: int) -> list:
    """
    Функция, которая возвращает список ссылок на вакансии,
    с наибольшими зарплатами.

    :param name: название языка программирования, фреймворка и т.д.;
    :param max_vac_num: максимальное количество вакансий;;
    :return: result(list) — список ссылок.
    """
    return get_vacancies_list(name, max_vac_num, order="salary_desc")


def get_min_salary_vacancies(name: str, max_vac_num: int) -> list:
    """
    Функция, которая возвращает список ссылок на вакансии,
    с наименьшими зарплатами.

    :param name: название языка программирования, фреймворка и т.д.;
    :param max_vac_num: максимальное количество вакансий;;
    :return: result(list) — список ссылок.
    """
    return get_vacancies_list(name, max_vac_num, order="salary_asc")


def get_num_of_internships():
    params = {
        'text': 'стажёр OR стажировка OR стажировку',
        'page': 1,
        'per_page': 1,
        'experience': 'noExperience',
        'professional_role': ['96', '124', '165', '160', '113'],
    }
    num_of_vacancies = int(make_request(params)["found"])
    return num_of_vacancies


def get_all_internship() -> list:
    params = {
        'text': 'стажёр OR стажировка OR стажировку',
        'page': 0,
        'per_page': 100,
        'experience': 'noExperience',
        'professional_role': ['96', '124', '165', '160', '113']
    }

    result = list()
    for i_page in range(get_num_of_pages()):
        params["page"] = i_page
        data = make_request(params)['items']
        for vacancy in data:
            result.append({'url': vacancy["alternate_url"], 'name': vacancy['name']})
    return result


def get_list_of_intern_categories():
    intern_categories = dict()
    for category in config.categories:
        intern_categories[category] = {"counter": 0, "items": []}
    data = get_all_internship()
    for name, tags in config.categories.items():
        for i, vacancy in enumerate(data):
            for tag in tags:
                if tag in vacancy["name"].lower():
                    intern_categories[name]["counter"] += 1
                    intern_categories[name]["items"].append(vacancy)
                    data.pop(i)
    # Если остались вакансии
    if data:
        intern_categories["Другое"] = dict()
        intern_categories["Другое"]["counter"] = len(data)
        intern_categories["Другое"]["items"] = data
    return intern_categories
