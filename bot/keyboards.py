from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.locales import b, normalize_lang, status_text


def client_main_kb(lang: str) -> ReplyKeyboardMarkup:
    lang = normalize_lang(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=b(lang, "new_order")), KeyboardButton(text=b(lang, "my_orders"))],
            [KeyboardButton(text=b(lang, "switch_mode")), KeyboardButton(text=b(lang, "switch_lang"))],
        ],
        resize_keyboard=True,
    )


def admin_main_kb(lang: str) -> ReplyKeyboardMarkup:
    lang = normalize_lang(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=b(lang, "open_orders")), KeyboardButton(text=b(lang, "close_orders"))],
            [KeyboardButton(text=b(lang, "summary")), KeyboardButton(text=b(lang, "excel"))],
            [KeyboardButton(text=b(lang, "catalog")), KeyboardButton(text=b(lang, "catalog_sync"))],
            [KeyboardButton(text=b(lang, "clients"))],
            [KeyboardButton(text=b(lang, "remind"))],
            [KeyboardButton(text=b(lang, "switch_mode")), KeyboardButton(text=b(lang, "switch_lang"))],
        ],
        resize_keyboard=True,
    )


def menu_kb(lang: str, mode: str) -> ReplyKeyboardMarkup:
    return admin_main_kb(lang) if mode == "admin" else client_main_kb(lang)


def confirm_order_kb(lang: str) -> InlineKeyboardMarkup:
    lang = normalize_lang(lang)
    labels = {
        "ru": ("✅ Подтвердить", "📝 Изменить", "✖ Отменить"),
        "es": ("✅ Confirmar", "📝 Cambiar", "✖ Cancelar"),
    }
    confirm, edit, cancel = labels.get(lang, labels["ru"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=confirm, callback_data="order:confirm"),
                InlineKeyboardButton(text=edit, callback_data="order:edit"),
                InlineKeyboardButton(text=cancel, callback_data="order:cancel"),
            ]
        ]
    )


def skip_product_kb(lang: str) -> InlineKeyboardMarkup:
    text = "Пропустить (0)" if normalize_lang(lang) == "ru" else "Saltar (0)"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data="order:skip")]]
    )


def approve_client_kb(client_id: int, lang: str) -> InlineKeyboardMarkup:
    lang = normalize_lang(lang)
    approve = "✅ Одобрить" if lang == "ru" else "✅ Aprobar"
    reject = "⛔ Отклонить" if lang == "ru" else "⛔ Bloquear"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=approve, callback_data=f"client:approve:{client_id}"),
                InlineKeyboardButton(text=reject, callback_data=f"client:block:{client_id}"),
            ]
        ]
    )


def client_list_kb(clients: list[dict], lang: str) -> InlineKeyboardMarkup:
    lang = normalize_lang(lang)
    rows: list[list[InlineKeyboardButton]] = []
    for client in clients:
        icon = {"approved": "✅", "pending": "🕒", "blocked": "⛔"}.get(client["status"], "•")
        label = f"{icon} {client['name']}"
        if client.get("company"):
            label += f" ({client['company']})"
        label += f" · {status_text(lang, client['status'])}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"client:info:{client['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def client_actions_kb(client_id: int, status: str, lang: str) -> InlineKeyboardMarkup:
    lang = normalize_lang(lang)
    approve = "✅ Одобрить" if lang == "ru" else "✅ Aprobar"
    block = "⛔ Блок" if lang == "ru" else "⛔ Bloquear"

    buttons: list[InlineKeyboardButton] = []
    if status in {"pending", "blocked"}:
        buttons.append(InlineKeyboardButton(text=approve, callback_data=f"client:approve:{client_id}"))
    if status != "blocked":
        buttons.append(InlineKeyboardButton(text=block, callback_data=f"client:block:{client_id}"))

    return InlineKeyboardMarkup(inline_keyboard=[buttons] if buttons else [])


def catalog_kb(products: list[dict], lang: str) -> InlineKeyboardMarkup:
    lang = normalize_lang(lang)
    add_label = "➕ Добавить" if lang == "ru" else "➕ Anadir"

    rows: list[list[InlineKeyboardButton]] = []
    for p in products:
        rows.append(
            [
                InlineKeyboardButton(text=p["name"], callback_data=f"catalog:noop:{p['id']}"),
                InlineKeyboardButton(text="⬆", callback_data=f"catalog:up:{p['id']}"),
                InlineKeyboardButton(text="⬇", callback_data=f"catalog:down:{p['id']}"),
                InlineKeyboardButton(text="✖", callback_data=f"catalog:del:{p['id']}"),
            ]
        )
    rows.append([InlineKeyboardButton(text=add_label, callback_data="catalog:add")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇪🇸 Espanol", callback_data="lang:es"),
            ]
        ]
    )


def mode_kb(lang: str) -> InlineKeyboardMarkup:
    ru = normalize_lang(lang) == "ru"
    client_text = "👤 Клиент" if ru else "👤 Cliente"
    admin_text = "🛠 Админ" if ru else "🛠 Admin"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=client_text, callback_data="mode:client"),
                InlineKeyboardButton(text=admin_text, callback_data="mode:admin"),
            ]
        ]
    )
