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
        "order_editor_title": "Каталог. Нажимайте + / - для количества.",
        "order_editor_hint": "Используйте кнопки + / - / ✖ под товарами, затем нажмите «Подтвердить».",
        "order_confirmed": "Заказ подтвержден.",
        "order_cancelled": "Заказ отменен.",
        "my_orders_empty": "У тебя пока нет заказов.",
        "my_order_title": "Заказ от {date}:",
        "total_units": "Итого: {units} ед.",
        "lang_changed": "Язык переключен: Русский.",
        "mode_changed_client": "Режим: клиент.",
        "mode_changed_admin": "Режим: админ.",
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
        "catalog_sync_started": "Обновляю каталог с сайта...",
        "catalog_sync_empty": "Не удалось получить список вкусов с сайта.",
        "catalog_sync_done": "Каталог синхронизирован с сайтом.\nНайдено позиций: {total}\nСовпало: {matched}\nДобавлено: {added}\nВосстановлено: {reactivated}\nСохранено ваших доп. позиций: {kept_extra}",
        "catalog_sync_failed": "Не удалось обновить каталог с сайта.",
        "product_added": "Добавлено: {name}",
        "product_prompt": "Введи название нового продукта:",
        "name_empty": "Название не может быть пустым.",
        "clients_empty": "Клиентов пока нет.",
        "clients_title": "Клиенты:",
        "client_group": "Группа: {group}",
        "client_approved": "Клиент {name} подтвержден.",
        "client_blocked": "Клиент заблокирован.",
        "groups_empty": "Групп пока нет.",
        "groups_title": "Группы клиентов (маршруты/локации):",
        "group_prompt": "Введи название группы (например: Валенсия Центр / Маршрут A).",
        "group_added": "Группа создана: {name}",
        "group_exists": "Такая группа уже существует.",
        "group_add_failed": "Не удалось создать группу.",
        "group_name_empty": "Название группы не может быть пустым.",
        "group_details": "Группа: {name}\nКлиентов: {clients_total}\nОдобрено: {approved_total}\nБез заказа в текущей сессии: {without_order}",
        "group_no_open_session": "Нет открытой сессии. Открой прием заказов перед напоминанием группе.",
        "group_remind_none": "В этой группе нет одобренных клиентов без заказа.",
        "group_remind_sent": "Напоминание группе отправлено: {sent}/{total}.",
        "choose_group_for_client": "Выбери группу для клиента:",
        "client_group_set": "Группа клиента обновлена.",
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
        "superadmin_only": "Этот раздел доступен только суперадмину.",
        "admins_title": "Список админов:",
        "admins_empty": "Админов пока нет.",
        "admins_add_prompt": "Отправьте Telegram ID пользователя для выдачи роли админа.",
        "admins_invalid_id": "Нужен корректный Telegram ID (только цифры).",
        "admins_added": "Добавлен админ: {id}",
        "admins_removed": "Удален админ: {id}",
        "admins_not_found": "Админ не найден: {id}",
        "admins_already_admin": "Этот ID уже админ: {id}",
        "admins_already_superadmin": "Этот ID уже является суперадмином.",
        "admins_cannot_remove_superadmin": "Суперадмина удалить нельзя.",
        "admins_cannot_remove_fixed": "Этот админ задан в .env и не удаляется из бота.",
        "admin_role_superadmin": "superadmin",
        "admin_role_fixed": "admin(env)",
        "admin_role_admin": "admin",
        "admins_add_button": "➕ Добавить админа",
        "admins_refresh": "🔄 Обновить",
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
        "order_editor_title": "Catalogo. Usa + / - para ajustar cantidades.",
        "order_editor_hint": "Usa los botones + / - / ✖ debajo de cada producto y luego confirma.",
        "order_confirmed": "Pedido confirmado.",
        "order_cancelled": "Pedido cancelado.",
        "my_orders_empty": "Aun no tienes pedidos.",
        "my_order_title": "Pedido de {date}:",
        "total_units": "Total: {units} uds.",
        "lang_changed": "Idioma cambiado: Espanol.",
        "mode_changed_client": "Modo: cliente.",
        "mode_changed_admin": "Modo: admin.",
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
        "catalog_sync_started": "Actualizando catalogo desde la web...",
        "catalog_sync_empty": "No se pudo obtener la lista de sabores desde la web.",
        "catalog_sync_done": "Catalogo sincronizado con la web.\nSabores encontrados: {total}\nCoincidencias: {matched}\nAnadidos: {added}\nReactivados: {reactivated}\nExtras conservados: {kept_extra}",
        "catalog_sync_failed": "No se pudo sincronizar el catalogo desde la web.",
        "product_added": "Anadido: {name}",
        "product_prompt": "Escribe el nombre del nuevo producto:",
        "name_empty": "El nombre no puede estar vacio.",
        "clients_empty": "No hay clientes.",
        "clients_title": "Clientes:",
        "client_group": "Grupo: {group}",
        "client_approved": "Cliente {name} aprobado.",
        "client_blocked": "Cliente bloqueado.",
        "groups_empty": "Todavia no hay grupos.",
        "groups_title": "Grupos de clientes (rutas/zonas):",
        "group_prompt": "Escribe el nombre del grupo (por ejemplo: Valencia Centro / Ruta A).",
        "group_added": "Grupo creado: {name}",
        "group_exists": "Ese grupo ya existe.",
        "group_add_failed": "No se pudo crear el grupo.",
        "group_name_empty": "El nombre del grupo no puede estar vacio.",
        "group_details": "Grupo: {name}\nClientes: {clients_total}\nAprobados: {approved_total}\nSin pedido en sesion actual: {without_order}",
        "group_no_open_session": "No hay sesion abierta. Abre pedidos antes de recordar al grupo.",
        "group_remind_none": "En este grupo no hay clientes aprobados sin pedido.",
        "group_remind_sent": "Recordatorio al grupo enviado: {sent}/{total}.",
        "choose_group_for_client": "Elige grupo para el cliente:",
        "client_group_set": "Grupo del cliente actualizado.",
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
        "superadmin_only": "Esta seccion es solo para superadmins.",
        "admins_title": "Lista de admins:",
        "admins_empty": "Todavia no hay admins.",
        "admins_add_prompt": "Envia el Telegram ID del usuario para darle rol admin.",
        "admins_invalid_id": "Telegram ID invalido (solo numeros).",
        "admins_added": "Admin agregado: {id}",
        "admins_removed": "Admin eliminado: {id}",
        "admins_not_found": "Admin no encontrado: {id}",
        "admins_already_admin": "Ese ID ya es admin: {id}",
        "admins_already_superadmin": "Ese ID ya es superadmin.",
        "admins_cannot_remove_superadmin": "No puedes quitar un superadmin.",
        "admins_cannot_remove_fixed": "Ese admin esta fijo en .env y no se elimina desde el bot.",
        "admin_role_superadmin": "superadmin",
        "admin_role_fixed": "admin(env)",
        "admin_role_admin": "admin",
        "admins_add_button": "➕ Agregar admin",
        "admins_refresh": "🔄 Refrescar",
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
    "catalog_sync": {"ru": "🌐 Синк с сайта", "es": "🌐 Sync web"},
    "clients": {"ru": "👥 Клиенты", "es": "👥 Clientes"},
    "groups": {"ru": "🗂 Группы", "es": "🗂 Grupos"},
    "remind": {"ru": "🔔 Напомнить", "es": "🔔 Recordar"},
    "admins": {"ru": "🛡 Админы", "es": "🛡 Admins"},
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
    "catalog_sync": {"Sync web"},
    "clients": {"Clientes"},
    "groups": {"Grupos"},
    "remind": {"Recordar"},
    "admins": {"Admins"},
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
