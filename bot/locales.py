"""Localization helpers."""
from __future__ import annotations

SUPPORTED_LANGS = ("ru", "es")

TRANSLATIONS = {
    "ru": {
        "menu_client": "Панель клиента",
        "menu_admin": "Панель админа",
        "welcome": "Привет, {name}! Я помогу быстро собрать заказ.",
        "welcome_new": "Привет! Давай зарегистрируем тебя для заказов.",
        "ask_name": "Как тебя зовут? (имя и фамилия)",
        "ask_company": "Название точки/компании (или '-' если нет)",
        "request_sent": "Готово. Заявка отправлена администратору.",
        "pending": "Твоя заявка на рассмотрении. Подтверждение придет позже.",
        "blocked": "Доступ ограничен. Напиши администратору.",
        "access_denied": "Нет доступа. Нужна верификация администратора.",
        "orders_closed": "Прием заказов сейчас закрыт.",
        "no_products": "Каталог пока пуст.",
        "qty_prompt": "({current}/{total}) {product}\nВведи количество (0 = пропустить)",
        "qty_invalid": "Нужна цифра: 0 или больше.",
        "order_empty": "Похоже, ты ничего не выбрал. Заказ отменен.",
        "order_summary": "Твой заказ:",
        "order_total": "Итого: позиций {positions}, единиц {units}",
        "order_confirmed": "Заказ подтвержден.",
        "order_cancelled": "Заказ отменен.",
        "my_orders_empty": "У тебя пока нет заказов.",
        "my_order_title": "Заказ от {date}:",
        "total_units": "Итого: {units} ед.",
        "lang_changed": "Язык переключен: Русский.",
        "mode_changed_client": "Режим: клиент.",
        "mode_changed_admin": "Режим: админ (временно открыт для всех).",
        "choose_language": "Выбери язык интерфейса:",
        "choose_mode": "Выбери режим интерфейса:",
        "admin_only_mode": "Эта функция доступна в режиме админа.",
        "session_opened": "Сессия #{id} открыта. Уведомлено: {sent}/{total}.",
        "session_exists": "Сначала закрой текущую открытую сессию.",
        "session_closed": "Сессия закрыта. Заказов: {count}/{total}.",
        "no_open_session": "Сейчас нет открытой сессии.",
        "summary_empty": "Сессия #{id}: заказов пока нет ({count}/{total}).",
        "summary_title": "Сводка сессии #{id}",
        "summary_orders": "Заказов: {count}/{total}",
        "summary_grand": "Всего единиц: {total}",
        "no_sessions": "Сессий пока нет.",
        "excel_no_orders": "В этой сессии нет заказов.",
        "catalog_empty": "Каталог пуст.",
        "catalog_title": "Каталог:",
        "product_added": "Добавлено: {name}",
        "product_prompt": "Введи название нового продукта:",
        "name_empty": "Название не может быть пустым.",
        "clients_empty": "Клиентов пока нет.",
        "clients_title": "Клиенты:",
        "client_approved": "Клиент {name} подтвержден.",
        "client_blocked": "Клиент заблокирован.",
        "remind_all_done": "Все уже отправили заказ.",
        "remind_sent": "Напоминание отправлено: {sent}/{total}.",
        "registered_at": "Регистрация: {date}",
        "client_status": "Статус: {status}",
        "client_company": "Компания: {company}",
        "new_client_request": "Новая заявка\nИмя: {name}\nКомпания: {company}",
        "admin_new_order": "Новый заказ от {name}:",
        "admin_open_notice": "Прием заказов открыт. Отправьте заказ, пожалуйста.",
        "admin_remind_notice": "Напоминание: прием заказов открыт.",
        "auto_open_client": "Открыт новый прием заказов.{deadline}",
        "deadline_suffix": " Успей до {day} {time}.",
    },
    "es": {
        "menu_client": "Panel cliente",
        "menu_admin": "Panel admin",
        "welcome": "Hola, {name}. Te ayudo a enviar tu pedido rapido.",
        "welcome_new": "Hola. Vamos a registrarte para pedidos.",
        "ask_name": "Como te llamas? (nombre y apellido)",
        "ask_company": "Nombre de empresa/punto (o '-' si no aplica)",
        "request_sent": "Listo. Solicitud enviada al administrador.",
        "pending": "Tu solicitud sigue en revision.",
        "blocked": "Tu acceso esta bloqueado. Contacta al admin.",
        "access_denied": "Sin acceso. Espera aprobacion del admin.",
        "orders_closed": "Los pedidos estan cerrados ahora.",
        "no_products": "El catalogo esta vacio por ahora.",
        "qty_prompt": "({current}/{total}) {product}\nIngresa cantidad (0 = saltar)",
        "qty_invalid": "Ingresa un numero: 0 o mayor.",
        "order_empty": "No seleccionaste productos. Pedido cancelado.",
        "order_summary": "Tu pedido:",
        "order_total": "Total: {positions} productos, {units} unidades",
        "order_confirmed": "Pedido confirmado.",
        "order_cancelled": "Pedido cancelado.",
        "my_orders_empty": "Aun no tienes pedidos.",
        "my_order_title": "Pedido de {date}:",
        "total_units": "Total: {units} uds.",
        "lang_changed": "Idioma cambiado: Espanol.",
        "mode_changed_client": "Modo: cliente.",
        "mode_changed_admin": "Modo: admin (temporalmente para todos).",
        "choose_language": "Elige idioma:",
        "choose_mode": "Elige modo de interfaz:",
        "admin_only_mode": "Esta funcion requiere modo admin.",
        "session_opened": "Sesion #{id} abierta. Notificados: {sent}/{total}.",
        "session_exists": "Ya hay una sesion abierta.",
        "session_closed": "Sesion cerrada. Pedidos: {count}/{total}.",
        "no_open_session": "No hay sesion abierta.",
        "summary_empty": "Sesion #{id}: sin pedidos ({count}/{total}).",
        "summary_title": "Resumen sesion #{id}",
        "summary_orders": "Pedidos: {count}/{total}",
        "summary_grand": "Total unidades: {total}",
        "no_sessions": "No hay sesiones todavia.",
        "excel_no_orders": "No hay pedidos en esta sesion.",
        "catalog_empty": "Catalogo vacio.",
        "catalog_title": "Catalogo:",
        "product_added": "Anadido: {name}",
        "product_prompt": "Escribe el nombre del nuevo producto:",
        "name_empty": "El nombre no puede estar vacio.",
        "clients_empty": "No hay clientes.",
        "clients_title": "Clientes:",
        "client_approved": "Cliente {name} aprobado.",
        "client_blocked": "Cliente bloqueado.",
        "remind_all_done": "Todos ya hicieron su pedido.",
        "remind_sent": "Recordatorio enviado: {sent}/{total}.",
        "registered_at": "Registro: {date}",
        "client_status": "Estado: {status}",
        "client_company": "Empresa: {company}",
        "new_client_request": "Nueva solicitud\nNombre: {name}\nEmpresa: {company}",
        "admin_new_order": "Nuevo pedido de {name}:",
        "admin_open_notice": "Pedidos abiertos. Envia tu pedido ahora.",
        "admin_remind_notice": "Recordatorio: pedidos abiertos.",
        "auto_open_client": "Se abrio una nueva ventana de pedidos.{deadline}",
        "deadline_suffix": " Haz tu pedido antes de {day} {time}.",
    },
}

BUTTONS = {
    "new_order": {"ru": "🆕 Новый заказ", "es": "🆕 Nuevo pedido"},
    "my_orders": {"ru": "📦 Мои заказы", "es": "📦 Mis pedidos"},
    "open_orders": {"ru": "🟢 Открыть прием", "es": "🟢 Abrir pedidos"},
    "close_orders": {"ru": "🔴 Закрыть прием", "es": "🔴 Cerrar pedidos"},
    "summary": {"ru": "📊 Сводка", "es": "📊 Resumen"},
    "excel": {"ru": "📑 Excel", "es": "📑 Excel"},
    "catalog": {"ru": "🍨 Каталог", "es": "🍨 Catalogo"},
    "clients": {"ru": "👥 Клиенты", "es": "👥 Clientes"},
    "remind": {"ru": "🔔 Напомнить", "es": "🔔 Recordar"},
    "switch_lang": {"ru": "🌐 Язык", "es": "🌐 Idioma"},
    "switch_mode": {"ru": "🔀 Режим", "es": "🔀 Modo"},
    "home": {"ru": "🏠 Главное меню", "es": "🏠 Menu"},
}

LEGACY_MATCHES = {
    "new_order": {"Nuevo pedido"},
    "my_orders": {"Mis pedidos"},
    "open_orders": {"Abrir pedidos"},
    "close_orders": {"Cerrar pedidos"},
    "summary": {"Resumen"},
    "excel": {"Excel"},
    "catalog": {"Catalogo"},
    "clients": {"Clientes"},
    "remind": {"Recordar"},
}


def normalize_lang(lang: str | None) -> str:
    value = (lang or "").strip().lower()
    if value in SUPPORTED_LANGS:
        return value
    return "ru"


def t(lang: str, key: str, **kwargs: object) -> str:
    lang = normalize_lang(lang)
    text = TRANSLATIONS.get(lang, {}).get(key)
    if text is None:
        text = TRANSLATIONS["ru"].get(key, key)
    return text.format(**kwargs)


def b(lang: str, key: str) -> str:
    lang = normalize_lang(lang)
    values = BUTTONS.get(key, {})
    return values.get(lang) or values.get("ru") or key


def action_match(text: str | None, action: str) -> bool:
    if not text:
        return False
    labels = set(BUTTONS.get(action, {}).values())
    labels.update(LEGACY_MATCHES.get(action, set()))
    return text.strip() in labels


def action_labels(action: str) -> set[str]:
    labels = set(BUTTONS.get(action, {}).values())
    labels.update(LEGACY_MATCHES.get(action, set()))
    return labels


def status_text(lang: str, status: str) -> str:
    map_ru = {"approved": "Подтвержден", "pending": "На проверке", "blocked": "Заблокирован"}
    map_es = {"approved": "Aprobado", "pending": "Pendiente", "blocked": "Bloqueado"}
    src = map_ru if normalize_lang(lang) == "ru" else map_es
    return src.get(status, status)


def day_name(lang: str, day_code: str) -> str:
    ru = {"MON": "пн", "TUE": "вт", "WED": "ср", "THU": "чт", "FRI": "пт", "SAT": "сб", "SUN": "вс"}
    es = {"MON": "lunes", "TUE": "martes", "WED": "miercoles", "THU": "jueves", "FRI": "viernes", "SAT": "sabado", "SUN": "domingo"}
    source = ru if normalize_lang(lang) == "ru" else es
    return source.get(day_code, day_code)
