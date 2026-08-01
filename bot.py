import json
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
import requests
from datetime import datetime, timedelta
import threading
import time

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
USERS_FILE = "users.json"

CITY_TRANSLATION = {
    "москва": "Moscow",
    "санкт-петербург": "Saint Petersburg",
    "спб": "Saint Petersburg",
    "новосибирск": "Novosibirsk",
    "екатеринбург": "Yekaterinburg",
    "нижний новгород": "Nizhny Novgorod",
    "казань": "Kazan",
    "челябинск": "Chelyabinsk",
    "омск": "Omsk",
    "самара": "Samara",
    "ростов-на-дону": "Rostov-on-Don",
    "уфа": "Ufa",
    "краснодар": "Krasnodar",
    "пермь": "Perm",
    "воронеж": "Voronezh",
    "волгоград": "Volgograd",
    "саратов": "Saratov",
    "тюмень": "Tyumen",
    "иркутск": "Irkutsk",
    "владивосток": "Vladivostok",
    "новокузнецк": "Novokuznetsk",
    "кемерово": "Kemerovo",
    "тольятти": "Togliatti",
    "краснояск": "Krasnoyarsk",
    "сочи": "Sochi",
    "тверь": "Tver",
    "липецк": "Lipetsk",
    "ярославль": "Yaroslavl",
    "архангельск": "Arkhangelsk",
    "псков": "Pskov",
    "смоленск": "Smolensk",
    "брянск": "Bryansk",
    "тула": "Tula",
    "рязань": "Ryazan",
    "тамбов": "Tambov",
    "хабаровск": "Khabarovsk",
    "магадан": "Magadan",
    "якутск": "Yakutsk",
    "оренбург": "Orenburg",
    "мурманск": "Murmansk",
    "калининград": "Kaliningrad",
    "стерлитамак": "Sterlitamak",
    "сургут": "Surgut",
    "орёл": "Oryol",
    "курск": "Kursk",
    "белгород": "Belgorod",
    "курган": "Kurgan",
    "барнаул": "Barnaul",
    "томск": "Tomsk",
    "ставрополь": "Stavropol",
    "волжский": "Volzhsky",
    "махачкала": "Makhachkala",
    "симферополь": "Simferopol",
    "севастополь": "Sevastopol",
}

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def translate_city(city):
    city_lower = city.lower().strip()
    return CITY_TRANSLATION.get(city_lower, city)

def get_local_time():
    utc_time = datetime.utcnow()
    moscow_time = utc_time + timedelta(hours=3)
    return moscow_time.strftime('%H:%M:%S')

def get_local_hour_minute():
    utc_time = datetime.utcnow()
    moscow_time = utc_time + timedelta(hours=3)
    return moscow_time.strftime('%H:%M')

users = load_users()
application_global = None
last_send_time = None

def get_menu_keyboard():
    keyboard = [
        ['🌤 Погода сейчас', '⚙️ Установить город'],
        ['❓ Справка']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_weather(city):
    try:
        city_en = translate_city(city)
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city_en}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code != 200:
            return None
        
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        weather_desc = data['weather'][0]['description'].capitalize()
        clouds = data['clouds']['all']
        lat = data['coord']['lat']
        lon = data['coord']['lon']
        
        uvi_url = f"https://api.openweathermap.org/data/2.5/uvi?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}"
        uvi_response = requests.get(uvi_url)
        uvi_data = uvi_response.json()
        uvi = uvi_data.get('value', 'N/A')
        
        message = f"""🌍 <b>Погода в городе {city_en.title()}</b>

🌡 <b>Температура:</b> {temp}°C (ощущается как {feels_like}°C)
☁️ <b>Условия:</b> {weather_desc}
💧 <b>Влажность:</b> {humidity}%
💨 <b>Ветер:</b> {wind_speed} м/с
☁️ <b>Облачность:</b> {clouds}%
☀️ <b>УФ индекс:</b> {uvi}

⏰ Обновлено: {get_local_time()}"""
        return message
    except Exception as e:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = """👋 Привет! Я бот прогноза погоды.

Просто напишите название города (Москва, Казань и т.д.) или используйте кнопки ниже.

В 8:00 каждый день вы будете получать прогноз для вашего города."""
    await update.message.reply_text(message, reply_markup=get_menu_keyboard())

async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text("❌ Укажите город. Пример: Москва или Moscow", reply_markup=get_menu_keyboard())
        return
    
    city = " ".join(context.args)
    weather_msg = get_weather(city)
    
    if not weather_msg:
        await update.message.reply_text(f"❌ Город '{city}' не найден.", reply_markup=get_menu_keyboard())
        return
    
    users[user_id] = city
    save_users(users)
    
    await update.message.reply_text(f"✅ Город установлен: <b>{city.title()}</b>", parse_mode='HTML', reply_markup=get_menu_keyboard())

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in users:
        await update.message.reply_text("❌ Сначала установите город (напишите название)", reply_markup=get_menu_keyboard())
        return
    
    city = users[user_id]
    await update.message.chat.send_action(ChatAction.TYPING)
    weather_msg = get_weather(city)
    if weather_msg:
        await update.message.reply_text(weather_msg, parse_mode='HTML', reply_markup=get_menu_keyboard())
    else:
        await update.message.reply_text("❌ Ошибка при получении погоды", reply_markup=get_menu_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""📖 <b>Справка</b>

Напишите название города (Москва, Казань и т.д.)
🌤 Погода сейчас — получить погоду
⚙️ Установить город — установить новый город
❓ Справка — эта справка""", parse_mode='HTML', reply_markup=get_menu_keyboard())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    
    if text == "🌤 Погода сейчас":
        await weather(update, context)
        return
    elif text == "⚙️ Установить город":
        await update.message.reply_text("Напишите название города:", reply_markup=get_menu_keyboard())
        return
    elif text == "❓ Справка":
        await help_command(update, context)
        return
    
    if text.startswith('/'):
        return
    
    weather_msg = get_weather(text)
    
    if not weather_msg:
        await update.message.reply_text(f"❌ Город '{text}' не найден.", reply_markup=get_menu_keyboard())
        return
    
    users[user_id] = text
    save_users(users)
    
    city_en = translate_city(text)
    await update.message.reply_text(f"✅ Город установлен: <b>{city_en.title()}</b>", parse_mode='HTML', reply_markup=get_menu_keyboard())
    await update.message.reply_text(weather_msg, parse_mode='HTML', reply_markup=get_menu_keyboard())

def send_weather_to_all():
    global last_send_time
    print(f"📤 Рассылка погоды... ({get_local_time()})")
    last_send_time = get_local_hour_minute()
    
    if not application_global:
        return
    
    for user_id, city in users.items():
        try:
            weather_msg = get_weather(city)
            if weather_msg:
                import asyncio
                asyncio.run(application_global.bot.send_message(
                    chat_id=int(user_id),
                    text=weather_msg,
                    parse_mode='HTML',
                    reply_markup=get_menu_keyboard()
                ))
                print(f"✅ Отправлено {user_id} ({city})")
        except Exception as e:
            print(f"❌ Ошибка для {user_id}: {e}")

def scheduler_thread():
    global last_send_time
    last_send_time = None
    
    while True:
        current_time = get_local_hour_minute()
        
        if current_time == "08:00" and last_send_time != "08:00":
            send_weather_to_all()
        
        time.sleep(60)

def main():
    global application_global
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application_global = application
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setcity", setcity))
    application.add_handler(CommandHandler("weather", weather))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    thread = threading.Thread(target=scheduler_thread, daemon=True)
    thread.start()
    
    print("🤖 Бот запущен!")
    print("📅 Расписание: каждый день в 8:00 (московское время)")
    print("⏰ Текущее время:", get_local_time())
    
    application.run_polling()

if __name__ == '__main__':
    main()
