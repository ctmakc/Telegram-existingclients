from __future__ import annotations

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot import db
from bot.config import config
from bot.keyboards import (
    admin_main_kb,
    catalog_kb,
    client_list_kb,
    client_actions_kb,
)
from bot.utils.excel import generate_excel

router = Router()


class AddProduct(StatesGroup):
    name = State()


# ==================== Admin filter ====================

def _is_admin(message: Message) -> bool:
    return config.is_admin(message.from_user.id)


# ==================== Open / Close orders ====================

@router.message(F.text == "Abrir pedidos")
async def open_orders(message: Message) -> None:
    if not _is_admin(message):
        return
    session = await db.get_active_session()
    if session:
        await message.answer("Ya hay una sesion abierta. Cierra la actual primero.")
        return

    session_id = await db.open_session()
    clients = await db.get_approved_clients()

    sent = 0
    for client in clients:
        try:
            await message.bot.send_message(
                client["telegram_id"],
                "Pedidos abiertos! Haz tu pedido ahora.",
            )
            sent += 1
        except Exception:
            pass

    await message.answer(
        f"Sesion #{session_id} abierta. Notificados: {sent}/{len(clients)} clientes.",
        reply_markup=admin_main_kb(),
    )


@router.message(F.text == "Cerrar pedidos")
async def close_orders(message: Message) -> None:
    if not _is_admin(message):
        return
    session = await db.get_active_session()
    if not session:
        await message.answer("No hay sesion abierta.")
        return

    await db.close_session()
    count = await db.count_session_orders(session["id"])
    total_clients = len(await db.get_approved_clients())
    await message.answer(
        f"Sesion cerrada. Pedidos recibidos: {count}/{total_clients}.",
        reply_markup=admin_main_kb(),
    )


# ==================== Summary ====================

@router.message(F.text == "Resumen")
async def summary(message: Message) -> None:
    if not _is_admin(message):
        return
    session = await db.get_active_session()
    if not session:
        # Show summary for last closed session
        pass

    # Try active session, or find the most recent
    if session:
        session_id = session["id"]
    else:
        # Fallback: get the latest session
        _db = await db.get_db()
        try:
            cur = await _db.execute("SELECT * FROM order_sessions ORDER BY id DESC LIMIT 1")
            row = await cur.fetchone()
            if not row:
                await message.answer("No hay sesiones todavia.")
                return
            session_id = row["id"]
        finally:
            await _db.close()

    summary_data = await db.get_session_summary(session_id)
    count = await db.count_session_orders(session_id)
    total_clients = len(await db.get_approved_clients())

    if not summary_data:
        await message.answer(f"Sesion #{session_id}: sin pedidos todavia. ({count}/{total_clients} clientes)")
        return

    lines = [f"Resumen sesion #{session_id}\n"]
    lines.append(f"Pedidos: {count}/{total_clients} clientes\n")

    grand_total = 0
    for item in summary_data:
        lines.append(f"  {item['name']:.<30} {item['total']}")
        grand_total += item["total"]

    lines.append(f"\nTOTAL unidades: {grand_total}")
    await message.answer("\n".join(lines))


# ==================== Excel export ====================

@router.message(F.text == "Excel")
async def export_excel(message: Message) -> None:
    if not _is_admin(message):
        return

    session = await db.get_active_session()
    if not session:
        _db = await db.get_db()
        try:
            cur = await _db.execute("SELECT * FROM order_sessions ORDER BY id DESC LIMIT 1")
            row = await cur.fetchone()
            if not row:
                await message.answer("No hay sesiones todavia.")
                return
            session = dict(row)
        finally:
            await _db.close()

    orders = await db.get_session_orders(session["id"])
    products = await db.get_active_products()

    if not orders:
        await message.answer("No hay pedidos en esta sesion.")
        return

    file_path = await generate_excel(orders, products, session["id"])
    from aiogram.types import FSInputFile
    await message.answer_document(FSInputFile(str(file_path), filename=file_path.name))


# ==================== Catalog management ====================

@router.message(F.text == "Catalogo")
async def show_catalog(message: Message) -> None:
    if not _is_admin(message):
        return
    products = await db.get_active_products()
    if not products:
        await message.answer("Catalogo vacio.")
    await message.answer("Catalogo actual:", reply_markup=catalog_kb(products))


@router.callback_query(F.data == "catalog:add")
async def catalog_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not config.is_admin(callback.from_user.id):
        return
    await callback.answer()
    await callback.message.answer("Escribe el nombre del nuevo producto:")
    await state.set_state(AddProduct.name)


@router.message(AddProduct.name)
async def catalog_add_finish(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name:
        await message.answer("Nombre no puede estar vacio.")
        return
    await db.add_product(name)
    await state.clear()
    products = await db.get_active_products()
    await message.answer(f"Producto '{name}' anadido.", reply_markup=catalog_kb(products))


@router.callback_query(F.data.startswith("catalog:del:"))
async def catalog_delete(callback: CallbackQuery) -> None:
    if not config.is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split(":")[2])
    await db.delete_product(product_id)
    products = await db.get_active_products()
    await callback.answer("Eliminado")
    await callback.message.edit_reply_markup(reply_markup=catalog_kb(products))


@router.callback_query(F.data.startswith("catalog:up:"))
async def catalog_move_up(callback: CallbackQuery) -> None:
    if not config.is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split(":")[2])
    await db.move_product(product_id, "up")
    products = await db.get_active_products()
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=catalog_kb(products))


@router.callback_query(F.data.startswith("catalog:down:"))
async def catalog_move_down(callback: CallbackQuery) -> None:
    if not config.is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split(":")[2])
    await db.move_product(product_id, "down")
    products = await db.get_active_products()
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=catalog_kb(products))


@router.callback_query(F.data.startswith("catalog:noop:"))
async def catalog_noop(callback: CallbackQuery) -> None:
    await callback.answer()


# ==================== Client management ====================

@router.message(F.text == "Clientes")
async def show_clients(message: Message) -> None:
    if not _is_admin(message):
        return
    clients = await db.get_all_clients()
    if not clients:
        await message.answer("No hay clientes registrados.")
        return
    await message.answer("Clientes:", reply_markup=client_list_kb(clients))


@router.callback_query(F.data.startswith("client:info:"))
async def client_info(callback: CallbackQuery) -> None:
    if not config.is_admin(callback.from_user.id):
        return
    client_id = int(callback.data.split(":")[2])

    _db = await db.get_db()
    try:
        cur = await _db.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        client = dict(await cur.fetchone())
    finally:
        await _db.close()

    status_text = {"approved": "Aprobado", "pending": "Pendiente", "blocked": "Bloqueado"}.get(client["status"], client["status"])
    text = (
        f"Nombre: {client['name']}\n"
        f"Empresa: {client.get('company') or '-'}\n"
        f"Estado: {status_text}\n"
        f"Registrado: {client['created_at'][:16]}"
    )
    await callback.answer()
    await callback.message.answer(text, reply_markup=client_actions_kb(client_id, client["status"]))


@router.callback_query(F.data.startswith("client:approve:"))
async def approve_client(callback: CallbackQuery) -> None:
    if not config.is_admin(callback.from_user.id):
        return
    client_id = int(callback.data.split(":")[2])
    await db.approve_client(client_id)

    _db = await db.get_db()
    try:
        cur = await _db.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        client = dict(await cur.fetchone())
    finally:
        await _db.close()

    await callback.answer("Aprobado!")
    await callback.message.edit_text(f"Cliente {client['name']} aprobado.")

    # Notify client
    try:
        from bot.keyboards import client_main_kb
        await callback.bot.send_message(
            client["telegram_id"],
            "Tu cuenta ha sido aprobada! Ya puedes hacer pedidos.",
            reply_markup=client_main_kb(),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("client:block:"))
async def block_client(callback: CallbackQuery) -> None:
    if not config.is_admin(callback.from_user.id):
        return
    client_id = int(callback.data.split(":")[2])
    await db.block_client(client_id)
    await callback.answer("Bloqueado")
    await callback.message.edit_text("Cliente bloqueado.")


# ==================== Reminder ====================

@router.message(F.text == "Recordar")
async def remind_clients(message: Message) -> None:
    if not _is_admin(message):
        return
    session = await db.get_active_session()
    if not session:
        await message.answer("No hay sesion abierta.")
        return

    clients = await db.get_clients_without_order(session["id"])
    if not clients:
        await message.answer("Todos los clientes ya hicieron su pedido!")
        return

    sent = 0
    for client in clients:
        try:
            await message.bot.send_message(
                client["telegram_id"],
                "Recordatorio: los pedidos estan abiertos. No olvides hacer tu pedido!",
            )
            sent += 1
        except Exception:
            pass

    await message.answer(f"Recordatorio enviado a {sent}/{len(clients)} clientes sin pedido.")
