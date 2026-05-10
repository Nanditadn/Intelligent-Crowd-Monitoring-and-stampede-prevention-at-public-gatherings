# database.py
# MongoDB connection for your project

from pymongo import MongoClient

client = MongoClient(
    "mongodb://localhost:27017/",
    serverSelectionTimeoutMS=5000
)

db = client["crowd_hybrid"]

alerts = db["alerts"]