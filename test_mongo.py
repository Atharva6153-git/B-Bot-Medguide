from pymongo import MongoClient

# Replace with your actual connection string
connection_string = "mongodb://username:password@cluster0.xxxxx.mongodb.net/"

try:
    client = MongoClient(connection_string)
    db = client['medguide']
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
