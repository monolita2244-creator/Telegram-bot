import logging
import asyncio
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

DATA_FILE = "data.txt"
COUNTER_FILE = "counter.txt"
OBJECT_FILE = "object.txt"
WORK_FILE = "work.txt"
PLAN_FILE = "plan.txt"

DEFAULT_OBJECT = "Объект не задан"
DEFAULT_WORK = "Установка анкеров"
DEFAULT_PLAN = 13.61077

WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# --- Файловые функции ---

def load_total():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return float(f.read())
            except:
                return 0.0
    return 0.0

def save_total(value):
    with open(DATA_FILE, "w") as f:
        f.write(str(value))

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
    return DEFAULT_OBJECT

def save_object(name):
    with open(OBJECT_FILE, "w", encoding="utf-8") as f:
        f.write(name)

def load_work():
    if os.path.exists(WORK_FILE):
        with open(WORK_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return DEFAULT_WORK

def save_work(name):
    with open(WORK_FILE, "w", encoding="utf-8") as f:
        f.write(name)

def load_plan():
    if os.path.exists(PLAN_FILE):
        with open(PLAN_FILE, "r") as f:
            try:
                return float(f.read().strip())
            except:
                return DEFAULT_PLAN
    return DEFAULT_PLAN

def save_plan(value):
    with open(PLAN_FILE, "w") as f:
        f.write(str(value))

def get_date_str():
    now = datetime.now()
    weekday = WEEKDAYS_RU[now.weekday()]
    return now.strftime(f"%d.%m.%Y {weekday}")

# --- Клавиатуры ---

def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Создать отчёт", callback_data="menu_report")
    builder.button(text="📊 Статус", callback_data="menu_status")
    builder.button(text="⚙️ Настройки", callback_data="menu_settings")
    builder.button(text="🔄 Сбросить данные", callback_data="menu_reset")
    builder.adjust(2)
    return builder.as_markup()

def settings_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏗 Сменить объект", callback_data="settings_object")
    builder.button(text="🔨 Сменить вид работы", callback_data="settings_work")
    builder.button(text="📐 Изменить план (т)", callback_data="settings_plan")
    builder.button(text="🏠 Главное меню", callback_data="menu_main")
    builder.adjust(1)
    return builder.as_markup()

def lunch_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="0 мин", callback_data="lunch_0")
    builder.button(text="15 мин", callback_data="lunch_15")
    builder.button(text="30 мин", callback_data="lunch_30")
    builder.button(text="60 мин", callback_data="lunch_60")
    builder.button(text="✏️ Другое", callback_data="lunch_custom")
    builder.adjust(4, 1)
    return builder.as_markup()

def secondary_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="➖ Вторичных работ нет", callback_data="secondary_none")
    return builder.as_markup()

def back_to_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="menu_main")
    return builder.as_markup()

def back_to_settings_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад к настройкам", callback_data="menu_settings")
    return builder.as_markup()

def confirm_reset_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, сбросить", callback_data="reset_confirm")
    builder.button(text="❌ Отмена", callback_data="menu_main")
    builder.adjust(2)
    return builder.as_markup()

# --- Состояния ---

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
    waiting_work_name = State()
    waiting_plan_value = State()

# --- /start и главное меню ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    object_name = load_object()
    work_name = load_work()
    plan = load_plan()
    await message.answer(
        f"👋 Привет! Я бот для ежесменных отчётов.\n\n"
        f"🏗 Объект: <b>{object_name}</b>\n"
        f"🔨 Вид работы: <b>{work_name}</b>\n"
        f"📐 План: <b>{plan} т</b>\n\n"
        f"Выберите действие:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "menu_main")
async def cb_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    object_name = load_object()
    work_name = load_work()
    plan = load_plan()
    await callback.message.edit_text(
        f"🏗 Объект: <b>{object_name}</b>\n"
        f"🔨 Вид работы: <b>{work_name}</b>\n"
        f"📐 План: <b>{plan} т</b>\n\n"
        f"Выберите действие:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

# --- Статус ---

@dp.callback_query(F.data == "menu_status")
async def cb_status(callback: types.CallbackQuery):
    vsego_done = load_total()
    plan = load_plan()
    percent_done = (vsego_done / plan) * 100 if plan > 0 else 0
    remains = plan - vsego_done
    percent_remains = 100 - percent_done
    object_name = load_object()
    work_name = load_work()
    report_num = load_counter()

    text = (
        f"📊 <b>Текущий прогресс</b>\n\n"
        f"🏗 {object_name}\n"
        f"🔨 {work_name}\n\n"
        f"✅ Выполнено: <b>{vsego_done:.4f} т ({percent_done:.2f}%)</b>\n"
        f"из {plan} т\n"
        f"⬜️ Осталось: <b>{remains:.4f} т ({percent_remains:.2f}%)</b>\n\n"
        f"📋 Следующий отчёт: № {report_num}"
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(), parse_mode="HTML")
    await callback.answer()

# --- Настройки ---

@dp.callback_query(F.data == "menu_settings")
async def cb_settings(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    object_name = load_object()
    work_name = load_work()
    plan = load_plan()
    await callback.message.edit_text(
        f"⚙️ <b>Настройки</b>\n\n"
        f"🏗 Объект: <b>{object_name}</b>\n"
        f"🔨 Вид работы: <b>{work_name}</b>\n"
        f"📐 План: <b>{plan} т</b>\n\n"
        f"Что хотите изменить?",
        reply_markup=settings_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

# Сменить объект
@dp.callback_query(F.data == "settings_object")
async def cb_settings_object(callback: types.CallbackQuery, state: FSMContext):
    current = load_object()
    await callback.message.edit_text(
        f"🏗 Текущий объект:\n<b>{current}</b>\n\nВведите новое название:",
        parse_mode="HTML",
        reply_markup=back_to_settings_keyboard()
    )
    await state.set_state(SettingsStates.waiting_object_name)
    await callback.answer()

@dp.message(SettingsStates.waiting_object_name)
async def process_object_name(message: types.Message, state: FSMContext):
    save_object(message.text.strip())
    await state.clear()
    await message.answer(
        f"✅ Объект сохранён:\n<b>{message.text.strip()}</b>",
        reply_markup=settings_menu(),
        parse_mode="HTML"
    )

# Сменить вид работы
@dp.callback_query(F.data == "settings_work")
async def cb_settings_work(callback: types.CallbackQuery, state: FSMContext):
    current = load_work()
    await callback.message.edit_text(
        f"🔨 Текущий вид работы:\n<b>{current}</b>\n\nВведите новое название:",
        parse_mode="HTML",
        reply_markup=back_to_settings_keyboard()
    )
    await state.set_state(SettingsStates.waiting_work_name)
    await callback.answer()

@dp.message(SettingsStates.waiting_work_name)
async def process_work_name(message: types.Message, state: FSMContext):
    save_work(message.text.strip())
    await state.clear()
    await message.answer(
        f"✅ Вид работы сохранён:\n<b>{message.text.strip()}</b>",
        reply_markup=settings_menu(),
        parse_mode="HTML"
    )

# Изменить план
@dp.callback_query(F.data == "settings_plan")
async def cb_settings_plan(callback: types.CallbackQuery, state: FSMContext):
    current = load_plan()
    await callback.message.edit_text(
        f"📐 Текущий план: <b>{current} т</b>\n\nВведите новое значение плана (например: 25.5):",
        parse_mode="HTML",
        reply_markup=back_to_settings_keyboard()
    )
    await state.set_state(SettingsStates.waiting_plan_value)
    await callback.answer()

@dp.message(SettingsStates.waiting_plan_value)
async def process_plan_value(message: types.Message, state: FSMContext):
    try:
        new_plan = float(message.text.strip().replace(',', '.'))
    except ValueError:
        return await message.answer("Введите число через точку (например: 25.5):")
    save_plan(new_plan)
    await state.clear()
    await message.answer(
        f"✅ План сохранён: <b>{new_plan} т</b>",
        reply_markup=settings_menu(),
        parse_mode="HTML"
    )

# --- Сброс ---

@dp.callback_query(F.data == "menu_reset")
async def cb_reset_ask(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "⚠️ Вы уверены, что хотите сбросить все данные?\n"
        "(объём выполнения и счётчик отчётов обнулятся,\nнастройки объекта, работы и плана сохранятся)",
        reply_markup=confirm_reset_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "reset_confirm")
async def cb_reset_confirm(callback: types.CallbackQuery):
    save_total(0.0)
    save_counter(1)
    await callback.message.edit_text(
        "🔄 Данные сброшены до нуля.\n\nВыберите действие:",
        reply_markup=main_menu()
    )
    await callback.answer()

# --- Создать отчёт ---

@dp.callback_query(F.data == "menu_report")
async def cb_report_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 <b>Ежесменный отчёт</b>\n\n"
        "🕐 Введите время <b>начала</b> смены (например: 07:00):",
        parse_mode="HTML"
    )
    await state.set_state(ReportStates.waiting_start_time)
    await callback.answer()

@dp.message(ReportStates.waiting_start_time)
async def process_start_time(message: types.Message, state: FSMContext):
    text = message.text.strip().replace('.', ':').replace('-', ':')
    if ':' not in text:
        return await message.answer("Введите время в формате ЧЧ:ММ (например: 07:00):")
    await state.update_data(start_time=text)
    await message.answer("🕐 Введите время <b>завершения</b> смены (например: 15:00):", parse_mode="HTML")
    await state.set_state(ReportStates.waiting_end_time)

@dp.message(ReportStates.waiting_end_time)
async def process_end_time(message: types.Message, state: FSMContext):
    text = message.text.strip().replace('.', ':').replace('-', ':')
    if ':' not in text:
        return await message.answer("Введите время в формате ЧЧ:ММ (например: 15:00):")
    await state.update_data(end_time=text)
    await message.answer(
        "🍖 <b>Длительность обеда:</b>",
        reply_markup=lunch_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(ReportStates.waiting_lunch_custom)

@dp.callback_query(F.data.startswith("lunch_"), ReportStates.waiting_lunch_custom)
async def cb_lunch(callback: types.CallbackQuery, state: FSMContext):
    value = callback.data.replace("lunch_", "")
    if value == "custom":
        await callback.message.edit_text("Введите длительность обеда в минутах:")
        await callback.answer()
        return
    await state.update_data(lunch=value)
    await callback.message.edit_text(
        f"🍖 Обед: <b>{value} мин</b>\n\n👷 Введите количество рабочих на объекте:",
        parse_mode="HTML"
    )
    await state.set_state(ReportStates.waiting_workers)
    await callback.answer()

@dp.message(ReportStates.waiting_lunch_custom)
async def process_lunch_custom(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        return await message.answer("Введите количество минут цифрами (например: 0):")
    await state.update_data(lunch=text)
    await message.answer("👷 Введите количество рабочих на объекте:")
    await state.set_state(ReportStates.waiting_workers)

@dp.message(ReportStates.waiting_workers)
async def process_workers(message: types.Message, state: FSMContext):
    if not message.text.strip().isdigit():
        return await message.answer("Пожалуйста, введите число (количество человек):")
    await state.update_data(workers=message.text.strip())
    work_name = load_work()
    await message.answer(f"⛏ Введите выполнение за смену по работе «{work_name}» (в тоннах, например: 0.225):")
    await state.set_state(ReportStates.waiting_volume)

@dp.message(ReportStates.waiting_volume)
async def process_volume(message: types.Message, state: FSMContext):
    try:
        shift_done = float(message.text.strip().replace(',', '.'))
    except ValueError:
        return await message.answer("Введите число через точку (например: 0.225):")
    await state.update_data(shift_done=shift_done)
    await message.answer(
        "🥈 Введите вторичные (сопутствующие) работы.\n"
        "Каждый пункт с новой строки, например:\n"
        "<i>1. Установка опалубки\n2. Армирование карты</i>",
        reply_markup=secondary_keyboard(),
        parse_mode="HTML"
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
    shift_done = data['shift_done']
    start_time = data['start_time']
    end_time = data['end_time']
    lunch = data['lunch']
    secondary = data.get('secondary', '-')

    plan = load_plan()
    work_name = load_work()

    vsego_done = load_total()
    vsego_done += shift_done
    save_total(vsego_done)

    report_num = load_counter()
    save_counter(report_num + 1)

    object_name = load_object()
    date_str = get_date_str()

    percent_done = (vsego_done / plan) * 100 if plan > 0 else 0
    remains = plan - vsego_done
    percent_remains = 100 - percent_done

    secondary_section = ""
    if secondary.strip() != "-":
        secondary_section = f"\n\n🥈 Вторичные (сопутствующие) работы:\n{secondary}"

    report_text = (
        f"🧾 Ежесменный отчёт № {report_num} по объекту:\n"
        f"{object_name}\n\n"
        f"🕐 Начало смены: {date_str} {start_time}\n"
        f"🕐 Завершение смены: {date_str} {end_time}\n"
        f"🍖 Длительность обеда: {lunch} минут\n\n"
        f"👷 Всего рабочих на объекте: {workers} чел.\n\n"
        f"Выполнение за смену по основным видам работ:\n\n"
        f"🔨 1. ... ({work_name})\n"
        f"☑️ Смена: {shift_done} т\n"
        f"👷‍♂️🔄 Задействовано рабочих: {workers}\n"
        f"✅ Всего выполнено: {vsego_done:.4f} т({percent_done:.2f}%)\n"
        f"из {plan} т\n"
        f"⬜️ Всего осталось: {remains:.4f} т ({percent_remains:.2f}%)"
        f"{secondary_section}"
    )

    await state.clear()
    await message.answer(report_text, reply_markup=back_to_menu_keyboard())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
