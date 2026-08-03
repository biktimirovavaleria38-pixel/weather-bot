import os
import requests
import asyncio
from telegram import Bot
from supabase import create_client, Client
from datetime import datetime, timedelta

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

async def send_all():
    try:
        response = supabase.table("users").select("user_id, city").execute()
        users = response.data
        
        if not users:
            print("No users")
            return
        
        bot = Bot(token=TELEGRAM_TOKEN)
        
        for user in users:
            try:
                user_id = user['user_id']
                city = user['city']
                weather_msg = get_weather(city)
                if weather_msg:
                    await bot.send_message(chat_id=int(user_id), text=weather_msg, parse_mode='HTML')
                    print(f"✅ {user_id} ({city})")
            except Exception as e:
                print(f"❌ {user['user_id']}: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(send_all())
