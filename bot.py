import logging
import asyncio
import os
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

DATA_FILE = "works.json"
COUNTER_FILE = "counter.txt"
OBJECT_FILE = "object.txt"

DEFAULT_WORKS = [
    {"name": "Установка анкеров", "plan": 13.61077, "done": 0.0}
]

WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# --- Файловые функции ---

def load_works():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                pass
    return [w.copy() for w in DEFAULT_WORKS]

def save_works(works):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(works, f, ensure_ascii=False, indent=2)

def load_counter():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except:
                return 1
    return 1

def save_counter(value):
    with open(COUNTER_FILE, "w") as f:
        f.write(str(value))

def load_object():
    if os.path.exists(OBJECT_FILE):
        with open(OBJECT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "Объект не задан"

def save_object(name):
    with open(OBJECT_FILE, "w", encoding="utf-8") as f:
        f.write(name)

def get_date_str():
    now = datetime.now()
    weekday = WEEKDAYS_RU[now.weekday()]
    return now.strftime(f"%d.%m.%Y {weekday}")

# --- Клавиатуры ---

def main_menu():
    b = InlineKeyboardBuilder()
    b.button(text="📋 Создать отчёт", callback_data="menu_report")
    b.button(text="📊 Статус", callback_data="menu_status")
    b.button(text="⚙️ Настройки", callback_data="menu_settings")
    b.button(text="🔄 Сбросить данные", callback_data="menu_reset")
    b.adjust(2)
    return b.as_markup()

def settings_menu():
    b = InlineKeyboardBuilder()
    b.button(text="🏗 Сменить объект", callback_data="s_object")
    b.button(text="⚒️ Управление работами", callback_data="s_works")
    b.button(text="🏠 Главное меню", callback_data="menu_main")
    b.adjust(1)
    return b.as_markup()

def works_list_menu():
    works = load_works()
    b = InlineKeyboardBuilder()
    for i, w in enumerate(works):
        b.button(text=f"✏️ {w['name']}", callback_data=f"w_edit_{i}")
        b.button(text="🗑", callback_data=f"w_del_{i}")
    if len(works) < 6:
        b.button(text="➕ Добавить вид работы", callback_data="w_add")
    b.button(text="◀️ Назад", callback_data="menu_settings")
    b.adjust(*([2] * len(works)), 1, 1)
    return b.as_markup()

def cancel_keyboard():
    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data="cancel_report")
    return b.as_markup()

def back_menu():
    b = InlineKeyboardBuilder()
    b.button(text="🏠 Главное меню", callback_data="menu_main")
    return b.as_markup()

def back_settings():
    b = InlineKeyboardBuilder()
    b.button(text="◀️ Назад к настройкам", callback_data="menu_settings")
    return b.as_markup()

def back_works():
    b = InlineKeyboardBuilder()
    b.button(text="◀️ Назад", callback_data="s_works")
    return b.as_markup()

def confirm_reset_keyboard():
    b = InlineKeyboardBuilder()
    b.button(text="✅ Да, сбросить", callback_data="reset_confirm")
    b.button(text="❌ Отмена", callback_data="menu_main")
    b.adjust(2)
    return b.as_markup()

def confirm_delete_keyboard(idx):
    b = InlineKeyboardBuilder()
    b.button(text="✅ Удалить", callback_data=f"w_del_confirm_{idx}")
    b.button(text="❌ Отмена", callback_data="s_works")
    b.adjust(2)
    return b.as_markup()

def secondary_keyboard():
    b = InlineKeyboardBuilder()
    b.button(text="➖ Вторичных работ нет", callback_data="secondary_none")
    b.button(text="❌ Отмена", callback_data="cancel_report")
    b.adjust(1)
    return b.as_markup()

def lunch_keyboard():
    b = InlineKeyboardBuilder()
    b.button(text="0 мин", callback_data="lunch_0")
    b.button(text="15 мин", callback_data="lunch_15")
    b.button(text="30 мин", callback_data="lunch_30")
    b.button(text="60 мин", callback_data="lunch_60")
    b.button(text="✏️ Другое", callback_data="lunch_custom")
    b.button(text="❌ Отмена", callback_data="cancel_report")
    b.adjust(4, 1, 1)
    return b.as_markup()

# --- Бот и диспетчер ---

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class ReportStates(StatesGroup):
    waiting_start_time = State()
    waiting_end_time = State()
    waiting_lunch_custom = State()
    waiting_workers = State()
    waiting_volume = State()
    waiting_secondary = State()

class SettingsStates(StatesGroup):
    waiting_object_name = State()
    waiting_new_work_name = State()
    waiting_new_work_plan = State()
    waiting_edit_work_name = State()
    waiting_edit_work_plan = State()

# --- /start ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    works = load_works()
    obj = load_object()
    works_str = "\n".join(f"  🔨 {w['name']} — план: {w['plan']} т" for w in works)
    await message.answer(
        f"👋 Привет! Я бот для ежесменных отчётов.\n\n"
        f"🏗 Объект: <b>{obj}</b>\n\n"
        f"Виды работ:\n{works_str}\n\n"
        f"Выберите действие:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "menu_main")
async def cb_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    works = load_works()
    obj = load_object()
    works_str = "\n".join(f"  🔨 {w['name']} — план: {w['plan']} т" for w in works)
    await callback.message.edit_text(
        f"🏗 Объект: <b>{obj}</b>\n\n"
        f"Виды работ:\n{works_str}\n\n"
        f"Выберите действие:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "cancel_report")
async def cb_cancel_report(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Отчёт отменён.\n\nВыберите действие:",
        reply_markup=main_menu()
    )
    await callback.answer()

# --- Статус ---

@dp.callback_query(F.data == "menu_status")
async def cb_status(callback: types.CallbackQuery):
    works = load_works()
    obj = load_object()
    report_num = load_counter()
    lines = [f"📊 <b>Текущий прогресс</b>\n\n🏗 {obj}\n"]
    for w in works:
        plan = w['plan']
        done = w['done']
        pct = (done / plan * 100) if plan > 0 else 0
        remains = plan - done
        lines.append(
            f"🔨 <b>{w['name']}</b>\n"
            f"  ✅ Выполнено: {done:.4f} т ({pct:.2f}%)\n"
            f"  ⬜️ Осталось: {remains:.4f} т из {plan} т\n"
        )
    lines.append(f"📋 Следующий отчёт: № {report_num}")
    await callback.message.edit_text("\n".join(lines), reply_markup=back_menu(), parse_mode="HTML")
    await callback.answer()

# --- Сброс ---

@dp.callback_query(F.data == "menu_reset")
async def cb_reset_ask(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "⚠️ Вы уверены, что хотите сбросить все данные?\n"
        "(объём выполнения и счётчик отчётов обнулятся,\nнастройки сохранятся)",
        reply_markup=confirm_reset_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "reset_confirm")
async def cb_reset_confirm(callback: types.CallbackQuery):
    works = load_works()
    for w in works:
        w['done'] = 0.0
    save_works(works)
    save_counter(1)
    await callback.message.edit_text(
        "🔄 Данные сброшены до нуля.\n\nВыберите действие:",
        reply_markup=main_menu()
    )
    await callback.answer()

# --- Настройки ---

@dp.callback_query(F.data == "menu_settings")
async def cb_settings(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    obj = load_object()
    works = load_works()
    works_str = "\n".join(f"  🔨 {w['name']} — {w['plan']} т" for w in works)
    await callback.message.edit_text(
        f"⚙️ <b>Настройки</b>\n\n"
        f"🏗 Объект: <b>{obj}</b>\n\n"
        f"Виды работ:\n{works_str}\n\n"
        f"Что изменить?",
        reply_markup=settings_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

# Сменить объект
@dp.callback_query(F.data == "s_object")
async def cb_s_object(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        f"🏗 Текущий объект: <b>{load_object()}</b>\n\nВведите новое название:",
        parse_mode="HTML", reply_markup=back_settings()
    )
    await state.set_state(SettingsStates.waiting_object_name)
    await callback.answer()

@dp.message(SettingsStates.waiting_object_name)
async def process_object_name(message: types.Message, state: FSMContext):
    save_object(message.text.strip())
    await state.clear()
    await message.answer(f"✅ Объект сохранён: <b>{message.text.strip()}</b>",
                         reply_markup=settings_menu(), parse_mode="HTML")

# --- Управление видами работ ---

@dp.callback_query(F.data == "s_works")
async def cb_s_works(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    works = load_works()
    if not works:
        text = "⚒️ <b>Виды работ</b>\n\nСписок пуст. Добавьте хотя бы один вид работы."
    else:
        lines = [f"⚒️ <b>Виды работ</b>\n"]
        for i, w in enumerate(works):
            lines.append(f"{i+1}. {w['name']} — план: {w['plan']} т, выполнено: {w['done']:.4f} т")
        text = "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=works_list_menu(), parse_mode="HTML")
    await callback.answer()

# Добавить работу
@dp.callback_query(F.data == "w_add")
async def cb_w_add(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "➕ <b>Новый вид работы</b>\n\nВведите название:",
        parse_mode="HTML", reply_markup=back_works()
    )
    await state.set_state(SettingsStates.waiting_new_work_name)
    await callback.answer()

@dp.message(SettingsStates.waiting_new_work_name)
async def process_new_work_name(message: types.Message, state: FSMContext):
    await state.update_data(new_work_name=message.text.strip())
    await message.answer(f"Введите план для «{message.text.strip()}» (в тоннах, например: 20.5):")
    await state.set_state(SettingsStates.waiting_new_work_plan)

@dp.message(SettingsStates.waiting_new_work_plan)
async def process_new_work_plan(message: types.Message, state: FSMContext):
    try:
        plan = float(message.text.strip().replace(',', '.'))
    except ValueError:
        return await message.answer("Введите число (например: 20.5):")
    data = await state.get_data()
    name = data['new_work_name']
    works = load_works()
    works.append({"name": name, "plan": plan, "done": 0.0})
    save_works(works)
    await state.clear()
    await message.answer(
        f"✅ Добавлено: <b>{name}</b> — план {plan} т",
        reply_markup=works_list_menu(), parse_mode="HTML"
    )

# Редактировать работу
@dp.callback_query(F.data.startswith("w_edit_"))
async def cb_w_edit(callback: types.CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[-1])
    works = load_works()
    if idx >= len(works):
        await callback.answer("Ошибка")
        return
    w = works[idx]
    await state.update_data(edit_work_idx=idx)
    await callback.message.edit_text(
        f"✏️ <b>Редактирование работы</b>\n\n"
        f"Текущее название: <b>{w['name']}</b>\n"
        f"Текущий план: <b>{w['plan']} т</b>\n"
        f"Выполнено: <b>{w['done']:.4f} т</b>\n\n"
        f"Введите новое название (или отправьте «-» чтобы не менять):",
        parse_mode="HTML", reply_markup=back_works()
    )
    await state.set_state(SettingsStates.waiting_edit_work_name)
    await callback.answer()

@dp.message(SettingsStates.waiting_edit_work_name)
async def process_edit_work_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    idx = data['edit_work_idx']
    works = load_works()
    if message.text.strip() != "-":
        works[idx]['name'] = message.text.strip()
        save_works(works)
    await state.update_data(edit_work_idx=idx)
    await message.answer(
        f"Введите новый план в тоннах (или «-» чтобы не менять, текущий: {works[idx]['plan']} т):"
    )
    await state.set_state(SettingsStates.waiting_edit_work_plan)

@dp.message(SettingsStates.waiting_edit_work_plan)
async def process_edit_work_plan(message: types.Message, state: FSMContext):
    data = await state.get_data()
    idx = data['edit_work_idx']
    works = load_works()
    if message.text.strip() != "-":
        try:
            works[idx]['plan'] = float(message.text.strip().replace(',', '.'))
            save_works(works)
        except ValueError:
            return await message.answer("Введите число (например: 20.5) или «-»:")
    await state.clear()
    w = works[idx]
    await message.answer(
        f"✅ Сохранено: <b>{w['name']}</b> — план {w['plan']} т",
        reply_markup=works_list_menu(), parse_mode="HTML"
    )

# Удалить работу
@dp.callback_query(F.data.startswith("w_del_") & ~F.data.startswith("w_del_confirm_"))
async def cb_w_del(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[-1])
    works = load_works()
    if idx >= len(works):
        await callback.answer("Ошибка")
        return
    if len(works) == 1:
        await callback.answer("Нельзя удалить последний вид работы!", show_alert=True)
        return
    w = works[idx]
    await callback.message.edit_text(
        f"🗑 Удалить «<b>{w['name']}</b>»?",
        reply_markup=confirm_delete_keyboard(idx), parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("w_del_confirm_"))
async def cb_w_del_confirm(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[-1])
    works = load_works()
    if idx >= len(works):
        await callback.answer("Ошибка")
        return
    name = works[idx]['name']
    works.pop(idx)
    save_works(works)
    await callback.message.edit_text(
        f"✅ «{name}» удалён.",
        reply_markup=works_list_menu()
    )
    await callback.answer()

# --- Создать отчёт ---

@dp.callback_query(F.data == "menu_report")
async def cb_report_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 <b>Ежесменный отчёт</b>\n\n"
        "🕐 Введите время <b>начала</b> смены (например: 07:00):",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )
    await state.set_state(ReportStates.waiting_start_time)
    await callback.answer()

@dp.message(ReportStates.waiting_start_time)
async def process_start_time(message: types.Message, state: FSMContext):
    text = message.text.strip().replace('.', ':').replace('-', ':')
    if ':' not in text:
        return await message.answer("Введите время в формате ЧЧ:ММ (например: 07:00):", reply_markup=cancel_keyboard())
    await state.update_data(start_time=text)
    await message.answer("🕐 Введите время <b>завершения</b> смены (например: 15:00):",
                         parse_mode="HTML", reply_markup=cancel_keyboard())
    await state.set_state(ReportStates.waiting_end_time)

@dp.message(ReportStates.waiting_end_time)
async def process_end_time(message: types.Message, state: FSMContext):
    text = message.text.strip().replace('.', ':').replace('-', ':')
    if ':' not in text:
        return await message.answer("Введите время в формате ЧЧ:ММ (например: 15:00):", reply_markup=cancel_keyboard())
    await state.update_data(end_time=text)
    await message.answer("🍖 <b>Длительность обеда:</b>", reply_markup=lunch_keyboard(), parse_mode="HTML")
    await state.set_state(ReportStates.waiting_lunch_custom)

@dp.callback_query(F.data.startswith("lunch_"), ReportStates.waiting_lunch_custom)
async def cb_lunch(callback: types.CallbackQuery, state: FSMContext):
    value = callback.data.replace("lunch_", "")
    if value == "custom":
        await callback.message.edit_text("Введите длительность обеда в минутах:", reply_markup=cancel_keyboard())
        await callback.answer()
        return
    await state.update_data(lunch=value)
    await callback.message.edit_text(
        f"🍖 Обед: <b>{value} мин</b>\n\n👷 Введите количество рабочих на объекте:",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )
    await state.set_state(ReportStates.waiting_workers)
    await callback.answer()

@dp.message(ReportStates.waiting_lunch_custom)
async def process_lunch_custom(message: types.Message, state: FSMContext):
    if not message.text.strip().isdigit():
        return await message.answer("Введите количество минут цифрами:", reply_markup=cancel_keyboard())
    await state.update_data(lunch=message.text.strip())
    await message.answer("👷 Введите количество рабочих на объекте:", reply_markup=cancel_keyboard())
    await state.set_state(ReportStates.waiting_workers)

@dp.message(ReportStates.waiting_workers)
async def process_workers(message: types.Message, state: FSMContext):
    if not message.text.strip().isdigit():
        return await message.answer("Введите число:", reply_markup=cancel_keyboard())
    await state.update_data(workers=message.text.strip(), volumes=[], current_work_idx=0)
    works = load_works()
    w = works[0]
    await message.answer(
        f"⛏ Введите выполнение за смену по работе:\n<b>{w['name']}</b> (план: {w['plan']} т)\n\nВведите значение в тоннах:",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )
    await state.set_state(ReportStates.waiting_volume)

@dp.message(ReportStates.waiting_volume)
async def process_volume(message: types.Message, state: FSMContext):
    try:
        shift_done = float(message.text.strip().replace(',', '.'))
    except ValueError:
        return await message.answer("Введите число (например: 0.225):", reply_markup=cancel_keyboard())

    data = await state.get_data()
    volumes = data.get('volumes', [])
    current_idx = data.get('current_work_idx', 0)
    volumes.append(shift_done)
    current_idx += 1
    await state.update_data(volumes=volumes, current_work_idx=current_idx)

    works = load_works()
    if current_idx < len(works):
        w = works[current_idx]
        await message.answer(
            f"⛏ Введите выполнение по работе:\n<b>{w['name']}</b> (план: {w['plan']} т)\n\nВведите значение в тоннах:",
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )
    else:
        await message.answer(
            "🥈 Введите вторичные (сопутствующие) работы.\n"
            "Каждый пункт с новой строки, например:\n"
            "<i>1. Установка опалубки\n2. Армирование карты</i>",
            reply_markup=secondary_keyboard(), parse_mode="HTML"
        )
        await state.set_state(ReportStates.waiting_secondary)

@dp.callback_query(F.data == "secondary_none", ReportStates.waiting_secondary)
async def cb_secondary_none(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(secondary="-")
    await callback.message.edit_text("Формирую отчёт...")
    await finish_report(callback.message, state)
    await callback.answer()

@dp.message(ReportStates.waiting_secondary)
async def process_secondary(message: types.Message, state: FSMContext):
    await state.update_data(secondary=message.text.strip())
    await finish_report(message, state)

async def finish_report(message: types.Message, state: FSMContext):
    data = await state.get_data()
    workers = data['workers']
    start_time = data['start_time']
    end_time = data['end_time']
    lunch = data['lunch']
    secondary = data.get('secondary', '-')
    volumes = data.get('volumes', [])

    works = load_works()
    date_str = get_date_str()
    obj = load_object()
    report_num = load_counter()
    save_counter(report_num + 1)

    # Обновляем накопленные данные
    for i, w in enumerate(works):
        if i < len(volumes):
            w['done'] = round(w['done'] + volumes[i], 6)
    save_works(works)

    # Формируем отчёт
    lines = [
        f"🧾 Ежесменный отчёт № {report_num} по объекту:",
        f"{obj}",
        f"",
        f"🕐 Начало смены: {date_str} {start_time}",
        f"🕐 Завершение смены: {date_str} {end_time}",
        f"🍖 Длительность обеда: {lunch} минут",
        f"",
        f"👷 Всего рабочих на объекте: {workers} чел.",
        f"",
        f"Выполнение за смену по основным видам работ:",
        f"",
    ]

    for i, w in enumerate(works):
        vol = volumes[i] if i < len(volumes) else 0.0
        plan = w['plan']
        done = w['done']
        pct_done = (done / plan * 100) if plan > 0 else 0
        remains = plan - done
        pct_rem = 100 - pct_done
        lines += [
            f"🔨 {i+1}. {w['name']}",
            f"☑️ Смена: {vol} т",
            f"👷‍♂️🔄 Задействовано рабочих: {workers}",
            f"✅ Всего выполнено: {done:.4f} т({pct_done:.2f}%)",
            f"из {plan} т",
            f"⬜️ Всего осталось: {remains:.4f} т ({pct_rem:.2f}%)",
            f"",
        ]

    if secondary.strip() != "-":
        lines += [f"🥈 Вторичные (сопутствующие) работы:", secondary]

    await state.clear()
    await message.answer("\n".join(lines), reply_markup=back_menu())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
