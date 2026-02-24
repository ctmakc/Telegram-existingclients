from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import db
from bot.config import config
from bot.keyboards import (
    approve_client_kb,
    confirm_order_kb,
    language_kb,
    menu_kb,
    mode_kb,
    skip_product_kb,
)
from bot.locales import action_match, normalize_lang, t

router = Router()
logger = logging.getLogger(__name__)


class Registration(StatesGroup):
    name = State()
    company = State()


class OrderFlow(StatesGroup):
    entering_quantity = State()


def _version_text() -> str:
    return f"v{config.bot_version} (image:{config.image_tag})"


def _user_id(message_or_callback: Message | CallbackQuery) -> int:
    if isinstance(message_or_callback, CallbackQuery):
        return message_or_callback.from_user.id
    return message_or_callback.from_user.id


async def _lang_mode(user_id: int) -> tuple[str, str]:
    pref = await db.get_user_pref(user_id)
    lang = normalize_lang(pref.get("language"))
    mode = pref.get("ui_mode") or "client"
    return lang, mode


async def _is_admin_view(user_id: int) -> bool:
    if config.is_admin(user_id):
        return True
    return (await db.get_user_mode(user_id)) == "admin"


async def _show_menu(target: Message | CallbackQuery) -> None:
    user_id = _user_id(target)
    lang, mode = await _lang_mode(user_id)
    title = t(lang, "menu_admin") if mode == "admin" else t(lang, "menu_client")
    text = f"✨ {title}\n{_version_text()}"

    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=menu_kb(lang, mode))
    else:
        await target.answer(text, reply_markup=menu_kb(lang, mode))


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await db.ensure_user_pref(message.from_user.id)
    lang, mode = await _lang_mode(message.from_user.id)

    client = await db.get_client_by_tg(message.from_user.id)
    if client:
        await message.answer(
            f"{t(lang, 'welcome', name=client['name'])}\n{_version_text()}",
            reply_markup=menu_kb(lang, mode),
        )
        return

    if mode == "admin" or config.is_admin(message.from_user.id):
        await _show_menu(message)
        return

    await message.answer(t(lang, "welcome_new"))
    await message.answer(t(lang, "ask_name"))
    await state.set_state(Registration.name)


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await _show_menu(message)


@router.message(Command("lang"))
async def cmd_lang(message: Message) -> None:
    lang = await db.get_user_language(message.from_user.id)
    await message.answer(t(lang, "choose_language"), reply_markup=language_kb())


@router.message(Command("mode"))
async def cmd_mode(message: Message) -> None:
    lang = await db.get_user_language(message.from_user.id)
    await message.answer(t(lang, "choose_mode"), reply_markup=mode_kb(lang))


@router.message(Command("version"))
async def cmd_version(message: Message) -> None:
    await message.answer(f"Version: {_version_text()}")


@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery) -> None:
    lang = callback.data.split(":", 1)[1]
    if lang not in {"ru", "es"}:
        await callback.answer()
        return

    await db.set_user_language(callback.from_user.id, lang)
    await callback.answer("OK")
    await callback.message.answer(t(lang, "lang_changed"), reply_markup=menu_kb(lang, await db.get_user_mode(callback.from_user.id)))


@router.callback_query(F.data.startswith("mode:"))
async def set_mode(callback: CallbackQuery) -> None:
    mode = callback.data.split(":", 1)[1]
    if mode not in {"client", "admin"}:
        await callback.answer()
        return

    await db.set_user_mode(callback.from_user.id, mode)
    lang = await db.get_user_language(callback.from_user.id)
    msg_key = "mode_changed_admin" if mode == "admin" else "mode_changed_client"
    await callback.answer("OK")
    await callback.message.answer(t(lang, msg_key), reply_markup=menu_kb(lang, mode))


@router.message(Registration.name)
async def registration_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        lang = await db.get_user_language(message.from_user.id)
        await message.answer(t(lang, "ask_name"))
        return
    await state.update_data(name=name)
    lang = await db.get_user_language(message.from_user.id)
    await message.answer(t(lang, "ask_company"))
    await state.set_state(Registration.company)


@router.message(Registration.company)
async def registration_company(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    company = (message.text or "").strip()
    company = None if company == "-" else company

    await db.add_client(
        telegram_id=message.from_user.id,
        name=data["name"],
        company=company,
    )
    await state.clear()

    lang = await db.get_user_language(message.from_user.id)
    await message.answer(t(lang, "request_sent"), reply_markup=menu_kb(lang, await db.get_user_mode(message.from_user.id)))

    client = await db.get_client_by_tg(message.from_user.id)
    for admin_id in config.admin_ids:
        try:
            admin_lang = await db.get_user_language(admin_id)
            await message.bot.send_message(
                admin_id,
                t(admin_lang, "new_client_request", name=data["name"], company=company or "-"),
                reply_markup=approve_client_kb(client["id"], admin_lang),
            )
        except Exception:
            logger.warning("Failed to notify admin %s about new client", admin_id)


@router.message(F.text)
async def text_router(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    lang, mode = await _lang_mode(message.from_user.id)

    if action_match(text, "switch_lang"):
        await message.answer(t(lang, "choose_language"), reply_markup=language_kb())
        return

    if action_match(text, "switch_mode"):
        await message.answer(t(lang, "choose_mode"), reply_markup=mode_kb(lang))
        return

    if action_match(text, "home"):
        await _show_menu(message)
        return

    if action_match(text, "new_order"):
        await new_order(message, state)
        return

    if action_match(text, "my_orders"):
        await my_orders(message)
        return


async def new_order(message: Message, state: FSMContext) -> None:
    lang = await db.get_user_language(message.from_user.id)
    client = await db.get_client_by_tg(message.from_user.id)
    if not client:
        await message.answer(t(lang, "welcome_new"))
        await message.answer(t(lang, "ask_name"))
        await state.set_state(Registration.name)
        return

    if client["status"] != "approved":
        await message.answer(t(lang, "pending") if client["status"] == "pending" else t(lang, "blocked"))
        return

    session = await db.get_active_session()
    if not session:
        await message.answer(t(lang, "orders_closed"))
        return

    products = await db.get_active_products()
    if not products:
        await message.answer(t(lang, "no_products"))
        return

    await state.update_data(
        session_id=session["id"],
        client_id=client["id"],
        products=products,
        current_idx=0,
        order_items=[],
        lang=lang,
    )
    await state.set_state(OrderFlow.entering_quantity)
    await _ask_product_quantity(message, state)


async def _ask_product_quantity(target: Message | CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data or "products" not in data:
        await state.clear()
        return

    idx = data["current_idx"]
    products = data["products"]
    lang = data.get("lang") or await db.get_user_language(_user_id(target))

    if idx >= len(products):
        await _show_order_summary(target, state)
        return

    product = products[idx]
    text = t(lang, "qty_prompt", current=idx + 1, total=len(products), product=product["name"])

    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=skip_product_kb(lang))
    else:
        await target.answer(text, reply_markup=skip_product_kb(lang))


@router.callback_query(F.data == "order:skip", OrderFlow.entering_quantity)
async def skip_product(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data or "order_items" not in data:
        await callback.answer()
        await state.clear()
        return

    items = data["order_items"]
    items.append(0)
    await state.update_data(order_items=items, current_idx=data["current_idx"] + 1)
    await callback.answer()
    await _ask_product_quantity(callback, state)


@router.message(OrderFlow.entering_quantity)
async def enter_quantity(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang") if data else await db.get_user_language(message.from_user.id)

    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer(t(lang, "qty_invalid"))
        return

    if not data or "order_items" not in data:
        await state.clear()
        return

    items = data["order_items"]
    items.append(int(text))
    await state.update_data(order_items=items, current_idx=data["current_idx"] + 1)
    await _ask_product_quantity(message, state)


async def _show_order_summary(target: Message | CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data or "products" not in data:
        await state.clear()
        return

    products = data["products"]
    items = data["order_items"]
    lang = data.get("lang") or await db.get_user_language(_user_id(target))

    lines = [f"🧾 {t(lang, 'order_summary')}"]
    total_units = 0
    total_positions = 0
    for product, qty in zip(products, items):
        if qty > 0:
            lines.append(f"• {product['name']} - {qty}")
            total_units += qty
            total_positions += 1

    if total_units == 0:
        if isinstance(target, CallbackQuery):
            await target.message.answer(t(lang, "order_empty"))
        else:
            await target.answer(t(lang, "order_empty"))
        await state.clear()
        return

    lines.append("")
    lines.append(t(lang, "order_total", positions=total_positions, units=total_units))
    text = "\n".join(lines)

    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=confirm_order_kb(lang))
    else:
        await target.answer(text, reply_markup=confirm_order_kb(lang))


@router.callback_query(F.data == "order:confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data or not all(k in data for k in ("products", "order_items", "client_id", "session_id")):
        await state.clear()
        await callback.answer()
        return

    products = data["products"]
    items = data["order_items"]
    lang = data.get("lang") or await db.get_user_language(callback.from_user.id)

    order_items = [(products[i]["id"], items[i]) for i in range(len(products)) if items[i] > 0]
    await db.create_order(client_id=data["client_id"], session_id=data["session_id"], items=order_items)

    await state.clear()
    await callback.answer(t(lang, "order_confirmed"))
    await callback.message.edit_text(callback.message.text + f"\n\n✅ {t(lang, 'order_confirmed')}")

    client = await db.get_client_by_tg(callback.from_user.id)
    for admin_id in config.admin_ids:
        try:
            admin_lang = await db.get_user_language(admin_id)
            lines = [t(admin_lang, "admin_new_order", name=client["name"])]
            for product, qty in zip(products, items):
                if qty > 0:
                    lines.append(f"• {product['name']} - {qty}")
            await callback.bot.send_message(admin_id, "\n".join(lines))
        except Exception:
            logger.warning("Failed to notify admin %s about order", admin_id)


@router.callback_query(F.data == "order:edit")
async def edit_order(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data:
        await callback.answer()
        return
    await state.update_data(current_idx=0, order_items=[])
    await callback.answer()
    await state.set_state(OrderFlow.entering_quantity)
    await _ask_product_quantity(callback, state)


@router.callback_query(F.data == "order:cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await db.get_user_language(callback.from_user.id)
    await state.clear()
    await callback.answer(t(lang, "order_cancelled"))
    await callback.message.edit_text(t(lang, "order_cancelled"))


async def my_orders(message: Message) -> None:
    lang = await db.get_user_language(message.from_user.id)
    client = await db.get_client_by_tg(message.from_user.id)
    if not client or client["status"] != "approved":
        await message.answer(t(lang, "access_denied"))
        return

    orders = await db.get_client_orders(client["id"], limit=5)
    if not orders:
        await message.answer(t(lang, "my_orders_empty"))
        return

    for order in orders:
        lines = [f"📦 {t(lang, 'my_order_title', date=order['created_at'][:16])}"]
        total = 0
        for item in order["items"]:
            lines.append(f"• {item['name']} - {item['quantity']}")
            total += item["quantity"]
        lines.append(t(lang, "total_units", units=total))
        await message.answer("\n".join(lines))
