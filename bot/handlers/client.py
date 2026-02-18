from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot import db
from bot.config import config
from bot.keyboards import client_main_kb, confirm_order_kb, skip_product_kb, approve_client_kb

router = Router()


# ==================== FSM States ====================

class Registration(StatesGroup):
    name = State()
    company = State()


class OrderFlow(StatesGroup):
    entering_quantity = State()


# ==================== /start — Registration ====================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    if config.is_admin(message.from_user.id):
        # Admin is handled via admin router, but still greet
        from bot.keyboards import admin_main_kb
        await message.answer(
            "Hola, administrador! Usa el menu para gestionar.",
            reply_markup=admin_main_kb(),
        )
        return

    client = await db.get_client_by_tg(message.from_user.id)
    if client:
        if client["status"] == "approved":
            await message.answer(
                f"Hola, {client['name']}! Ya estas registrado.",
                reply_markup=client_main_kb(),
            )
        elif client["status"] == "pending":
            await message.answer("Tu solicitud esta en revision. El administrador te confirmara pronto.")
        else:
            await message.answer("Tu cuenta esta bloqueada. Contacta al administrador.")
        return

    await message.answer("Bienvenido! Como te llamas? (Nombre y apellido)")
    await state.set_state(Registration.name)


@router.message(Registration.name)
async def registration_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await message.answer("Nombre de tu empresa/punto de venta (o escribe '-' si no aplica):")
    await state.set_state(Registration.company)


@router.message(Registration.company)
async def registration_company(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    company = message.text.strip()
    if company == "-":
        company = None

    client_id = await db.add_client(
        telegram_id=message.from_user.id,
        name=data["name"],
        company=company,
    )
    await state.clear()
    await message.answer(
        "Gracias! Tu solicitud ha sido enviada al administrador. "
        "Te avisaremos cuando sea aprobada."
    )

    # Notify admins
    client = await db.get_client_by_tg(message.from_user.id)
    for admin_id in config.admin_ids:
        try:
            text = (
                f"Nuevo cliente solicita acceso:\n"
                f"Nombre: {data['name']}\n"
                f"Empresa: {company or '-'}\n"
            )
            await message.bot.send_message(
                admin_id,
                text,
                reply_markup=approve_client_kb(client["id"]),
            )
        except Exception:
            pass


# ==================== New Order ====================

@router.message(F.text == "Nuevo pedido")
async def new_order(message: Message, state: FSMContext) -> None:
    client = await db.get_client_by_tg(message.from_user.id)
    if not client or client["status"] != "approved":
        await message.answer("No tienes acceso. Espera la aprobacion del administrador.")
        return

    session = await db.get_active_session()
    if not session:
        await message.answer("El pedido esta cerrado ahora. Te avisaremos cuando se abra.")
        return

    products = await db.get_active_products()
    if not products:
        await message.answer("No hay productos en el catalogo todavia.")
        return

    await state.update_data(
        session_id=session["id"],
        client_id=client["id"],
        products=products,
        current_idx=0,
        order_items=[],
    )
    await state.set_state(OrderFlow.entering_quantity)
    await _ask_product_quantity(message, state)


async def _ask_product_quantity(message_or_callback, state: FSMContext) -> None:
    data = await state.get_data()
    idx = data["current_idx"]
    products = data["products"]

    if idx >= len(products):
        await _show_order_summary(message_or_callback, state)
        return

    product = products[idx]
    text = f"({idx + 1}/{len(products)}) {product['name']}\nIntroduce la cantidad (0 = saltar):"

    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(text, reply_markup=skip_product_kb())
    else:
        await message_or_callback.answer(text, reply_markup=skip_product_kb())


@router.callback_query(F.data == "order:skip", OrderFlow.entering_quantity)
async def skip_product(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    items = data["order_items"]
    items.append(0)
    await state.update_data(order_items=items, current_idx=data["current_idx"] + 1)
    await callback.answer()
    await _ask_product_quantity(callback, state)


@router.message(OrderFlow.entering_quantity)
async def enter_quantity(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("Por favor, introduce un numero (0 o mas):")
        return

    quantity = int(text)
    data = await state.get_data()
    items = data["order_items"]
    items.append(quantity)
    await state.update_data(order_items=items, current_idx=data["current_idx"] + 1)
    await _ask_product_quantity(message, state)


async def _show_order_summary(message_or_callback, state: FSMContext) -> None:
    data = await state.get_data()
    products = data["products"]
    items = data["order_items"]

    lines = ["Tu pedido:\n"]
    total_units = 0
    total_positions = 0
    for product, qty in zip(products, items):
        if qty > 0:
            lines.append(f"  {product['name']} — {qty}")
            total_units += qty
            total_positions += 1

    if total_units == 0:
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.answer("No has seleccionado nada. Pedido cancelado.")
        else:
            await message_or_callback.answer("No has seleccionado nada. Pedido cancelado.")
        await state.clear()
        return

    lines.append(f"\nTotal: {total_positions} productos, {total_units} unidades")

    text = "\n".join(lines)
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(text, reply_markup=confirm_order_kb())
    else:
        await message_or_callback.answer(text, reply_markup=confirm_order_kb())


@router.callback_query(F.data == "order:confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    products = data["products"]
    items = data["order_items"]

    order_items = [
        (products[i]["id"], items[i])
        for i in range(len(products))
        if items[i] > 0
    ]

    order_id = await db.create_order(
        client_id=data["client_id"],
        session_id=data["session_id"],
        items=order_items,
    )
    await state.clear()
    await callback.answer("Pedido confirmado!")
    await callback.message.edit_text(
        callback.message.text + "\n\nPedido confirmado!"
    )

    # Notify admins
    client = await db.get_client_by_tg(callback.from_user.id)
    for admin_id in config.admin_ids:
        try:
            lines = [f"Nuevo pedido de {client['name']}:"]
            for p, qty in zip(products, items):
                if qty > 0:
                    lines.append(f"  {p['name']} — {qty}")
            await callback.bot.send_message(admin_id, "\n".join(lines))
        except Exception:
            pass


@router.callback_query(F.data == "order:edit")
async def edit_order(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.update_data(current_idx=0, order_items=[])
    await callback.answer()
    await state.set_state(OrderFlow.entering_quantity)
    await _ask_product_quantity(callback, state)


@router.callback_query(F.data == "order:cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Pedido cancelado.")
    await callback.message.edit_text("Pedido cancelado.")


# ==================== My Orders ====================

@router.message(F.text == "Mis pedidos")
async def my_orders(message: Message) -> None:
    client = await db.get_client_by_tg(message.from_user.id)
    if not client or client["status"] != "approved":
        await message.answer("No tienes acceso.")
        return

    orders = await db.get_client_orders(client["id"], limit=5)
    if not orders:
        await message.answer("No tienes pedidos todavia.")
        return

    for order in orders:
        lines = [f"Pedido del {order['created_at'][:16]}:"]
        total = 0
        for item in order["items"]:
            lines.append(f"  {item['name']} — {item['quantity']}")
            total += item["quantity"]
        lines.append(f"Total: {total} unidades")
        await message.answer("\n".join(lines))
