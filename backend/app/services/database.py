from pymongo import MongoClient
from app.core.config import settings
from datetime import datetime
import logging

class DatabaseService:
    def __init__(self):
        self.client = None
        self.db = None
        if settings.MONGODB_URL:
            try:
                self.client = MongoClient(settings.MONGODB_URL)
                self.db = self.client.get_database() # Uses db name from URI
                logging.info("Connected to MongoDB successfully.")
            except Exception as e:
                logging.error(f"Could not connect to MongoDB: {e}")

    def save_analysis(self, profile_data: dict, result_data: dict):
        if self.db is None:
            return
            
        try:
            document = {
                "timestamp": datetime.utcnow(),
                "profile": profile_data,
                "analysis_result": result_data
            }
            self.db.analyses.insert_one(document)
        except Exception as e:
            logging.error(f"Failed to save to MongoDB: {e}")

db_service = DatabaseService()
