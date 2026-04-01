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
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)   # auto-create the folder if it doesn't exist
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

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)
    except FileNotFoundError:
        flash('File not found. It may have been deleted.', 'danger')
        return redirect(url_for('history'))

@app.route('/delete_record/<record_id>', methods=['POST'])
def delete_record(record_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    try:
        record = history_collection.find_one({
            '_id': ObjectId(record_id),
            'user_id': session['user']   # ensure users can only delete their own records
        })

        if record:
            # Delete the physical file if it exists
            if record.get('file'):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], record['file'])
                if os.path.exists(file_path):
                    os.remove(file_path)

            history_collection.delete_one({'_id': ObjectId(record_id)})
            flash('Record deleted successfully!', 'success')
        else:
            flash('Record not found or access denied.', 'danger')

    except Exception as e:
        flash(f'Error deleting record: {str(e)}', 'danger')

    return redirect(url_for('history'))

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

import json as json_module

DISEASE_COLORS = [
    "#4CAF50", "#FF5722", "#FF9800", "#9C27B0", "#2196F3",
    "#00BCD4", "#F44336", "#795548", "#607D8B", "#E91E63"
]

@app.route('/fever-ratio', methods=['GET', 'POST'])
def fever_ratio():
    if 'user' not in session:
        return redirect(url_for('login'))

    ratios = {}
    symptoms = None
    ai_error = None

    if request.method == 'POST':
        symptoms = request.form.get('symptoms', '').strip()

        ai_prompt = f"""You are an expert medical diagnostic AI. A patient reports the following symptoms: "{symptoms}"

Analyze these symptoms and return a JSON object listing the most likely diseases/conditions that could cause these symptoms, with probability percentages that SUM EXACTLY TO 100.

Return ONLY a valid JSON object (no markdown, no explanation) in this exact format:
{{
  "diseases": [
    {{
      "name": "Disease Name",
      "probability": <integer 1-100>,
      "description": "One-sentence description of this disease related to the given symptoms.",
      "warning_signs": [
        ["Symptom combination to watch", "Immediate action to take"],
        ["Symptom combination to watch", "Immediate action to take"],
        ["Symptom combination to watch", "Immediate action to take"]
      ],
      "action": "Specific recommended action for this disease based on the symptoms given."
    }}
  ]
}}

Rules:
- Include only diseases genuinely relevant to the given symptoms (minimum 2, maximum 6).
- Probabilities must be realistic and based on symptom overlap, not random.
- All probabilities must sum to exactly 100.
- warning_signs must be 3-4 entries, each an array of exactly 2 strings: [symptom_combo, action].
- Do NOT include any text outside the JSON object."""

        try:
            result = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": ai_prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            raw = result.choices[0].message.content.strip()

            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            parsed = json_module.loads(raw)
            diseases = parsed.get("diseases", [])

            for i, disease in enumerate(diseases):
                color = DISEASE_COLORS[i % len(DISEASE_COLORS)]
                name = disease.get("name", "Unknown")
                ratios[name] = {
                    "probability": disease.get("probability", 0),
                    "color": color,
                    "description": disease.get("description", ""),
                    "warning_signs": [
                        (ws[0], ws[1]) for ws in disease.get("warning_signs", [])
                    ],
                    "action": disease.get("action", "")
                }

        except Exception as e:
            ai_error = f"AI analysis failed: {str(e)}. Please try again."
            ratios = {}

    return render_template('fever_ratio.html', ratios=ratios, symptoms=symptoms, ai_error=ai_error)

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

    # Broad query — catches hospitals, clinics, doctors, pharmacies within 5 km
    query = f"""
        [out:json][timeout:30];
        (
            node["amenity"="hospital"](around:5000,{lat},{lon});
            way["amenity"="hospital"](around:5000,{lat},{lon});
            node["amenity"="clinic"](around:5000,{lat},{lon});
            way["amenity"="clinic"](around:5000,{lat},{lon});
            node["amenity"="doctors"](around:5000,{lat},{lon});
            node["healthcare"="hospital"](around:5000,{lat},{lon});
            node["healthcare"="clinic"](around:5000,{lat},{lon});
        );
        out center 30;
    """

    # Try multiple Overpass API mirrors in order
    MIRRORS = [
        'https://overpass-api.de/api/interpreter',
        'https://lz4.overpass-api.de/api/interpreter',
        'https://z.overpass-api.de/api/interpreter',
        'https://overpass.karte.io/api/interpreter',
    ]

    for mirror in MIRRORS:
        try:
            req = urllib.request.Request(
                mirror,
                data=query.encode('utf-8'),
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'BotMedguide/1.0'
                }
            )
            with urllib.request.urlopen(req, timeout=25) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                elements = res_data.get('elements', [])
                # Normalise 'way' elements: they have center lat/lon instead of direct lat/lon
                normalised = []
                for el in elements:
                    if el.get('lat') and el.get('lon'):
                        normalised.append(el)
                    elif el.get('center'):
                        el['lat'] = el['center']['lat']
                        el['lon'] = el['center']['lon']
                        normalised.append(el)
                if normalised:
                    print(f"Overpass success via {mirror}: {len(normalised)} results")
                    return {"elements": normalised}
        except Exception as e:
            print(f"Overpass mirror {mirror} failed: {e}")
            continue

    # ── All mirrors failed — return failure signal, no fake data ──
    print("All Overpass mirrors failed — returning api_failed")
    return {"elements": [], "api_failed": True}

if __name__ == '__main__':
    app.run(debug=True)