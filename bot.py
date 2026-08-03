import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
import requests
from datetime import datetime, timedelta
from supabase import create_client, Client

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

def translate_city(city):
    city_lower = city.lower().strip()
    return CITY_TRANSLATION.get(city_lower, city)

def get_local_time():
    utc_time = datetime.utcnow()
    moscow_time = utc_time + timedelta(hours=3)
    return moscow_time.strftime('%H:%M:%S')

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
    except:
        return None

def get_menu_keyboard():
    keyboard = [
        ['🌤 Погода сейчас', '⚙️ Установить город'],
        ['❓ Справка']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = """👋 Привет! Я бот прогноза погоды.

Просто напишите название города (Москва, Казань и т.д.) или используйте кнопки ниже.

В 8:00 каждый день вы будете получать прогноз для вашего города."""
    await update.message.reply_text(message, reply_markup=get_menu_keyboard())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    
    if text == "🌤 Погода сейчас":
        try:
            response = supabase.table("users").select("city").eq("user_id", user_id).execute()
            if not response.data:
                await update.message.reply_text("❌ Сначала установите город", reply_markup=get_menu_keyboard())
                return
            city = response.data[0]['city']
            await update.message.chat.send_action(ChatAction.TYPING)
            weather_msg = get_weather(city)
            if weather_msg:
                await update.message.reply_text(weather_msg, parse_mode='HTML', reply_markup=get_menu_keyboard())
        except Exception as e:
            await update.message.reply_text("❌ Ошибка", reply_markup=get_menu_keyboard())
        return
    elif text == "⚙️ Установить город":
        await update.message.reply_text("Напишите название города:", reply_markup=get_menu_keyboard())
        return
    elif text == "❓ Справка":
        await update.message.reply_text("📖 Используйте кнопки или напишите город", reply_markup=get_menu_keyboard())
        return
    
    if text.startswith('/'):
        return
    
    weather_msg = get_weather(text)
    
    if not weather_msg:
        await update.message.reply_text(f"❌ Город '{text}' не найден.", reply_markup=get_menu_keyboard())
        return
    
    try:
        city_en = translate_city(text)
        supabase.table("users").upsert({
            "user_id": user_id,
            "city": text
        }).execute()
        await update.message.reply_text(f"✅ Город установлен: <b>{city_en.title()}</b>", parse_mode='HTML', reply_markup=get_menu_keyboard())
        await update.message.reply_text(weather_msg, parse_mode='HTML', reply_markup=get_menu_keyboard())
    except Exception as e:
        await update.message.reply_text("❌ Ошибка при сохранении города", reply_markup=get_menu_keyboard())

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🤖 Бот запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()
