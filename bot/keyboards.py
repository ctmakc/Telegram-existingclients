from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


# ==================== Client keyboards ====================

def client_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Nuevo pedido"), KeyboardButton(text="Mis pedidos")],
        ],
        resize_keyboard=True,
    )


def confirm_order_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Confirmar", callback_data="order:confirm"),
            InlineKeyboardButton(text="Cambiar", callback_data="order:edit"),
            InlineKeyboardButton(text="Cancelar", callback_data="order:cancel"),
        ],
    ])


def skip_product_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Saltar (0)", callback_data="order:skip")],
    ])


# ==================== Admin keyboards ====================

def admin_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Abrir pedidos"), KeyboardButton(text="Cerrar pedidos")],
            [KeyboardButton(text="Resumen"), KeyboardButton(text="Excel")],
            [KeyboardButton(text="Catalogo"), KeyboardButton(text="Clientes")],
            [KeyboardButton(text="Recordar")],
        ],
        resize_keyboard=True,
    )


def approve_client_kb(client_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Aprobar", callback_data=f"client:approve:{client_id}"),
            InlineKeyboardButton(text="Rechazar", callback_data=f"client:block:{client_id}"),
        ],
    ])


def client_list_kb(clients: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for c in clients:
        status_icon = {"approved": "", "pending": "?", "blocked": "X"}.get(c["status"], "")
        label = f"{status_icon} {c['name']}"
        if c.get("company"):
            label += f" ({c['company']})"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"client:info:{c['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def client_actions_kb(client_id: int, status: str) -> InlineKeyboardMarkup:
    buttons = []
    if status == "pending":
        buttons.append(InlineKeyboardButton(text="Aprobar", callback_data=f"client:approve:{client_id}"))
    if status != "blocked":
        buttons.append(InlineKeyboardButton(text="Bloquear", callback_data=f"client:block:{client_id}"))
    if status == "blocked":
        buttons.append(InlineKeyboardButton(text="Aprobar", callback_data=f"client:approve:{client_id}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons] if buttons else [])


def catalog_kb(products: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for p in products:
        buttons.append([
            InlineKeyboardButton(text=p["name"], callback_data=f"catalog:noop:{p['id']}"),
            InlineKeyboardButton(text="^", callback_data=f"catalog:up:{p['id']}"),
            InlineKeyboardButton(text="v", callback_data=f"catalog:down:{p['id']}"),
            InlineKeyboardButton(text="X", callback_data=f"catalog:del:{p['id']}"),
        ])
    buttons.append([InlineKeyboardButton(text="+ Anadir producto", callback_data="catalog:add")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
