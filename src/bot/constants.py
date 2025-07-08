from re import compile as re_compile

URL_REGEX = re_compile(r'https?://\S+')

ADD_GOOD = 'Добавить товар'
DELETE_GOOD = 'Удалить товар'
CHECK_GOODS = 'Проверить все товары'
MAIN_KB_PLACEHOLDER = 'Выберите пункт меню...'
CANCEL = '❌ Отмена'

ALLOWED_SITES = ('https://www.toppreise.ch/',)

SEND_LINK_MESSAGE = 'Дай ссылку на товар, бро.'
INCORRECT_URL_MESSAGE = (
    'Ссылка должна начинаться с одного из следующих сайтов: '
    f'{', '.join(ALLOWED_SITES)}'
)
LINK_RECEIVED_MESSAGE = 'Получил! Как назовешь товар?'
GOOD_ADDED_MESSAGE = 'Товар "{name}" с ценой {price} добавлен.'
ALREADY_EXISTS_MESSAGE = 'Этот товар уже отслеживается.'
NO_PRICE_MESSAGE = 'Не удалось получить цену по ссылке.'
NOT_URL_MESSAGE = 'Это не похоже на ссылку. Пришли правильную ссылку.'
NO_GOODS_MESSAGE = 'Пока ничего не отслеживается.'
DELETION_CANCELED_MESSAGE = 'Удаление отменено.'
PRODUCT_DELETED_MESSAGE = 'Товар "{product_name}" удалён.'
ERROR_MESSAGE = 'Произошла ошибка. Попробуйте начать сначала.'
NO_MESSAGE_ERROR = 'Ошибка: сообщение недоступно.'


ITEMS_PER_PAGE = 10
PREV_PAGE_BUTTON = '⬅️ Назад'
NEXT_PAGE_BUTTON = '➡️ Вперёд'
