from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot import db
from bot.config import config
from bot.keyboards import (
    admin_main_kb,
    catalog_kb,
    client_actions_kb,
    client_group_assign_kb,
    client_list_kb,
    group_actions_kb,
    groups_kb,
)
from bot.locales import action_labels, status_text, t
from bot.utils.catalog_scraper import fetch_flavors_async
from bot.utils.excel import generate_excel

router = Router()
logger = logging.getLogger(__name__)


class AddProduct(StatesGroup):
    name = State()


class AddGroup(StatesGroup):
    name = State()


class AddAdmin(StatesGroup):
    telegram_id = State()


async def _is_admin_view(user_id: int) -> bool:
    return await db.is_admin_user(user_id)


def _is_superadmin(user_id: int) -> bool:
    return config.is_superadmin(user_id)


async def _admin_guard(message: Message) -> tuple[bool, str]:
    lang = await db.get_user_language(message.from_user.id)
    if not await _is_admin_view(message.from_user.id):
        await message.answer(t(lang, "admin_only_mode"))
        return False, lang
    return True, lang


async def _superadmin_guard_message(message: Message) -> tuple[bool, str]:
    lang = await db.get_user_language(message.from_user.id)
    if not _is_superadmin(message.from_user.id):
        await message.answer(t(lang, "superadmin_only"))
        return False, lang
    return True, lang


async def _superadmin_guard_callback(callback: CallbackQuery) -> tuple[bool, str]:
    lang = await db.get_user_language(callback.from_user.id)
    if not _is_superadmin(callback.from_user.id):
        await callback.answer()
        await callback.message.answer(t(lang, "superadmin_only"))
        return False, lang
    return True, lang


def _admin_role_label(lang: str, role: str) -> str:
    labels = {
        "superadmin": t(lang, "admin_role_superadmin"),
        "admin_env": t(lang, "admin_role_fixed"),
        "admin": t(lang, "admin_role_admin"),
    }
    return labels.get(role, role)


def _admins_manage_kb(profiles: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for profile in profiles:
        if profile["role"] != "admin":
            continue
        label = f"➖ {profile['telegram_id']}"
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"admins:remove:{profile['telegram_id']}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=t(lang, "admins_add_button"), callback_data="admins:add")])
    rows.append([InlineKeyboardButton(text=t(lang, "admins_refresh"), callback_data="admins:refresh")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _send_group_reminder(bot, group_id: int) -> tuple[int, int, str]:
    group = await db.get_client_group(group_id)
    if not group:
        return 0, 0, ""
    session = await db.get_active_session()
    if not session:
        return -1, -1, group["name"]

    clients = await db.get_clients_without_order(session["id"], group_id=group_id)
    sent = 0
    for client in clients:
        try:
            client_lang = await db.get_user_language(client["telegram_id"])
            await bot.send_message(client["telegram_id"], t(client_lang, "admin_remind_notice"))
            sent += 1
        except Exception:
            logger.warning("Failed to send group reminder to %s", client["telegram_id"])
    return sent, len(clients), group["name"]


async def _render_admins_panel(lang: str) -> tuple[str, InlineKeyboardMarkup]:
    profiles = await db.list_admin_profiles()
    lines = [t(lang, "admins_title")]
    if not profiles:
        lines.append(t(lang, "admins_empty"))
        return "\n".join(lines), _admins_manage_kb([], lang)

    for profile in profiles:
        role = _admin_role_label(lang, profile["role"])
        suffix = ""
        if profile.get("name"):
            suffix = f" - {profile['name']}"
            if profile.get("company"):
                suffix += f" ({profile['company']})"
        lines.append(f"• {profile['telegram_id']} [{role}]{suffix}")
    return "\n".join(lines), _admins_manage_kb(profiles, lang)


@router.message(Command("admins"))
@router.message(F.text.in_(action_labels("admins")))
async def manage_admins(message: Message) -> None:
    allowed, lang = await _superadmin_guard_message(message)
    if not allowed:
        return
    text, kb = await _render_admins_panel(lang)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "admins:add")
async def admins_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    allowed, lang = await _superadmin_guard_callback(callback)
    if not allowed:
        return
    await callback.answer()
    await callback.message.answer(t(lang, "admins_add_prompt"))
    await state.set_state(AddAdmin.telegram_id)


@router.message(AddAdmin.telegram_id)
async def admins_add_finish(message: Message, state: FSMContext) -> None:
    allowed, lang = await _superadmin_guard_message(message)
    if not allowed:
        await state.clear()
        return

    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(t(lang, "admins_invalid_id"))
        return

    telegram_id = int(raw)
    if telegram_id <= 0:
        await message.answer(t(lang, "admins_invalid_id"))
        return

    if config.is_superadmin(telegram_id):
        await state.clear()
        await message.answer(t(lang, "admins_already_superadmin"))
        return

    if await db.is_admin_user(telegram_id):
        await state.clear()
        await message.answer(t(lang, "admins_already_admin", id=telegram_id))
        return

    await db.add_dynamic_admin(telegram_id, added_by=message.from_user.id)
    await state.clear()
    text, kb = await _render_admins_panel(lang)
    await message.answer(t(lang, "admins_added", id=telegram_id))
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "admins:refresh")
async def admins_refresh(callback: CallbackQuery) -> None:
    allowed, lang = await _superadmin_guard_callback(callback)
    if not allowed:
        return
    text, kb = await _render_admins_panel(lang)
    await callback.answer("OK")
    await callback.message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("admins:remove:"))
async def admins_remove(callback: CallbackQuery) -> None:
    allowed, lang = await _superadmin_guard_callback(callback)
    if not allowed:
        return

    telegram_id = int(callback.data.split(":")[2])
    if config.is_superadmin(telegram_id):
        await callback.answer()
        await callback.message.answer(t(lang, "admins_cannot_remove_superadmin"))
        return
    if telegram_id in config.admin_ids:
        await callback.answer()
        await callback.message.answer(t(lang, "admins_cannot_remove_fixed"))
        return

    removed = await db.remove_dynamic_admin(telegram_id)
    await callback.answer("OK")
    if removed:
        await callback.message.answer(t(lang, "admins_removed", id=telegram_id))
    else:
        await callback.message.answer(t(lang, "admins_not_found", id=telegram_id))
    text, kb = await _render_admins_panel(lang)
    await callback.message.answer(text, reply_markup=kb)


@router.message(F.text.in_(action_labels("open_orders")))
async def open_orders(message: Message) -> None:
    allowed, lang = await _admin_guard(message)
    if not allowed:
        return

    session = await db.get_active_session()
    if session:
        await message.answer(t(lang, "session_exists"))
        return

    session_id = await db.open_session()
    clients = await db.get_approved_clients()

    sent = 0
    for client in clients:
        try:
            client_lang = await db.get_user_language(client["telegram_id"])
            await message.bot.send_message(client["telegram_id"], t(client_lang, "admin_open_notice"))
            sent += 1
        except Exception:
            logger.warning("Failed to notify client %s about open session", client["telegram_id"])

    await message.answer(
        t(lang, "session_opened", id=session_id, sent=sent, total=len(clients)),
        reply_markup=admin_main_kb(lang),
    )


@router.message(F.text.in_(action_labels("close_orders")))
async def close_orders(message: Message) -> None:
    allowed, lang = await _admin_guard(message)
    if not allowed:
        return

    session = await db.get_active_session()
    if not session:
        await message.answer(t(lang, "no_open_session"))
        return

    await db.close_session()
    count = await db.count_session_orders(session["id"])
    total_clients = len(await db.get_approved_clients())
    await message.answer(
        t(lang, "session_closed", count=count, total=total_clients),
        reply_markup=admin_main_kb(lang),
    )


@router.message(F.text.in_(action_labels("summary")))
async def summary(message: Message) -> None:
    allowed, lang = await _admin_guard(message)
    if not allowed:
        return

    session = await db.get_active_session()
    if session:
        session_id = session["id"]
    else:
        _db = await db.get_db()
        try:
            cur = await _db.execute("SELECT id FROM order_sessions ORDER BY id DESC LIMIT 1")
            row = await cur.fetchone()
            if not row:
                await message.answer(t(lang, "no_sessions"))
                return
            session_id = row["id"]
        finally:
            await _db.close()

    summary_data = await db.get_session_summary(session_id)
    count = await db.count_session_orders(session_id)
    total_clients = len(await db.get_approved_clients())

    if not summary_data:
        await message.answer(t(lang, "summary_empty", id=session_id, count=count, total=total_clients))
        return

    lines = [f"📊 {t(lang, 'summary_title', id=session_id)}", t(lang, "summary_orders", count=count, total=total_clients), ""]
    grand_total = 0
    for item in summary_data:
        lines.append(f"• {item['name']}: {item['total']}")
        grand_total += item["total"]
    lines.append("")
    lines.append(t(lang, "summary_grand", total=grand_total))
    await message.answer("\n".join(lines))


@router.message(F.text.in_(action_labels("excel")))
async def export_excel(message: Message) -> None:
    allowed, lang = await _admin_guard(message)
    if not allowed:
        return

    session = await db.get_active_session()
    if not session:
        _db = await db.get_db()
        try:
            cur = await _db.execute("SELECT * FROM order_sessions ORDER BY id DESC LIMIT 1")
            row = await cur.fetchone()
            if not row:
                await message.answer(t(lang, "no_sessions"))
                return
            session = dict(row)
        finally:
            await _db.close()

    orders = await db.get_session_orders(session["id"])
    products = await db.get_active_products()
    if not orders:
        await message.answer(t(lang, "excel_no_orders"))
        return

    try:
        file_path = await generate_excel(orders, products, session["id"])
    except ModuleNotFoundError:
        await message.answer("openpyxl not installed. Run: pip install -r requirements.txt")
        return
    await message.answer_document(FSInputFile(str(file_path), filename=file_path.name))


@router.message(F.text.in_(action_labels("catalog")))
async def show_catalog(message: Message) -> None:
    allowed, lang = await _admin_guard(message)
    if not allowed:
        return

    products = await db.get_active_products()
    if not products:
        await message.answer(t(lang, "catalog_empty"), reply_markup=catalog_kb([], lang))
        return

    await message.answer(t(lang, "catalog_title"), reply_markup=catalog_kb(products, lang))


@router.message(Command("sync_catalog"))
@router.message(F.text.in_(action_labels("catalog_sync")))
async def sync_catalog_from_site(message: Message) -> None:
    allowed, lang = await _admin_guard(message)
    if not allowed:
        return

    await message.answer(t(lang, "catalog_sync_started"))
    try:
        names = await fetch_flavors_async(config.catalog_source_url)
        if not names:
            await message.answer(t(lang, "catalog_sync_empty"))
            return

        stats = await db.sync_products_catalog(names)
        products = await db.get_active_products()
        await message.answer(
            t(
                lang,
                "catalog_sync_done",
                total=stats["total_incoming"],
                matched=stats["matched"],
                added=stats["added"],
                reactivated=stats["reactivated"],
                kept_extra=stats["kept_extra"],
            ),
            reply_markup=catalog_kb(products, lang),
        )
    except Exception:
        logger.exception("Failed to sync catalog from site")
        await message.answer(t(lang, "catalog_sync_failed"))


@router.callback_query(F.data == "catalog:add")
async def catalog_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _is_admin_view(callback.from_user.id):
        await callback.answer()
        return
    lang = await db.get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.answer(t(lang, "product_prompt"))
    await state.set_state(AddProduct.name)


@router.message(AddProduct.name)
async def catalog_add_finish(message: Message, state: FSMContext) -> None:
    allowed, lang = await _admin_guard(message)
    if not allowed:
        return

    name = (message.text or "").strip()
    if not name:
        await message.answer(t(lang, "name_empty"))
        return

    await db.add_product(name)
    await state.clear()
    products = await db.get_active_products()
    await message.answer(t(lang, "product_added", name=name), reply_markup=catalog_kb(products, lang))


@router.callback_query(F.data.startswith("catalog:del:"))
async def catalog_delete(callback: CallbackQuery) -> None:
    if not await _is_admin_view(callback.from_user.id):
        await callback.answer()
        return

    product_id = int(callback.data.split(":")[2])
    await db.delete_product(product_id)
    lang = await db.get_user_language(callback.from_user.id)
    products = await db.get_active_products()
    await callback.answer("OK")
    await callback.message.edit_reply_markup(reply_markup=catalog_kb(products, lang))


@router.callback_query(F.data.startswith("catalog:up:"))
async def catalog_move_up(callback: CallbackQuery) -> None:
    if not await _is_admin_view(callback.from_user.id):
        await callback.answer()
        return

    product_id = int(callback.data.split(":")[2])
    await db.move_product(product_id, "up")
    lang = await db.get_user_language(callback.from_user.id)
    products = await db.get_active_products()
    await callback.answer("OK")
    await callback.message.edit_reply_markup(reply_markup=catalog_kb(products, lang))


@router.callback_query(F.data.startswith("catalog:down:"))
async def catalog_move_down(callback: CallbackQuery) -> None:
    if not await _is_admin_view(callback.from_user.id):
        await callback.answer()
        return

    product_id = int(callback.data.split(":")[2])
    await db.move_product(product_id, "down")
    lang = await db.get_user_language(callback.from_user.id)
    products = await db.get_active_products()
    await callback.answer("OK")
    await callback.message.edit_reply_markup(reply_markup=catalog_kb(products, lang))


@router.callback_query(F.data.startswith("catalog:noop:"))
async def catalog_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.message(F.text.in_(action_labels("groups")))
async def show_groups(message: Message) -> None:
    allowed, lang = await _admin_guard(message)
    if not allowed:
        return

    groups = await db.get_client_groups()
    if not groups:
        await message.answer(t(lang, "groups_empty"), reply_markup=groups_kb([], lang))
        return
    await message.answer(t(lang, "groups_title"), reply_markup=groups_kb(groups, lang))


@router.callback_query(F.data == "group:add")
async def group_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _is_admin_view(callback.from_user.id):
        await callback.answer()
        return
    lang = await db.get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.answer(t(lang, "group_prompt"))
    await state.set_state(AddGroup.name)


@router.message(AddGroup.name)
async def group_add_finish(message: Message, state: FSMContext) -> None:
    allowed, lang = await _admin_guard(message)
    if not allowed:
        return

    name = (message.text or "").strip()
    if not name:
        await message.answer(t(lang, "group_name_empty"))
        return

    try:
        await db.add_client_group(name)
    except Exception as exc:
        await state.clear()
        groups = await db.get_client_groups()
        if "UNIQUE" in str(exc).upper():
            await message.answer(t(lang, "group_exists"), reply_markup=groups_kb(groups, lang))
            return
        logger.exception("Failed to add client group")
        await message.answer(t(lang, "group_add_failed"), reply_markup=groups_kb(groups, lang))
        return

    await state.clear()
    groups = await db.get_client_groups()
    await message.answer(t(lang, "group_added", name=name), reply_markup=groups_kb(groups, lang))


@router.callback_query(F.data.startswith("group:view:"))
async def group_view(callback: CallbackQuery) -> None:
    if not await _is_admin_view(callback.from_user.id):
        await callback.answer()
        return
    group_id = int(callback.data.split(":")[2])
    group = await db.get_client_group(group_id)
    if not group:
        await callback.answer()
        return

    session = await db.get_active_session()
    without_order = 0
    if session:
        without_order = len(await db.get_clients_without_order(session["id"], group_id=group_id))

    lang = await db.get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.answer(
        t(
            lang,
            "group_details",
            name=group["name"],
            clients_total=group.get("clients_total", 0),
            approved_total=group.get("approved_total", 0),
            without_order=without_order,
        ),
        reply_markup=group_actions_kb(group_id, lang),
    )


@router.callback_query(F.data.startswith("group:remind:"))
async def group_remind(callback: CallbackQuery) -> None:
    if not await _is_admin_view(callback.from_user.id):
        await callback.answer()
        return
    group_id = int(callback.data.split(":")[2])
    lang = await db.get_user_language(callback.from_user.id)
    sent, total, _group_name = await _send_group_reminder(callback.bot, group_id)
    if sent == -1 and total == -1:
        await callback.answer()
        await callback.message.answer(t(lang, "group_no_open_session"))
        return
    await callback.answer("OK")
    if total == 0:
        await callback.message.answer(t(lang, "group_remind_none"))
        return
    await callback.message.answer(t(lang, "group_remind_sent", sent=sent, total=total))


@router.message(F.text.in_(action_labels("clients")))
async def show_clients(message: Message) -> None:
    allowed, lang = await _admin_guard(message)
    if not allowed:
        return

    clients = await db.get_all_clients()
    if not clients:
        await message.answer(t(lang, "clients_empty"))
        return

    await message.answer(t(lang, "clients_title"), reply_markup=client_list_kb(clients, lang))


@router.callback_query(F.data.startswith("client:info:"))
async def client_info(callback: CallbackQuery) -> None:
    if not await _is_admin_view(callback.from_user.id):
        await callback.answer()
        return

    client_id = int(callback.data.split(":")[2])
    _db = await db.get_db()
    try:
        cur = await _db.execute(
            """
            SELECT c.*, g.name AS group_name
            FROM clients c
            LEFT JOIN client_groups g ON g.id = c.group_id
            WHERE c.id = ?
            """,
            (client_id,),
        )
        row = await cur.fetchone()
        if not row:
            await callback.answer()
            return
        client = dict(row)
    finally:
        await _db.close()

    lang = await db.get_user_language(callback.from_user.id)
    text = "\n".join(
        [
            f"👤 {client['name']}",
            t(lang, "client_company", company=client.get("company") or "-"),
            t(lang, "client_group", group=client.get("group_name") or "-"),
            t(lang, "client_status", status=status_text(lang, client["status"])),
            t(lang, "registered_at", date=client["created_at"][:16]),
        ]
    )
    await callback.answer()
    await callback.message.answer(text, reply_markup=client_actions_kb(client_id, client["status"], lang))


@router.callback_query(F.data.startswith("client:groupmenu:"))
async def client_group_menu(callback: CallbackQuery) -> None:
    if not await _is_admin_view(callback.from_user.id):
        await callback.answer()
        return
    client_id = int(callback.data.split(":")[2])
    groups = await db.get_client_groups()
    lang = await db.get_user_language(callback.from_user.id)
    await callback.answer()
    await callback.message.answer(
        t(lang, "choose_group_for_client"),
        reply_markup=client_group_assign_kb(client_id, groups, lang),
    )


@router.callback_query(F.data.startswith("client:setgroup:"))
async def client_set_group(callback: CallbackQuery) -> None:
    if not await _is_admin_view(callback.from_user.id):
        await callback.answer()
        return
    _, _, client_id_s, group_id_s = callback.data.split(":", 3)
    client_id = int(client_id_s)
    group_id = int(group_id_s)
    await db.set_client_group(client_id, None if group_id == 0 else group_id)
    lang = await db.get_user_language(callback.from_user.id)
    await callback.answer("OK")
    await callback.message.answer(t(lang, "client_group_set"))


@router.callback_query(F.data.startswith("client:approve:"))
async def approve_client(callback: CallbackQuery) -> None:
    if not await _is_admin_view(callback.from_user.id):
        await callback.answer()
        return

    client_id = int(callback.data.split(":")[2])
    await db.approve_client(client_id)

    _db = await db.get_db()
    try:
        cur = await _db.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        row = await cur.fetchone()
        if not row:
            await callback.answer()
            return
        client = dict(row)
    finally:
        await _db.close()

    lang = await db.get_user_language(callback.from_user.id)
    await callback.answer("OK")
    await callback.message.edit_text(t(lang, "client_approved", name=client["name"]))

    try:
        client_lang = await db.get_user_language(client["telegram_id"])
        from bot.keyboards import menu_kb

        user_mode = await db.get_user_mode(client["telegram_id"])
        is_admin = await db.is_admin_user(client["telegram_id"])
        mode = "admin" if is_admin and user_mode == "admin" else "client"
        await callback.bot.send_message(
            client["telegram_id"],
            t(client_lang, "client_approved", name=client["name"]),
            reply_markup=menu_kb(client_lang, mode),
        )
    except Exception:
        logger.exception("Failed to notify approved client %s", client["telegram_id"])


@router.callback_query(F.data.startswith("client:block:"))
async def block_client(callback: CallbackQuery) -> None:
    if not await _is_admin_view(callback.from_user.id):
        await callback.answer()
        return

    client_id = int(callback.data.split(":")[2])
    await db.block_client(client_id)
    lang = await db.get_user_language(callback.from_user.id)
    await callback.answer("OK")
    await callback.message.edit_text(t(lang, "client_blocked"))


@router.message(F.text.in_(action_labels("remind")))
async def remind_clients(message: Message) -> None:
    allowed, lang = await _admin_guard(message)
    if not allowed:
        return

    session = await db.get_active_session()
    if not session:
        await message.answer(t(lang, "no_open_session"))
        return

    clients = await db.get_clients_without_order(session["id"])
    if not clients:
        await message.answer(t(lang, "remind_all_done"))
        return

    sent = 0
    for client in clients:
        try:
            client_lang = await db.get_user_language(client["telegram_id"])
            await message.bot.send_message(client["telegram_id"], t(client_lang, "admin_remind_notice"))
            sent += 1
        except Exception:
            logger.warning("Failed to send reminder to %s", client["telegram_id"])

    await message.answer(t(lang, "remind_sent", sent=sent, total=len(clients)))
