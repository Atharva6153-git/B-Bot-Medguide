# 🏥 B Bot Medguide

> **Your AI-Powered Medical Companion** — Trusted and Prescribed by Specialist Doctors

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-black?style=for-the-badge&logo=flask)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green?style=for-the-badge&logo=mongodb)
![Groq](https://img.shields.io/badge/Groq-AI-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

---

## 📖 About The Project

**B Bot Medguide** is a full-stack AI-powered medical web application designed to help users who are stuck in an unknown place and suddenly fall ill. The app provides temporary medicine suggestions, AI-powered symptom analysis, skin infection detection via image upload, nearby hospital locator, and a complete patient history management system.

This project was developed as a **college mini project** with a focus on backend development, database management, and AI integration.

---

## ✨ Features

### 🔐 User Authentication
- Secure **signup and login** system
- Password hashing using **Flask-Bcrypt**
- Session-based authentication
- Patient profile with name, age, and blood group

### 💊 Medicine Guide
- Select illness and age group to get medicine recommendations
- Color-coded medicine cards (painkillers, antibiotics, vitamins, others)
- Covers: Cold, Infection, Vitamin Deficiency, Headache, Allergy
- Doctor consultation warning on every prescription

### 🤖 AI Medical Chatbot
- Powered by **Groq AI (Llama 3.3 70B)**
- User describes symptoms → AI suggests medicines
- Age-based medicine recommendations
- Dosage instructions included
- Doctor consultation warning

### 🖼️ Skin Infection AI Analyzer
- Upload a photo of skin infection
- **Groq Vision AI (Llama 4 Scout)** analyzes the image
- Identifies infection type and causes
- Suggests medicines and skincare tips
- Warning to consult a dermatologist

### 📊 Fever Ratio Tool
- Enter symptoms to get fever probability analysis
- Shows probability chart for:
  - Viral Fever (55%)
  - Dengue (20%)
  - Malaria (15%)
  - Typhoid (7%)
  - COVID-19 (3%)
- Warning signs table included

### 🏥 Nearby Hospitals
- Uses browser **Geolocation API**
- Powered by **OpenStreetMap + Overpass API**
- Shows hospitals on interactive map
- Lists hospital name, address, phone, distance
- Get directions link for each hospital
- Emergency numbers: 108 (Ambulance), 102 (Medical Helpline)

### 📋 Patient History
- Add and store medical records
- Upload files (PDF, Images, Documents)
- View all past medical records
- Timestamp for each record
- Stored securely in MongoDB Atlas

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript |
| **Backend** | Python, Flask |
| **Database** | MongoDB Atlas (Cloud) |
| **AI Chatbot** | Groq API — Llama 3.3 70B |
| **AI Vision** | Groq API — Llama 4 Scout 17B |
| **Maps** | OpenStreetMap + Leaflet.js + Overpass API |
| **Authentication** | Flask Session + Flask-Bcrypt |
| **File Upload** | Werkzeug |
| **Fonts** | Google Fonts (Poppins) |

---

## 📁 Project Structure

```
B Bot Medguide/
├── app.py                  # Main Flask application
├── templates/
│   ├── index.html          # Home - Medicine Guide
│   ├── login.html          # Login page
│   ├── signup.html         # Signup page
│   ├── history.html        # Patient history page
│   ├── chatbot.html        # AI Chatbot page
│   ├── skin.html           # Skin infection analyzer
│   ├── fever_ratio.html    # Fever ratio tool
│   └── hospitals.html      # Nearby hospitals
├── static/
│   └── css/
│       └── style.css       # Global stylesheet
├── uploads/                # Uploaded files storage
└── README.md               # Project documentation
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10+
- MongoDB Atlas account
- Groq API key (free at https://console.groq.com)

### Step 1 — Clone the project
```bash
git clone https://github.com/yourusername/b-bot-medguide.git
cd b-bot-medguide
```

### Step 2 — Install dependencies
```bash
pip install flask pymongo flask-bcrypt werkzeug groq dnspython python-dotenv certifi
```

### Step 3 — Configure Environment Variables
Create a `.env` file in the root directory of the project and add your API keys:
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/medguide
GROQ_API_KEY=YOUR_GROQ_API_KEY
SECRET_KEY=your_secret_key_here
```

### Step 4 — Configure Git (Important for Security)
Create a `.gitignore` file in the root directory and add the following line to ensure your `.env` file containing API keys is not uploaded to GitHub:
```text
.env
```

### Step 5 — Run the app
```bash
python app.py
```

### Step 6 — Open in browser
```
http://127.0.0.1:5000
```

---

## 🔑 API Keys Required

| API | Purpose | Get It From |
|---|---|---|
| **Groq API** | AI Chatbot + Skin Analysis | https://console.groq.com |
| **MongoDB Atlas** | Database | https://cloud.mongodb.com |

---

## 📦 Dependencies

```
flask
pymongo
flask-bcrypt
werkzeug
groq
dnspython
python-dotenv
certifi
```

---

## 🗄️ Database Schema

### Users Collection
```json
{
  "_id": "ObjectId",
  "username": "string",
  "email": "string",
  "password": "hashed string",
  "age": "string",
  "blood_group": "string",
  "created_at": "datetime"
}
```

### Patient History Collection
```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "username": "string",
  "medical_condition": "string",
  "notes": "string",
  "file": "filename string",
  "timestamp": "datetime"
}
```

---

## 🚀 AI Models Used

| Model | Provider | Purpose |
|---|---|---|
| `llama-3.3-70b-versatile` | Groq | Medical chatbot — symptom analysis |
| `meta-llama/llama-4-scout-17b-16e-instruct` | Groq | Skin infection image analysis |

---

## ⚠️ Disclaimer

> This application is for **educational purposes only**. The medicine suggestions and AI analysis provided are **not a substitute for professional medical advice**. Always consult a qualified doctor for proper diagnosis and treatment.

---

## 👨‍💻 Developed By

**Atharva J** — Backend Developer

- College Mini Project
- Role: Backend Development + Database + AI Integration

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgements

- [Groq](https://groq.com) — for free AI API
- [MongoDB Atlas](https://www.mongodb.com/atlas) — for free cloud database
- [OpenStreetMap](https://www.openstreetmap.org) — for free maps
- [Leaflet.js](https://leafletjs.com) — for interactive maps
- [Flask](https://flask.palletsprojects.com) — for the web framework
