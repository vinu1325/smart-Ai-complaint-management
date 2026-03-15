import bcrypt
import os
import datetime
from pymongo import MongoClient

# MongoDB Connection Details
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://vinuprasaath:STRZVSycY8wHpMdv@vinuprojectdb.j0l81cu.mongodb.net/?appName=vinuprojectDB")
DB_NAME = "smart_complaint_db"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def get_hashed_password(plain_text_password):
    return bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt())

def seed_users():
    # Predefined accounts
    accounts = [
        {"email": "officer_water@gmail.com", "name": "Water Officer", "role": "officer", "dept": "Water", "password": "officer123"},
        {"email": "officer_road@gmail.com", "name": "Road Officer", "role": "officer", "dept": "Roads", "password": "officer123"},
        {"email": "officer_sanitation@gmail.com", "name": "Sanitation Officer", "role": "officer", "dept": "Sanitation", "password": "officer123"},
        {"email": "officer_electricity@gmail.com", "name": "Electricity Officer", "role": "officer", "dept": "Electricity", "password": "officer123"},
        {"email": "officer_other@gmail.com", "name": "General Officer", "role": "officer", "dept": "General", "password": "officer123"},
        {"email": "admin@gmail.com", "name": "System Admin", "role": "admin", "password": "admin123"}
    ]
    
    for acc in accounts:
        if not db.users.find_one({"email": acc['email']}):
            acc['password'] = get_hashed_password(acc['password'])
            db.users.insert_one(acc)
            print(f"Seeded user: {acc['email']}")

def init_db():
    # Seed Departments if empty
    if db.departments.count_documents({}) == 0:
        departments = [
            {"name": "Electricity", "head": "Elec Dept Head"},
            {"name": "Water", "head": "Water Dept Head"},
            {"name": "Roads", "head": "Roads Dept Head"},
            {"name": "Sanitation", "head": "Sanitation Dept Head"}
        ]
        db.departments.insert_many(departments)
        print("Departments seeded.")
    
    seed_users()
    print("Database seeded and ready.")

def get_db():
    return db

if __name__ == "__main__":
    init_db()
