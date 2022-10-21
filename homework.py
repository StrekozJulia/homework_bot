import os
import telegram
from time import time
import requests
import logging
import sys
from dotenv import load_dotenv
import exceptions

load_dotenv()

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

PRACTICUM_TOKEN: str = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME: int = 600
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES: dict = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> bool:
    """Проверяет наличие переменных окружения."""
    if PRACTICUM_TOKEN is None:
        message = (
            'Отсутствует переменная окружения: "PRACTICUM_TOKEN". '
            'Программа принудительно остановлена.'
        )
        logging.critical(message)
        return False

    if TELEGRAM_TOKEN is None:
        message = (
            'Отсутствует переменная окружения: '
            'TELEGRAM_TOKEN. Программа принудительно остановлена.'
        )
        logging.critical(message)
        return False

    if TELEGRAM_CHAT_ID is None:
        message = (
            'Отсутствует переменная окружения: '
            'TELEGRAM_CHAT_ID. Программа принудительно остановлена.'
        )
        logging.critical(message)
        return False

    return True


def get_api_answer(timestamp):
    """Делает запрос к API Яндекс.Практикума о наличии обновлений
    статусов домашних работ от переданного момента времени.
    """
    params = {'from_date': timestamp}

    homework_statuses = requests.get(url=ENDPOINT,
                                     headers=HEADERS,
                                     params=params)
    status_code = homework_statuses.status_code
    if status_code != 200:
        raise exceptions.EndpointUnavaliableExc(
            'Эндпоинт [https://practicum.yandex.ru/api/user_api/'
            'homework_statuses/] недоступен. '
            f'Код ответа API:  {status_code}'
        )
    return homework_statuses.json()


def check_response(response):
    """
    Проверяет валидность ответа API и возвращает список домашних
    работ, чей статус был изменен.
    """
    if not isinstance(response, dict):
        raise TypeError('Данные, переданные API, не являются словарем.')
    if response == {}:
        raise exceptions.EmptyDataExc(
            'В словаре, переданном API, нет данных.'
        )
    if 'homeworks' not in response:
        raise KeyError(
            'В словаре, переданном API отсутствует ключ "homeworks".'
        )

    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise exceptions.HomeworkTypeError(
            'По ключу "homeworks" не найден список.'
        )
    if homeworks == []:
        raise exceptions.NoNewStatusExc
    return homeworks[0]


def parse_status(homework):
    """Формирует сообщение о новом статусе домашней работы"""
    if ('homework_name' not in homework or 'status' not in homework):
        raise KeyError(
            'В словаре домашней работы отсутствуют нобходимые ключи.'
        )
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_STATUSES:
        raise exceptions.UnknownStatusExc(
            'Неизвестный статус работы.'
        )

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, msg):
    """Отправляет в telegram сообщение о смене статуса домашней работы"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, msg)
    except Exception:
        logging.error(f'Бот не смог отправить сообщение в чат: "{msg}"')
    else:
        logging.info(f'Бот отправил сообщение в чат: "{msg}"')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise exceptions.NoTokenException(
            'Одна или более переменных окружения отсуствуют.'
        )

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    error_msg_sent = False

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = int(time.time())
            homework = check_response(response)
            message = parse_status(homework)

        except exceptions.NoNewStatusExc:
            msg = 'Статус домашней работы не изменен.'
            logging.info(msg)
            error_msg_sent = False
            time.sleep(RETRY_TIME)

        except Exception as error:
            msg = f'Сбой в работе программы: {error}'
            logging.error(msg)
            if not error_msg_sent:
                send_message(bot=bot, msg=msg)
                error_msg_sent = True
            time.sleep(RETRY_TIME)

        else:
            error_msg_sent = False
            send_message(bot=bot, msg=message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
