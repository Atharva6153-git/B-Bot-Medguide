from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory # type: ignore
from pymongo import MongoClient # type: ignore
from flask_bcrypt import Bcrypt # type: ignore
import os
from werkzeug.utils import secure_filename # type: ignore
from datetime import datetime
from bson.objectid import ObjectId # type: ignore
from groq import Groq # type: ignore
from dotenv import load_dotenv
import os
load_dotenv()

print("MONGO_URI:", os.getenv("MONGO_URI"))

# ── Groq AI Setup ──
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ── MongoDB Connection ──
import certifi
mongo_client = MongoClient(
    os.getenv("MONGO_URI"),
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=5000
)
db = mongo_client['medguide']
users_collection = db['users']
history_collection = db['patient_history']

bcrypt = Bcrypt(app)

# ── File Upload Config ──
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ── Medicine Data ──
illness_medicines = {
    "cold": {
        "child": [
            {"name": "Paracetamol Syrup", "dose": "5ml, 2 times a day", "type": "painkiller"},
            {"name": "Cough Syrup", "dose": "5ml, 3 times a day", "type": "other"}
        ],
        "adult": [
            {"name": "Paracetamol", "dose": "500mg, 2 times a day after meals", "type": "painkiller"},
            {"name": "Cough Syrup", "dose": "10ml, 3 times a day", "type": "other"}
        ],
        "senior": [
            {"name": "Paracetamol", "dose": "500mg, 1-2 times a day", "type": "painkiller"},
            {"name": "Cough Syrup", "dose": "10ml, 2 times a day", "type": "other"}
        ]
    },
    "infection": {
        "child": [
            {"name": "Amoxicillin Syrup", "dose": "5ml, 3 times a day for 7 days", "type": "antibiotic"},
        ],
        "adult": [
            {"name": "Amoxicillin", "dose": "250mg, 3 times a day for 7 days", "type": "antibiotic"},
            {"name": "Paracetamol", "dose": "500mg, 2 times a day", "type": "painkiller"}
        ],
        "senior": [
            {"name": "Amoxicillin", "dose": "250mg, 2 times a day for 7 days", "type": "antibiotic"},
            {"name": "Paracetamol", "dose": "500mg, 1-2 times a day", "type": "painkiller"}
        ]
    },
    "vitamin deficiency": {
        "child": [{"name": "Vitamin C Syrup", "dose": "5ml, once a day", "type": "vitamin"}],
        "adult": [{"name": "Vitamin C", "dose": "1000mg, once a day", "type": "vitamin"}],
        "senior": [{"name": "Vitamin C", "dose": "500mg, once a day", "type": "vitamin"}]
    },
    "headache": {
        "child": [{"name": "Paracetamol Syrup", "dose": "5ml, as needed", "type": "painkiller"}],
        "adult": [{"name": "Ibuprofen", "dose": "400mg, 2 times a day after meals", "type": "painkiller"}],
        "senior": [{"name": "Ibuprofen", "dose": "200mg, as needed", "type": "painkiller"}]
    },
    "allergy": {
        "child": [{"name": "Cetirizine Syrup", "dose": "5ml, once a day", "type": "other"}],
        "adult": [{"name": "Cetirizine", "dose": "10mg, once a day", "type": "other"}],
        "senior": [{"name": "Cetirizine", "dose": "5mg, once a day", "type": "other"}]
    }
}

age_groups = ["child", "adult", "senior"]

# ── Routes ──

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    selected_illness = None
    selected_age = None
    medicines = []

    if request.method == 'POST':
        selected_illness = request.form.get('illness')
        selected_age = request.form.get('age')
        if selected_illness and selected_age:
            medicines = illness_medicines.get(selected_illness, {}).get(selected_age, [])

    return render_template('index.html',
        illnesses=list(illness_medicines.keys()),
        age_groups=age_groups,
        selected_illness=selected_illness,
        selected_age=selected_age,
        medicines=medicines
    )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        age = request.form.get('age')
        blood_group = request.form.get('blood_group')

        if users_collection.find_one({'email': email}):
            flash('Email already registered!', 'danger')
            return redirect(url_for('signup'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.insert_one({
            'username': username,
            'email': email,
            'password': hashed_pw,
            'age': age,
            'blood_group': blood_group,
            'created_at': datetime.utcnow()
        })
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = users_collection.find_one({'email': email})

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user'] = str(user['_id'])
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password!', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/history', methods=['GET', 'POST'])
def history():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        notes = request.form.get('notes')
        medical_condition = request.form.get('medical_condition')
        file = request.files.get('file')
        filename = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        history_collection.insert_one({
            'user_id': session['user'],
            'username': session['username'],
            'notes': notes,
            'medical_condition': medical_condition,
            'file': filename,
            'timestamp': datetime.now()
        })
        flash('Record saved successfully!', 'success')
        return redirect(url_for('history'))

    records = list(history_collection.find({'user_id': session['user']}).sort('timestamp', -1))
    return render_template('history.html', records=records)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if 'user' not in session:
        return redirect(url_for('login'))

    response = None
    user_message = None

    if request.method == 'POST':
        user_message = request.form.get('message')
        age = request.form.get('age')

        prompt = f"""
        You are a medical assistant chatbot.
        A patient aged {age} years is saying: {user_message}

        Please:
        1. Identify the possible illness based on symptoms
        2. Suggest medicines suitable for age {age}
        3. Give dosage instructions
        4. Add a warning to consult a doctor

        Keep the response simple and clear.
        """

        try:
            result = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            response = result.choices[0].message.content
        except Exception as e:
            response = f"Error: {str(e)}"

    return render_template('chatbot.html', response=response, user_message=user_message)

import base64

@app.route('/skin', methods=['GET', 'POST'])
def skin():
    if 'user' not in session:
        return redirect(url_for('login'))

    response = None

    if request.method == 'POST':
        file = request.files.get('image')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                # Convert image to base64
                with open(filepath, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')

                # Get file extension
                ext = filename.rsplit('.', 1)[1].lower()
                mime_type = f"image/{ext}" if ext != 'jpg' else 'image/jpeg'

                result = groq_client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """You are a medical skin specialist AI.
                                Analyze this skin image and provide:
                                1. Name of the skin condition or infection
                                2. Reasons/causes of this infection
                                3. Recommended medicines and treatments
                                4. Skincare tips
                                5. Warning to consult a dermatologist if it worsens
                                Keep the response clear and simple."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{img_data}"
                                }
                            }
                        ]
                    }],
                    max_tokens=1024
                )
                response = result.choices[0].message.content

            except Exception as e:
                response = f"Error: {str(e)}"

    return render_template('skin.html', response=response)

@app.route('/fever-ratio', methods=['GET', 'POST'])
def fever_ratio():
    if 'user' not in session:
        return redirect(url_for('login'))

    all_ratios = {
        "Viral Fever":  {"probability": 55, "color": "#4CAF50", "description": "Most common cause of fever. Usually resolves in 3-5 days.", "keywords": ["fever", "cold", "runny nose", "mild", "cough", "sneezing"]},
        "Dengue":       {"probability": 20, "color": "#FF5722", "description": "Caused by mosquito bite. Watch for rash and low platelet count.", "keywords": ["rash", "dengue", "mosquito", "platelet", "eye pain", "joint pain"]},
        "Malaria":      {"probability": 15, "color": "#FF9800", "description": "Caused by Plasmodium parasite via mosquito. Recurring chills common.", "keywords": ["chills", "malaria", "shivering", "sweating", "recurring", "mosquito"]},
        "Typhoid":      {"probability": 7,  "color": "#9C27B0", "description": "Bacterial infection via contaminated food/water. Persistent high fever.", "keywords": ["typhoid", "stomach", "abdominal", "diarrhea", "constipation", "food"]},
        "COVID-19":     {"probability": 3,  "color": "#2196F3", "description": "Viral infection. May include loss of smell/taste, breathlessness.", "keywords": ["covid", "smell", "taste", "breathless", "oxygen", "corona"]},
    }

    ratios = {}
    symptoms = None

    if request.method == 'POST':
        symptoms = request.form.get('symptoms', '').lower()
        symptom_words = [s.strip() for s in symptoms.replace(',', ' ').split()]

        for illness, data in all_ratios.items():
            for keyword in data['keywords']: # type: ignore
                if any(keyword in word or word in keyword for word in symptom_words):
                    ratios[illness] = data
                    break

        if not ratios:
            ratios = {}

    return render_template('fever_ratio.html', ratios=ratios, symptoms=symptoms)

@app.route('/hospitals')
def hospitals():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('hospitals.html')

@app.route('/api/nearest_hospital', methods=['POST'])
def nearest_hospital():
    import urllib.request
    import json
    import math

    data = request.get_json()
    try:
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
    except (TypeError, ValueError):
        return {"error": "Invalid coordinates"}, 400

    query = f"""
        [out:json][timeout:10];
        (
            node["amenity"="hospital"](around:10000,{lat},{lon});
            node["amenity"="clinic"](around:10000,{lat},{lon});
        );
        out body limit 1;
    """

    try:
        req = urllib.request.Request(
            'https://overpass-api.de/api/interpreter', 
            data=query.encode('utf-8'), 
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if res_data.get('elements') and len(res_data['elements']) > 0:
                return res_data
    except Exception as e:
        print(f"Overpass API failed: {e}")

    # Fallback Database
    FALLBACK_HOSPITALS = [
        {"name": "Apollo Hospitals", "lat": 19.033, "lon": 73.029, "phone": "+91-22-3350-3350"},
        {"name": "Fortis Hospital", "lat": 28.6139, "lon": 77.2090, "phone": "+91-11-4713-5000"},
        {"name": "Manipal Hospital", "lat": 12.9716, "lon": 77.5946, "phone": "1800-102-5555"},
        {"name": "KEM Hospital", "lat": 19.0028, "lon": 72.8419, "phone": "+91-22-2410-7000"},
        {"name": "AIIMS", "lat": 28.5659, "lon": 77.2089, "phone": "+91-11-2658-8500"},
        {"name": "Safdarjung Hospital", "lat": 28.5684, "lon": 77.2057, "phone": "+91-11-2616-5060"},
        {"name": "Narayana Health", "lat": 12.8154, "lon": 77.6921, "phone": "1860-208-0208"},
        {"name": "CMC Vellore", "lat": 12.9248, "lon": 79.1350, "phone": "+91-416-228-1000"}
    ]

    def get_dist(hlat, hlon):
        R = 6371
        dlat = math.radians(hlat - lat)
        dlon = math.radians(hlon - lon)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat)) * math.cos(math.radians(hlat)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    FALLBACK_HOSPITALS.sort(key=lambda h: get_dist(h["lat"], h["lon"]))
    nearest = FALLBACK_HOSPITALS[0]
    
    if get_dist(nearest["lat"], nearest["lon"]) > 100:
        nearest = {
            "name": "City Central Emergency Care",
            "lat": lat + 0.01,
            "lon": lon + 0.01,
            "phone": "108"
        }

    fallback_data = {
        "elements": [
            {
                "tags": {
                    "name": nearest["name"],
                    "phone": nearest["phone"]
                }
            }
        ]
    }
    return fallback_data

if __name__ == '__main__':
    app.run(debug=True)