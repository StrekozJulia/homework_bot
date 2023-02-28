# Телеграм-бот для Яндекс.Практикум
### Функционал - оповещение о смене статуса проверки домашней работы
* Чат-бот раз в 10 минут делат запрос через API к сервису Практикум.Домашка. 
* При изменении статуса проверки работы (взята на ревью, возвращена на доработку, зачтена) присылает пользователю оповещение в Telegram.
* При возникновении новой ошибки доступа к серверу присылает пользователю оповещение в Telegram.
* Производит логирование своей работы.

### Технологии:
* Python 3.7
* python-telegram-bot 13.7

## Запуск проекта (только для пользователей Яндекс.Практикум)
1. Клонировать репозиторий, выполнив команду в консоли:
```
git@github.com:StrekozJulia/homework_bot.git
```
2. Перейти в папку проекта:
```
cd homework_bot
```
3. Создать и активировать виртуальное окружение:
```
py -3.7 -m venv venv
source venv/scripts/activate
```
4. Обновить пакетный установщик:
```
python -m pip install --upgrade pip
```
5. Установить зависимости из файла 'requirements.txt':
```
pip install -r requirements.txt
```
6. Создать аккаунт бота в Telegram:
  - *Найти в Telegram бота @BotFather.* В окно поиска над списком контактов
  введите его имя. Обратите внимание на иконку возле имени бота: белая галочка
  на голубом фоне. Эту иконку устанавливают администраторы Telegram, она означает,
  что бот настоящий.
  - *Зарегистрировать бота.*
  Начните диалог с ботом @BotFather: нажмите кнопку "Start".
  Затем отправьте  команду /newbot и укажите параметры нового бота:
  *имя, под которым ваш бот будет отображаться в списке контактов;
  *техническое имя вашего бота, по которому его можно будет найти в Telegram.
  Имя должно быть уникальным и оканчиваться на слово bot в любом регистре.
  Если аккаунт создан, @BotFather поздравит вас и отправит в чат токен для работы
  с Bot API.
  - *Настроить аккаунт бота через @BotFather.*
  Отправьте команду /mybots и вы получите список ботов, которыми вы управляете.
  Укажите бота, которого нужно отредактировать, и нажмите кнопку Edit Bot.
  Можно изменить:
  Имя бота (Edit Name);
  Описание (Edit Description) — текст, который пользователи увидят в самом начале
  диалога с ботом под заголовком «Что может делать этот бот?»;
  Общую информацию (Edit About) — текст, который будет виден в профиле бота;
  Картинку-аватар (Edit Botpic);
  Команды (Edit Commands) — подсказки для ввода команд.

7. Получить [токен Яндекс.Практикума](https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a)

8. Создать '.env' файл с токенами:
```
PRACTICUM_TOKEN=<PRACTICUM_TOKEN>       # токен профиля на Яндекс.Практикуме
TELEGRAM_TOKEN=<TELEGRAM_TOKEN>         # токен Telegram-бота
TELEGRAM_CHAT_ID=<TELEGRAM_CHAT_ID>     # ID пользователя в Telegram
```
9. Запустить код программы в редакторе кода:
```
python homework.py
```
10. Получать оповещения на телеграм.
