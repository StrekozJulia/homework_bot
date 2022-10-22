import os
import telegram
import time
import requests
import logging
import sys
from http import HTTPStatus
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
    logging.info('Проверяем наличие обязательных переменных окружения...')
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
    """Делает запрос к API Яндекс.
    Практикума о наличии обновлений статусов домашних работ
    от переданного момента времени.
    """
    params = {'from_date': timestamp}
    logging.info('Выполняем запрос к эндпойнту Яндекс.Практикума...')
    requests_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params
    }
    try:
        response = requests.get(**requests_params)
    except Exception as error:
        raise exceptions.EndpointRequestError(
            f'Ошибка при выполнении запроса к API. '
            f'Параметры запроса: {requests_params}. {error}'
        )
    status_code = response.status_code
    if status_code != HTTPStatus.OK:
        raise exceptions.EndpointUnavaliableExc(
            f'Эндпоинт [{ENDPOINT}] недоступен. '
            f'Параметры запроса: {requests_params}'
            f'Код ответа API: {status_code}. '
            f'{response.reason}. {response.text}'
        )
    else:
        homework_statuses = response.json()
        return homework_statuses


def check_response(response):
    """Проверяет валидность ответа API.
    Возвращает список домашних работ, чей статус был изменен.
    """
    logging.info('Проверяем валидность полученных данных...')
    if not isinstance(response, dict):
        raise TypeError(
            f'Данные, переданные API, являются {type(response)}, '
            'a не словарем.'
        )
    if response == {}:
        raise exceptions.EmptyDataExc(
            'В словаре, переданном API, нет данных.'
        )
    if 'homeworks' not in response:
        raise KeyError(
            'В словаре, переданном API отсутствует ключ "homeworks".'
            f'Присутствуют ключи: {response.keys()}'
        )

    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise exceptions.HomeworkTypeError(
            'По ключу "homeworks" не найден список. Тип данных: '
            f'{type(homeworks)}'
        )
    return homeworks


def parse_status(homework):
    """Формирует сообщение о новом статусе домашней работы."""
    logging.info('Получены обновления. Определяем новый статус работы...')
    if ('homework_name' not in homework or 'status' not in homework):
        raise KeyError(
            'В словаре домашней работы отсутствуют нобходимые ключи: '
            '"homework_name", "status". Присутствуют ключи: '
            f'{homework.keys()}.'
        )
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_STATUSES:
        raise exceptions.UnknownStatusExc(
            f'Домашняя работа имеет неизвестный статус: {homework_status}.'
            f'Доступные статусы: {HOMEWORK_STATUSES.keys()}'
        )

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, msg):
    """Отправляет в telegram сообщение о смене статуса домашней работы."""
    logging.info(f'Попытка отправки в чат сообщения: {msg}...')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, msg)
    except Exception as error:
        msg = (
            f'Бот не смог отправить в чат сообщение: "{msg}".'
            f'Ошибка: {error}.'
        )
        raise exceptions.SendMessageError(msg)
    else:
        logging.info(f'Бот отправил в чат сообщение: "{msg}"')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(
            'Одна или более обязательных переменных окружения: '
            'PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID - отсуствуют.'
        )
    logging.info('Обязательные переменные окружения найдены.')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    error_msg_sent = False

    while True:
        try:
            response = get_api_answer(current_timestamp)
            logging.info('Ответ от API получен.')
            current_timestamp = int(time.time())
            homework = check_response(response)
            logging.info('Ответ API прошел валидацию.')
            if homework == []:
                logging.info('Статус работы не изменен.')
                error_msg_sent = False
            else:
                message = parse_status(homework[0])
                error_msg_sent = False
                send_message(bot=bot, msg=message)

        except exceptions.SendMessageError as error:
            logging.error(error)

        except Exception as error:
            msg = f'Сбой в работе программы: {error}'
            logging.error(msg)
            if not error_msg_sent:
                send_message(bot=bot, msg=msg)
                error_msg_sent = True

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
