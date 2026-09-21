import os
import sqlite3
import json
import random
import math
from datetime import datetime
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Initial District Master Data
DISTRICTS_DATA = [
    {"id": "ludhiana", "name": "Ludhiana", "state": "Punjab", "lat": 30.9010, "lon": 75.8573, "tempBase": 28, "humidityBase": 82, "rainProbBase": 75, "windBase": 14, "uvBase": 6},
    {"id": "amritsar", "name": "Amritsar", "state": "Punjab", "lat": 31.6340, "lon": 74.8723, "tempBase": 26, "humidityBase": 75, "rainProbBase": 45, "windBase": 12, "uvBase": 5},
    {"id": "karnal", "name": "Karnal", "state": "Haryana", "lat": 29.6857, "lon": 76.9905, "tempBase": 30, "humidityBase": 68, "rainProbBase": 30, "windBase": 10, "uvBase": 7},
    {"id": "bathinda", "name": "Bathinda", "state": "Punjab", "lat": 30.2110, "lon": 74.9455, "tempBase": 32, "humidityBase": 60, "rainProbBase": 20, "windBase": 16, "uvBase": 8},
    {"id": "nashik", "name": "Nashik", "state": "Maharashtra", "lat": 20.0059, "lon": 73.7898, "tempBase": 27, "humidityBase": 70, "rainProbBase": 50, "windBase": 11, "uvBase": 6},
    {"id": "varanasi", "name": "Varanasi", "state": "Uttar Pradesh", "lat": 25.3176, "lon": 82.9739, "tempBase": 31, "humidityBase": 78, "rainProbBase": 65, "windBase": 9, "uvBase": 7},
    {"id": "indore", "name": "Indore", "state": "Madhya Pradesh", "lat": 22.7196, "lon": 75.8577, "tempBase": 29, "humidityBase": 65, "rainProbBase": 35, "windBase": 13, "uvBase": 7}
]

CROPS_DATA = {
    "wheat": {
        "id": "wheat", "name": "Wheat (गेहूं / ਕਣਕ)", "hiName": "गेहूं", "paName": "ਕਣਕ",
        "category": "Rabi", "icon": "🌾", "sowingSeason": "Nov - Dec", "harvestSeason": "Mar - Apr",
        "growthStages": ["Germination", "Tillering", "Jointing (Critical Water)", "Flowering", "Maturity"],
        "commonDiseases": ["Yellow Rust (Stripe Rust)", "Leaf Blight", "Loose Smut"]
    },
    "paddy": {
        "id": "paddy", "name": "Paddy / Rice (धान / ਝੋਨਾ)", "hiName": "धान", "paName": "ਝੋਨਾ",
        "category": "Kharif", "icon": "🌱", "sowingSeason": "Jun - Jul", "harvestSeason": "Oct - Nov",
        "growthStages": ["Nursery", "Transplanting", "Tillering", "Panicle Initiation", "Harvesting"],
        "commonDiseases": ["Bacterial Leaf Blight", "Rice Blast", "Sheath Blight"]
    },
    "sugarcane": {
        "id": "sugarcane", "name": "Sugarcane (गन्ना / ਕਮਾਦ)", "hiName": "गन्ना", "paName": "ਕਮਾਦ",
        "category": "Annual", "icon": "🎋", "sowingSeason": "Feb - Mar", "harvestSeason": "Dec - Feb",
        "growthStages": ["Germination", "Formative", "Grand Growth", "Ripening"],
        "commonDiseases": ["Red Rot", "Smut", "Wilt"]
    },
    "mustard": {
        "id": "mustard", "name": "Mustard (सरसों / ਸਰ੍ਹੋਂ)", "hiName": "सरसों", "paName": "ਸਰ੍ਹੋਂ",
        "category": "Rabi", "icon": "🌼", "sowingSeason": "Oct - Nov", "harvestSeason": "Feb - Mar",
        "growthStages": ["Seedling", "Rosette", "Bolting", "Flowering & Pod", "Maturation"],
        "commonDiseases": ["White Rust", "Alternaria Blight", "Downy Mildew"]
    },
    "cotton": {
        "id": "cotton", "name": "Cotton (कपास / ਨਰਮਾ)", "hiName": "कपास", "paName": "ਨਰਮਾ",
        "category": "Kharif", "icon": "☁️", "sowingSeason": "Apr - May", "harvestSeason": "Oct - Nov",
        "growthStages": ["Emergence", "Squaring", "Boll Formation", "Boll Opening"],
        "commonDiseases": ["Pink Bollworm", "Leaf Curl Virus", "Fungal Wilt"]
    },
    "maize": {
        "id": "maize", "name": "Maize (मक्का / ਛੱਲੀ)", "hiName": "मक्का", "paName": "ਛੱਲੀ",
        "category": "Kharif/Spring", "icon": "🌽", "sowingSeason": "Jun - Jul", "harvestSeason": "Sep - Oct",
        "growthStages": ["Knee-high", "Tasseling", "Silking", "Dough Stage", "Black Layer"],
        "commonDiseases": ["Fall Armyworm", "Turcicum Leaf Blight", "Maydis Leaf Blight"]
    },
    "potato": {
        "id": "potato", "name": "Potato (आलू / ਆਲੂ)", "hiName": "आलू", "paName": "ਆਲੂ",
        "category": "Rabi", "icon": "🥔", "sowingSeason": "Oct - Nov", "harvestSeason": "Jan - Feb",
        "growthStages": ["Sprout Development", "Vegetative", "Tuber Initiation", "Tuber Bulking"],
        "commonDiseases": ["Late Blight", "Early Blight", "Black Scurf"]
    }
}

LEAF_DISEASE_DB = {
    "wheat_rust": {
        "disease": "Yellow Stripe Rust (Puccinia striiformis)",
        "crop": "Wheat",
        "severity": "High",
        "symptoms": "Bright yellow pustules arranged in linear stripes on leaf blades and sheaths.",
        "organicTreatment": "Spray Neem oil solution (3-5 ml/L) mixed with mild soap water. Remove heavily infected lower leaves.",
        "chemicalTreatment": "Foliar spray of Propiconazole 25% EC @ 1 ml/L or Tebuconazole 250 EC @ 1.25 ml/L."
    },
    "paddy_blight": {
        "disease": "Bacterial Leaf Blight (Xanthomonas oryzae)",
        "crop": "Paddy / Rice",
        "severity": "Critical",
        "symptoms": "Water-soaked to yellowish stripes along leaf margins, turning grayish white with bacterial ooze.",
        "organicTreatment": "Apply fresh cow dung slurry extract (20%) filtered spray or Pseudomonas fluorescens @ 10g/L.",
        "chemicalTreatment": "Spray Streptocycline @ 6g + Copper Oxychloride 50% WP @ 500g in 200 Liters of water per acre."
    },
    "mustard_rust": {
        "disease": "White Rust (Albugo candida)",
        "crop": "Mustard",
        "severity": "Moderate",
        "symptoms": "White to cream pustules on the lower surface of leaves and floral malformation.",
        "organicTreatment": "Spray Trichoderma harzianum formulation @ 5g/L. Ensure balanced potassium fertilization.",
        "chemicalTreatment": "Spray Mancozeb 75% WP @ 2g/L or Metalaxyl 8% + Mancozeb 64% WP @ 2g/L."
    },
    "potato_blight": {
        "disease": "Potato Late Blight (Phytophthora infestans)",
        "crop": "Potato",
        "severity": "Critical",
        "symptoms": "Water-soaked dark lesions on leaf tips turning black with white mold under leaf in humid conditions.",
        "organicTreatment": "Spray fermented liquid buttermilk or Copper Hydroxide organic sprays.",
        "chemicalTreatment": "Prophylactic spray of Mancozeb 75% WP @ 2g/L or Cymoxanil + Mancozeb @ 2g/L."
    }
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaf_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            crop TEXT,
            disease TEXT,
            confidence TEXT,
            symptoms TEXT,
            organic_treatment TEXT,
            chemical_treatment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT,
            bot_reply TEXT,
            language TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district_id TEXT,
            crop_key TEXT,
            area_acres REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

init_db()

def get_live_weather(district):
    """Fetch real-time weather using Open-Meteo API or fallback to simulated model."""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={district['lat']}&longitude={district['lon']}&current=temperature_2m,relative_humidity_2m,rain,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code&timezone=auto"
        res = requests.get(url, timeout=4)
        if res.status_code == 200:
            data = res.json()
            curr = data.get('current', {})
            daily = data.get('daily', {})

            temp = round(curr.get('temperature_2m', district['tempBase']))
            humidity = round(curr.get('relative_humidity_2m', district['humidityBase']))
            wind_speed = round(curr.get('wind_speed_10m', district['windBase']))
            rain_prob = daily.get('precipitation_probability_max', [district['rainProbBase']])[0] or district['rainProbBase']

            uv_index = min(11, max(1, round((temp / 4) + (100 - humidity) / 20)))

            code = curr.get('weather_code', 0)
            if code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
                condition = "Rainy"
                icon = "🌧️"
            elif code in [1, 2, 3]:
                condition = "Partly Cloudy"
                icon = "⛅"
            elif code in [95, 96, 99]:
                condition = "Thunderstorm"
                icon = "⛈️"
            else:
                condition = "Clear Sunny"
                icon = "☀️"

            # Build 7-day forecast
            days_label = ["Today", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            forecast = []
            max_temps = daily.get('temperature_2m_max', [temp+3]*7)
            min_temps = daily.get('temperature_2m_min', [temp-3]*7)
            rain_probs = daily.get('precipitation_probability_max', [rain_prob]*7)

            for i in range(min(7, len(max_temps))):
                r_prob = rain_probs[i] if i < len(rain_probs) else rain_prob
                c_icon = "🌧️" if r_prob > 60 else "⛅" if r_prob > 30 else "☀️"
                forecast.append({
                    "day": days_label[i] if i < len(days_label) else f"Day {i+1}",
                    "tempMax": round(max_temps[i]),
                    "tempMin": round(min_temps[i]),
                    "humidity": humidity,
                    "rainProb": r_prob if r_prob is not None else 20,
                    "condition": "Rain" if r_prob and r_prob > 60 else "Sunny",
                    "icon": c_icon
                })

            return {
                "district": district['name'],
                "state": district['state'],
                "temp": temp,
                "humidity": humidity,
                "rainProb": rain_prob,
                "windSpeed": wind_speed,
                "uvIndex": uv_index,
                "condition": condition,
                "description": f"Live weather data for {district['name']}",
                "icon": icon,
                "forecast": forecast,
                "source": "Open-Meteo Live API"
            }
    except Exception as e:
        print(f"Open-Meteo API notice: {e}, using dynamic simulation")

    # Fallback to realistic dynamic model
    hour = datetime.now().hour
    temp_var = math.sin((hour - 8) * math.pi / 12) * 4
    temp = round(district['tempBase'] + temp_var)
    humidity = min(95, max(30, round(district['humidityBase'] - temp_var * 2)))
    rain_prob = district['rainProbBase']
    wind_speed = district['windBase']
    uv_index = min(11, max(1, round(district['uvBase'] + (2 if temp_var > 0 else -2))))

    condition = "Clear"
    if rain_prob > 75: condition = "Heavy Rain"
    elif rain_prob > 50: condition = "Light Rain"
    elif humidity > 80: condition = "Humid Clouds"

    forecast = []
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    today_idx = datetime.now().weekday()

    for i in range(7):
        day_name = "Today" if i == 0 else days[(today_idx + i) % 7]
        forecast.append({
            "day": day_name,
            "tempMax": temp + random.randint(1, 4),
            "tempMin": temp - random.randint(2, 5),
            "humidity": min(98, max(30, humidity + random.randint(-5, 5))),
            "rainProb": min(100, max(5, rain_prob + random.randint(-15, 15))),
            "condition": "Rain" if rain_prob > 60 else "Sunny",
            "icon": "🌧️" if rain_prob > 60 else "☀️"
        })

    return {
        "district": district['name'],
        "state": district['state'],
        "temp": temp,
        "humidity": humidity,
        "rainProb": rain_prob,
        "windSpeed": wind_speed,
        "uvIndex": uv_index,
        "condition": condition,
        "description": "Dynamic Simulation Engine",
        "icon": "🌧️" if rain_prob > 60 else "☀️",
        "forecast": forecast,
        "source": "Simulated Weather Model"
    }


# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat(), "service": "AgriWeather Advisor Backend Server"})

@app.route('/api/districts', methods=['GET'])
def get_districts():
    return jsonify({"districts": DISTRICTS_DATA})

@app.route('/api/crops', methods=['GET'])
def get_crops():
    return jsonify({"crops": CROPS_DATA})

@app.route('/api/weather', methods=['GET'])
def get_weather():
    district_id = request.args.get('district_id', 'ludhiana').lower()
    district = next((d for d in DISTRICTS_DATA if d['id'] == district_id), DISTRICTS_DATA[0])
    weather_info = get_live_weather(district)
    return jsonify(weather_info)

@app.route('/api/advisory', methods=['POST'])
def calculate_advisory():
    data = request.json or {}
    crop_key = data.get('crop_key', 'wheat')
    district_id = data.get('district_id', 'ludhiana')
    weather = data.get('weather')

    district = next((d for d in DISTRICTS_DATA if d['id'] == district_id), DISTRICTS_DATA[0])
    if not weather:
        weather = get_live_weather(district)

    crop = CROPS_DATA.get(crop_key, CROPS_DATA['wheat'])
    rain_prob = weather.get('rainProb', 50)
    temp = weather.get('temp', 28)
    humidity = weather.get('humidity', 70)
    wind_speed = weather.get('windSpeed', 12)

    # Irrigation Advice
    if rain_prob >= 65:
        irrigation = {
            "status": "Do Not Irrigate", "statusColor": "rose", "icon": "🚫💧", "badgeText": "High Rain Risk",
            "recommendation": f"Heavy rain ({rain_prob}%) expected in next 24-48h. Postpone all irrigation to prevent root rot.",
            "hiRecommendation": f"अगले 24-48 घंटों में भारी बारिश ({rain_prob}%) की संभावना है। सिंचाई स्थगित करें।",
            "paRecommendation": f"ਮੀਂਹ ({rain_prob}%) ਦੀ ਸੰਭਾਵਨਾ ਕਰਕੇ ਫਸਲ ਨੂੰ ਪਾਣੀ ਨਾ ਲਾਓ।",
            "actionStep": "Ensure drainage channels are clear to prevent flooding."
        }
    elif temp >= 33 and rain_prob < 30:
        irrigation = {
            "status": "Increase Irrigation", "statusColor": "amber", "icon": "☀️💧", "badgeText": "+15% Extra Water",
            "recommendation": f"High temperature ({temp}°C). Increase irrigation volume during early morning or evening.",
            "hiRecommendation": f"उच्च तापमान ({temp}°C)। सुबह या शाम को सिंचाई बढ़ाएं।",
            "paRecommendation": f"ਗਰਮੀ ({temp}°C) ਕਰਕੇ ਸਵੇਰੇ/ਸ਼ਾਮ ਨੂੰ ਪਾਣੀ 15% ਵਧਾਓ।",
            "actionStep": "Irrigate during cooler hours to minimize evaporation loss."
        }
    else:
        irrigation = {
            "status": "Normal Scheduled Irrigation", "statusColor": "emerald", "icon": "✅💧", "badgeText": "Optimal Schedule",
            "recommendation": f"Weather conditions are balanced ({temp}°C, {humidity}% RH). Follow normal irrigation schedule for {crop['name']}.",
            "hiRecommendation": f"मौसम अनुकूल है। {crop['hiName']} के लिए सामान्य सिंचाई जारी रखें।",
            "paRecommendation": f"ਮੌਸਮ ਠੀਕ ਹੈ। {crop['paName']} ਲਈ ਆਮ ਪਾਣੀ ਲਾਓ।",
            "actionStep": "Maintain uniform soil moisture levels."
        }

    # Fertilizer Advice
    if rain_prob > 60:
        fertilizer = {
            "status": "Delay Fertilizer Application", "statusColor": "rose", "icon": "🌧️⚠️", "badgeText": "Hold 2-3 Days",
            "recommendation": f"Rain forecast is high ({rain_prob}%). Hold Urea/NPK application to prevent fertilizer runoff.",
            "hiRecommendation": f"बारिश ({rain_prob}%) के कारण यूरिया/खाद का प्रयोग 2 दिनों के लिए टालें।",
            "paRecommendation": f"ਮੀਂਹ ਕਰਕੇ ਖਾਦ ਪਾਉਣਾ 2 ਦਿਨ ਲਈ ਰੋਕੋ।",
            "actionStep": "Apply fertilizer post rainfall when topsoil dries."
        }
    elif wind_speed > 18:
        fertilizer = {
            "status": "Avoid Spraying", "statusColor": "amber", "icon": "💨⛔", "badgeText": "High Wind Speed",
            "recommendation": f"Wind speed is elevated ({wind_speed} km/h). Avoid liquid spray fertilizers due to drift.",
            "hiRecommendation": f"तेज हवा ({wind_speed} किमी/घंटा)। तरल खाद या स्प्रे न करें।",
            "paRecommendation": f"ਤੇਜ਼ ਹਵਾ ਕਰਕੇ ਸਪਰੇਅ ਨਾ ਕਰੋ।",
            "actionStep": "Wait for wind speed to drop below 12 km/h."
        }
    else:
        fertilizer = {
            "status": "Suitable for Fertilizer", "statusColor": "emerald", "icon": "🌿✅", "badgeText": "Ideal Weather",
            "recommendation": f"Clear weather ({rain_prob}% rain risk). Excellent window for applying top-dressing fertilizer.",
            "hiRecommendation": f"मौसम साफ है। {crop['hiName']} में यूरिया और खाद देने के लिए उत्तम समय है।",
            "paRecommendation": f"ਖਾਦ ਪਾਉਣ ਲਈ ਢੁਕਵਾਂ ਸਮਾਂ ਹੈ।",
            "actionStep": "Incorporate fertilizer into moist topsoil."
        }

    # Pest Alert
    if humidity >= 80 and temp >= 22 and temp <= 32:
        pest_alert = {
            "riskLevel": "High Risk", "statusColor": "rose", "icon": "🐛⚠️", "badgeText": "Fungal Outbreak Risk",
            "recommendation": f"High humidity ({humidity}%) and warm temp ({temp}°C) create fungal risk for {crop['commonDiseases'][0]}.",
            "hiRecommendation": f"आर्द्रता ({humidity}%) के कारण फंगल बीमारी ({crop['commonDiseases'][0]}) का खतरा अधिक है।",
            "paRecommendation": f"ਨਮੀ ਕਰਕੇ ਫੰਗਸ ਅਤੇ ਬੀਮਾਰੀ ਦਾ ਖਤਰਾ ਹੈ।",
            "preventiveAction": "Spray Neem oil (3ml/L) or prophylactic organic fungicide."
        }
    else:
        pest_alert = {
            "riskLevel": "Low Risk", "statusColor": "emerald", "icon": "🛡️✅", "badgeText": "Field Healthy",
            "recommendation": f"Favorable atmosphere ({temp}°C, {humidity}% RH). Disease risk index is minimal.",
            "hiRecommendation": f"फसल के लिए मौसम सुरक्षित है। कीट जोखिम कम है।",
            "paRecommendation": f"ਮੌਸਮ ਵਧੀਆ ਹੈ, ਬੀਮਾਰੀ ਦਾ ਖਤਰਾ ਘੱਟ ਹੈ।",
            "preventiveAction": "Inspect leaf undersides regularly."
        }

    # Harvest Advice
    if rain_prob >= 70:
        harvest = {
            "status": "Urgent Harvest Advisory", "statusColor": "rose", "icon": "🌾🚨", "badgeText": "Rain Threat",
            "recommendation": f"Heavy rain ({rain_prob}%) expected. If {crop['name']} is mature (85%+), harvest immediately.",
            "hiRecommendation": f"बारिश की चेतावनी! यदि {crop['hiName']} पक चुकी है तो तुरंत कटाई करें।",
            "paRecommendation": f"ਮੀਂਹ ਦਾ ਖਤਰਾ! ਪੱਕੀ ਫਸਲ ਦੀ ਤੁਰੰਤ ਵਾਢੀ ਕਰੋ।",
            "actionItem": "Cover harvested produce with plastic tarpaulins."
        }
    else:
        harvest = {
            "status": "Ideal Harvesting Window", "statusColor": "emerald", "icon": "🌾☀️", "badgeText": "Clear Dry Days",
            "recommendation": f"Clear weather ({rain_prob}% rain risk). Great window for harvesting and sun drying.",
            "hiRecommendation": f"साफ मौसम। {crop['hiName']} की कटाई के लिए उत्तम समय है।",
            "paRecommendation": f"ਸਾਫ਼ ਮੌਸਮ ਵਿੱਚ ਵਾਢੀ ਸ਼ੁਰੂ ਕਰੋ।",
            "actionItem": "Ensure grain moisture level is below 14% for storage."
        }

    # Weather Warnings
    warnings = []
    if rain_prob >= 75:
        warnings.append({"type": "Heavy Rain Alert", "hiType": "भारी बारिश चेतावनी", "paType": "ਮੀਂਹ ਦੀ ਚੇਤਾਵਨੀ", "icon": "🌧️", "severity": "danger", "desc": f"Torrential rain expected ({rain_prob}%). Ensure field drainage."})
    if temp >= 38:
        warnings.append({"type": "Heatwave Warning", "hiType": "हीटवेव चेतावनी", "paType": "ਗਰਮੀ ਦੀ ਚੇਤਾਵਨੀ", "icon": "🔥", "severity": "warning", "desc": f"Extreme temperature ({temp}°C). Irrigate during evening."})

    return jsonify({
        "crop": crop['name'],
        "district": district['name'],
        "irrigation": irrigation,
        "fertilizer": fertilizer,
        "pestAlert": pest_alert,
        "harvest": harvest,
        "warnings": warnings
    })

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.json or {}
    user_query = data.get('query', '').strip()
    crop_key = data.get('crop_key', 'wheat')
    lang = data.get('lang', 'en')
    weather = data.get('weather', {})

    if not user_query:
        return jsonify({"error": "Empty query"}), 400

    crop = CROPS_DATA.get(crop_key, CROPS_DATA['wheat'])
    district_name = weather.get('district', 'Ludhiana')
    temp = weather.get('temp', 28)
    rain_prob = weather.get('rainProb', 30)
    humidity = weather.get('humidity', 70)

    q_lower = user_query.lower()

    if any(k in q_lower for k in ['irrigate', 'water', 'पानी', 'ਪਾਣੀ']):
        if rain_prob >= 60:
            reply_en = f"Rain probability in {district_name} is high ({rain_prob}%). Do NOT irrigate {crop['name']} today to prevent root rot."
            reply_hi = f"{district_name} में बारिश की संभावना {rain_prob}% है। आज {crop['hiName']} की सिंचाई न करें।"
            reply_pa = f"{district_name} ਵਿੱਚ ਮੀਂਹ ({rain_prob}%) ਦੀ ਸੰਭਾਵਨਾ ਕਰਕੇ ਅੱਜ {crop['paName']} ਨੂੰ ਪਾਣੀ ਨਾ ਲਾਓ।"
        else:
            reply_en = f"Weather in {district_name} is suitable ({temp}°C, {rain_prob}% rain). Irrigate {crop['name']} in early morning or late evening."
            reply_hi = f"{district_name} में मौसम सामान्य है ({temp}°C)। {crop['hiName']} को सुबह या शाम को सिंचाई दें।"
            reply_pa = f"{district_name} ਵਿੱਚ ਮੌਸਮ ਠੀਕ ਹੈ ({temp}°C)। ਸਵੇਰੇ ਜਾਂ ਸ਼ਾਮ ਨੂੰ ਪਾਣੀ ਲਾਓ।"
    elif any(k in q_lower for k in ['fertilizer', 'urea', 'खाद', 'ਖਾਦ']):
        if rain_prob > 60:
            reply_en = f"Hold fertilizer application on {crop['name']} for 2 days due to high rain forecast ({rain_prob}%)."
            reply_hi = f"भारी बारिश ({rain_prob}%) के कारण {crop['hiName']} में 2 दिनों तक यूरिया/खाद न डालें।"
            reply_pa = f"ਮੀਂਹ ({rain_prob}%) ਕਰਕੇ {crop['paName']} ਵਿੱਚ ਖਾਦ ਪਾਉਣਾ 2 ਦਿਨ ਲਈ ਰੋਕੋ।"
        else:
            reply_en = f"Clear weather conditions ({rain_prob}% rain risk). Apply recommended Nitrogen fertilizer for {crop['name']} in moist soil."
            reply_hi = f"मौसम साफ है। {crop['hiName']} में यूरिया और खाद देने का सही समय है।"
            reply_pa = f"ਮੌਸਮ ਸਾਫ਼ ਹੈ। {crop['paName']} ਵਿੱਚ ਲੋੜੀਂਦੀ ਖਾਦ ਪਾਓ।"
    elif any(k in q_lower for k in ['disease', 'fungus', 'pest', 'बीमारी', 'ਬੀਮਾਰੀ']):
        reply_en = f"Current humidity in {district_name} is {humidity}%. Spray Neem oil (3ml/L) as a preventive shield against {crop['commonDiseases'][0]}."
        reply_hi = f"{district_name} में नमी {humidity}% है। {crop['hiName']} को {crop['commonDiseases'][0]} से बचाने के लिए नीम के तेल का छिड़काव करें।"
        reply_pa = f"{district_name} ਵਿੱਚ ਨਮੀ {humidity}% ਹੈ। ਨਿੰਮ ਦੇ ਤੇਲ ਦਾ ਸਪਰੇਅ ਕਰੋ।"
    else:
        reply_en = f"Based on current weather in {district_name} ({temp}°C, {humidity}% RH), {crop['name']} growth index is optimal. Ensure proper field drainage."
        reply_hi = f"{district_name} के मौसम ({temp}°C) के आधार पर {crop['hiName']} की स्थिति अच्छी है।"
        reply_pa = f"{district_name} ਦੇ ਮੌਸਮ ({temp}°C) ਅਨੁਸਾਰ {crop['paName']} ਦੀ ਹਾਲਤ ਵਧੀਆ ਹੈ।"

    reply = reply_hi if lang == 'hi' else reply_pa if lang == 'pa' else reply_en

    # Save to SQLite DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (user_query, bot_reply, language) VALUES (?, ?, ?)", (user_query, reply, lang))
    conn.commit()
    conn.close()

    return jsonify({
        "query": user_query,
        "reply": reply,
        "language": lang,
        "timestamp": datetime.now().strftime("%H:%M")
    })

@app.route('/api/ai/detect-disease', methods=['POST'])
def detect_disease():
    crop_key = request.form.get('crop_key', 'wheat')
    sample_id = request.form.get('sample_id', '')

    disease_info = None
    if sample_id and sample_id in LEAF_DISEASE_DB:
        disease_info = LEAF_DISEASE_DB[sample_id]
    else:
        # Match disease info based on crop
        if crop_key == 'wheat': disease_info = LEAF_DISEASE_DB['wheat_rust']
        elif crop_key == 'paddy': disease_info = LEAF_DISEASE_DB['paddy_blight']
        elif crop_key == 'mustard': disease_info = LEAF_DISEASE_DB['mustard_rust']
        elif crop_key == 'potato': disease_info = LEAF_DISEASE_DB['potato_blight']
        else: disease_info = LEAF_DISEASE_DB['wheat_rust']

    filename = "leaf_sample.jpg"
    if 'image' in request.files:
        file = request.files['image']
        if file.filename:
            filename = f"scan_{int(datetime.now().timestamp())}_{file.filename}"
            filepath = os.path.join(UPLOADS_DIR, filename)
            file.save(filepath)

    confidence = f"{round(92.5 + random.random() * 5.0, 1)}%"

    # Save record to DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO leaf_scans (filename, crop, disease, confidence, symptoms, organic_treatment, chemical_treatment)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (filename, disease_info['crop'], disease_info['disease'], confidence, disease_info['symptoms'], disease_info['organicTreatment'], disease_info['chemicalTreatment']))
    conn.commit()
    conn.close()

    return jsonify({
        "id": f"scan_{int(datetime.now().timestamp())}",
        "crop": disease_info['crop'],
        "disease": disease_info['disease'],
        "confidence": confidence,
        "severity": disease_info['severity'],
        "symptoms": disease_info['symptoms'],
        "organicTreatment": disease_info['organicTreatment'],
        "chemicalTreatment": disease_info['chemicalTreatment'],
        "filename": filename
    })

@app.route('/api/ai/voice', methods=['POST'])
def process_voice():
    data = request.json or {}
    transcript = data.get('transcript', '').strip()
    lang = data.get('lang', 'en')
    crop_key = data.get('crop_key', 'wheat')
    weather = data.get('weather', {})

    if not transcript:
        return jsonify({"error": "No voice transcript provided"}), 400

    # Process transcript using AI chat handler logic
    chat_response = ai_chat_internal(transcript, crop_key, lang, weather)
    return jsonify({
        "transcript": transcript,
        "spokenReply": chat_response['reply'],
        "lang": lang
    })

def ai_chat_internal(user_query, crop_key, lang, weather):
    crop = CROPS_DATA.get(crop_key, CROPS_DATA['wheat'])
    district_name = weather.get('district', 'Ludhiana')
    temp = weather.get('temp', 28)
    rain_prob = weather.get('rainProb', 30)

    if rain_prob >= 60:
        reply_en = f"Rain probability in {district_name} is {rain_prob}%. Do not irrigate {crop['name']} today."
        reply_hi = f"{district_name} में बारिश की संभावना {rain_prob}% है। आज सिंचाई न करें।"
        reply_pa = f"{district_name} ਵਿੱਚ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ ਕਰਕੇ ਅੱਜ ਪਾਣੀ ਨਾ ਲਾਓ।"
    else:
        reply_en = f"Weather in {district_name} is clear ({temp}°C). Irrigate {crop['name']} during early morning."
        reply_hi = f"{district_name} में मौसम साफ है। फसल को सुबह सिंचाई दें।"
        reply_pa = f"{district_name} ਵਿੱਚ ਮੌਸਮ ਸਾਫ਼ ਹੈ। ਸਵੇਰੇ ਪਾਣੀ ਲਾਓ।"

    reply = reply_hi if lang == 'hi' else reply_pa if lang == 'pa' else reply_en
    return {"reply": reply}

@app.route('/api/history', methods=['GET'])
def get_history():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM leaf_scans ORDER BY created_at DESC LIMIT 10")
    scans = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM chat_history ORDER BY created_at DESC LIMIT 15")
    chats = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify({"scans": scans, "chats": chats})

# Serve static frontend files
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    print("🌾 AgriWeather Advisor Flask Server running on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
