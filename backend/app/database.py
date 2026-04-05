"""
Database Initialization Module
Sets up the MongoDB connection and provides access to collections across the app.
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

try:
    # Fail fast after 2 seconds if DB is not available instead of default 30s block
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
    # Trigger a connection attempt to guarantee fail-fast
    client.server_info()
    db = client["edi_platform"]
    users_collection = db["users"]
    sessions_collection = db["sessions"]
    rules_collection = db["rules"]
    print("=> Successfully connected to MongoDB.")
except Exception as e:
    print(f"=> WARNING: Could not connect to MongoDB. API will gracefully downgrade to mocks. ({e})")
    client = None
    db = None
    users_collection = None
    sessions_collection = None
    rules_collection = None
