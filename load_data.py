import json
from pymongo import MongoClient

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["airbnb_project"]
collection = db["listings"]

# Load JSON data
with open(r"C:\Anvitha\GUVI\Airbnb\sample_airbnb.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Insert into collection
# Insert into MongoDB
collection.delete_many({})  # clear old data
if isinstance(data, list):
    collection.insert_many(data)
    print(f"Inserted {len(data)} documents")
else:
    result = collection.insert_one(data)
    print("Inserted 1 document with _id", result.inserted_id)
