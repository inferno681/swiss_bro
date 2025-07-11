from re import compile as re_compile

URL_REGEX = re_compile(r'https?://\S+')

ADD_GOOD = 'Добавить товар'
DELETE_GOOD = 'Удалить товар'
CHECK_ONE = 'Статистика по товару'
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
PRICE_IN_RUBLES = 'Примерная цена в рублях {price}'
ALREADY_EXISTS_MESSAGE = 'Этот товар уже отслеживается.'
NO_PRICE_MESSAGE = 'Не удалось получить цену по ссылке.'
NOT_URL_MESSAGE = 'Это не похоже на ссылку. Пришли правильную ссылку.'
NO_GOODS_MESSAGE = 'Пока ничего не отслеживается.'
DELETION_CANCELED_MESSAGE = 'Удаление отменено.'
CHECK_ONE_CANCELED_MESSAGE = 'Просмотр статистики отменен.'
PRODUCT_DELETED_MESSAGE = 'Товар "{product_name}" удалён.'
ERROR_MESSAGE = 'Произошла ошибка. Попробуйте начать сначала.'
NO_MESSAGE_ERROR = 'Ошибка: сообщение недоступно.'
PRODUCT_NOT_FOUND_MESSAGE = '⚠️ Товар с именем «{product_name}» не найден.'
PRODUCT_INFO_LINE = '{pos}. {name} — {price} {currency}.'
RUBLE_PRICE_LINE_INFO = 'Примерно {rub_price} рублей'

ITEMS_PER_PAGE = 10
PREV_PAGE_BUTTON = '⬅️ Назад'
NEXT_PAGE_BUTTON = '➡️ Вперёд'

JOB_ID = 'update_prices_job'
RUB_LINE = '💵 Примерно <b>{rub_price} ₽</b>\n'
UPDATE_PRICE_MESSAGE = (
    '💰 Цена на <b>{product}</b> обновилась: <b>{new_price}</b>\n'
    '{rub_line}\n'
    '📉 Минимальная цена за период: <b>{min_price}</b>\n'
    '📈 Максимальная цена за период: <b>{max_price}</b>\n\n'
    '🕒 Наблюдение начато: <b>{created_at}</b>\n'
    '📅 Последнее обновление: <b>{updated_at}</b>'
)
