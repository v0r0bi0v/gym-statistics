import logging
import pandas as pd
import json
from copy import deepcopy
from pathlib import Path
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
import pytz

timezone = pytz.timezone('Europe/Moscow')

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка токена
try:
    with open("token.txt", "r") as f:
        TOKEN = f.read().strip()
except FileNotFoundError:
    logger.error("Файл token.txt не найден!")
    exit(1)

# Инициализация DataFrame
try:
    df = pd.read_csv("workouts.csv")
except FileNotFoundError:
    df = pd.DataFrame(columns=["user_id", "date", "muscle_group", "exercise", "weight", "reps"])

# Файл для хранения имен пользователей
USER_NAMES_FILE = "user_names.json"

# Загрузка имен пользователей из файла
def load_user_names():
    try:
        if Path(USER_NAMES_FILE).exists():
            with open(USER_NAMES_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке имен пользователей: {e}")
    return {}

# Сохранение имен пользователей в файл
def save_user_names():
    try:
        with open(USER_NAMES_FILE, "w") as f:
            json.dump(user_names, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка при сохранении имен пользователей: {e}")

# Словарь для хранения имен пользователей {user_id: name}
user_names = load_user_names()

# Состояния диалога
GET_NAME, SELECT_MUSCLE, INPUT_CUSTOM_MUSCLE, SELECT_EXERCISE, INPUT_CUSTOM_EXERCISE, INPUT_WEIGHT, INPUT_REPS = range(7)

# Группы мышц и упражнения по умолчанию
DEFAULT_MUSCLE_GROUPS = ["Грудь", "Спина", "Трицепс", "Плечи", "Бицепс", "Ноги", "Икры", "Другое"]
DEFAULT_EXERCISES = {
    "Грудь": ["Жим лежа", "Жим в хаммере", "Брусья"],
    "Спина": ["Тяга вертикального блока", "Тяга вертикального блока за голову", "Становая тяга"],
    "Трицепс": ["Брусья", "Разгибания руки за голову"],
    "Плечи": ["Разведения гантелей", "Подъем гантелей перед собой"],
    "Бицепс": ["Подъем штанги", "Молотки"],
    "Ноги": ["Присед", "Присед в тренажере", "Разгибания", "Сгибания"],
    "Икры": ["Тренажер сидя"],
    "Другое": []
}

def get_user_muscle_groups(user_name):
    """Получает список групп мышц для конкретного пользователя"""
    user_workouts = df[df["user_id"] == user_name]
    if not user_workouts.empty:
        muscle_groups = user_workouts["muscle_group"].unique().tolist()
        # Добавляем группы по умолчанию, если их еще нет
        for group in DEFAULT_MUSCLE_GROUPS:
            if group not in muscle_groups:
                muscle_groups.append(group)
        return muscle_groups
    return DEFAULT_MUSCLE_GROUPS

def get_user_exercises(user_name, muscle_group):
    """Получает список упражнений для конкретного пользователя и группы мышц"""
    user_workouts = df[df["user_id"] == user_name]
    exercises = []
    
    # Добавляем упражнения по умолчанию для этой группы мышц
    if muscle_group in DEFAULT_EXERCISES:
        exercises.extend(DEFAULT_EXERCISES[muscle_group])
    
    # Добавляем упражнения, которые пользователь уже делал для этой группы
    if not user_workouts.empty:
        user_exercises = user_workouts[user_workouts["muscle_group"] == muscle_group]["exercise"].unique().tolist()
        for ex in user_exercises:
            if ex not in exercises:
                exercises.append(ex)
    
    # Всегда добавляем "Другое" в конце
    if "Другое" not in exercises:
        exercises.append("Другое")
    
    return exercises

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало диалога, проверка имени пользователя."""
    user_id = str(update.message.from_user.id)
    
    # Если имя уже есть, пропускаем этап представления
    if user_id in user_names:
        user_name = user_names[user_id]
        muscle_groups = get_user_muscle_groups(user_name)
        reply_keyboard = [muscle_groups[i:i+2] for i in range(0, len(muscle_groups), 2)]
        
        await update.message.reply_text(
            f"Привет, {user_name}! Выберите группу мышц:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return SELECT_MUSCLE
    else:
        await update.message.reply_text(
            "Привет! Как тебя зовут?",
            reply_markup=ReplyKeyboardRemove()
        )
        return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода имени пользователя."""
    user_id = str(update.message.from_user.id)
    name = update.message.text.strip()
    
    # Проверяем, есть ли уже такое имя у другого пользователя
    if name in user_names.values():
        await update.message.reply_text(
            "Это имя уже занято. Пожалуйста, выберите другое имя:",
            reply_markup=ReplyKeyboardRemove()
        )
        return GET_NAME
    
    # Сохраняем имя пользователя
    user_names[user_id] = name
    save_user_names()
    
    muscle_groups = get_user_muscle_groups(name)
    reply_keyboard = [muscle_groups[i:i+2] for i in range(0, len(muscle_groups), 2)]
    
    await update.message.reply_text(
        f"Приятно познакомиться, {name}! Выберите группу мышц:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SELECT_MUSCLE

async def select_muscle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора группы мышц."""
    muscle_group = update.message.text
    context.user_data["muscle_group"] = muscle_group
    
    if muscle_group == "Другое":
        await update.message.reply_text(
            "Введите название группы мышц:",
            reply_markup=ReplyKeyboardRemove()
        )
        return INPUT_CUSTOM_MUSCLE
    
    user_name = user_names[str(update.message.from_user.id)]
    exercises = get_user_exercises(user_name, muscle_group)
    reply_keyboard = [exercises[i:i+2] for i in range(0, len(exercises), 2)]
    
    await update.message.reply_text(
        "Выберите упражнение:\nДля отмены нажмите /cancel",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SELECT_EXERCISE

async def input_custom_muscle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ручного ввода группы мышц для 'Другое'."""
    custom_muscle = update.message.text
    context.user_data["muscle_group"] = custom_muscle
    
    await update.message.reply_text(
        "Введите название упражнения:",
        reply_markup=ReplyKeyboardRemove()
    )
    return INPUT_CUSTOM_EXERCISE

async def select_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора упражнения."""
    exercise = update.message.text
    
    if exercise == "Другое":
        await update.message.reply_text(
            "Введите название упражнения:",
            reply_markup=ReplyKeyboardRemove()
        )
        return INPUT_CUSTOM_EXERCISE
    
    context.user_data["exercise"] = exercise
    await update.message.reply_text(
        "Введите вес (кг):\nДля отмены нажмите /cancel",
        reply_markup=ReplyKeyboardRemove()
    )
    return INPUT_WEIGHT

async def input_custom_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ручного ввода упражнения."""
    exercise = update.message.text
    context.user_data["exercise"] = exercise
    
    await update.message.reply_text(
        "Введите вес (кг):\nДля отмены нажмите /cancel",
        reply_markup=ReplyKeyboardRemove()
    )
    return INPUT_WEIGHT

async def input_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода веса с отображением последнего подхода."""
    try:
        weight = float(update.message.text)
        context.user_data["weight"] = weight
        
        # Получаем информацию о пользователе и текущем упражнении
        user_id = str(update.message.from_user.id)
        user_name = user_names.get(user_id, "друг")
        muscle_group = context.user_data.get("muscle_group", "")
        exercise = context.user_data.get("exercise", "")
        
        # Ищем последний подход в этом упражнении
        user_workouts = df[(df["user_id"] == user_name) & 
                          (df["muscle_group"] == muscle_group) & 
                          (df["exercise"] == exercise)]
        
        if not user_workouts.empty:
            last_workout = user_workouts.iloc[-1]
            message = (
                f"Последний подход в этом упражнении:\n"
                f"Дата: {last_workout['date']}\n"
                f"Вес: {last_workout['weight']} кг\n"
                f"Повторения: {last_workout['reps']}\n\n"
                f"Введите количество повторений для нового подхода:"
            )
        else:
            message = (
                f"Вы впервые делаете это упражнение ({exercise})!\n\n"
                f"Введите количество повторений:"
            )
        
        await update.message.reply_text(message)
        return INPUT_REPS
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число (например: 12.5):")
        return INPUT_WEIGHT

async def input_reps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода повторений и сохранение тренировки."""
    try:
        reps = int(update.message.text)
        user_data = context.user_data
        
        # Добавляем тренировку в DataFrame
        global df
        new_row = {
            "user_id": user_names[str(update.message.from_user.id)],
            "date": pd.Timestamp.now(timezone).strftime("%Y-%m-%d"),
            "muscle_group": user_data["muscle_group"],
            "exercise": user_data["exercise"],
            "weight": user_data["weight"],
            "reps": reps
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv("workouts.csv", index=False)
        
        await update.message.reply_text(
            f"Тренировка сохранена, {user_names.get(str(update.message.from_user.id), 'друг')}! "
            "Нажмите /start для новой записи."
            "\nНажмите /delete_last для удаления последнего подхода"
            "\nГрафики с прогрессом вы можете посмотреть на http://193.108.54.176:8080/"
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите целое число (например: 10):")
        return INPUT_REPS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена текущей операции."""
    user_name = user_names.get(str(update.message.from_user.id), "друг")
    await update.message.reply_text(
        f"Действие отменено, {user_name}.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def delete_last(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаляет последнюю запись пользователя."""
    global df
    
    user_id = str(update.message.from_user.id)
    
    if user_id not in user_names:
        await update.message.reply_text("Вы еще не сохраняли тренировки!")
        return
    
    user_name = user_names[user_id]
    user_entries = df[df["user_id"] == user_name]
    
    if user_entries.empty:
        await update.message.reply_text("У вас нет сохраненных тренировок!")
        return
    
    # Находим последнюю запись
    last_entry_index = user_entries.index[-1]
    
    # Удаляем запись
    df = df.drop(last_entry_index)
    df.to_csv("workouts.csv", index=False)
    
    await update.message.reply_text("Последняя тренировка удалена!")

def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)
            ],
            SELECT_MUSCLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_muscle)
            ],
            INPUT_CUSTOM_MUSCLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, input_custom_muscle)
            ],
            SELECT_EXERCISE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_exercise)
            ],
            INPUT_CUSTOM_EXERCISE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, input_custom_exercise)
            ],
            INPUT_WEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, input_weight)
            ],
            INPUT_REPS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, input_reps)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("delete_last", delete_last))
    
    application.run_polling()

if __name__ == "__main__":
    main()