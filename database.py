import bcrypt
import json
import os
import uuid
import datetime

DB_FILE = "db.json"

def get_hashed_password(plain_text_password):
    return bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt())

def seed_users(db_data):
    # Predefined accounts
    accounts = [
        {"email": "officer_water@gmail.com", "name": "Water Officer", "role": "officer", "dept": "Water", "password": "officer123"},
        {"email": "officer_road@gmail.com", "name": "Road Officer", "role": "officer", "dept": "Roads", "password": "officer123"},
        {"email": "officer_sanitation@gmail.com", "name": "Sanitation Officer", "role": "officer", "dept": "Sanitation", "password": "officer123"},
        {"email": "officer_electricity@gmail.com", "name": "Electricity Officer", "role": "officer", "dept": "Electricity", "password": "officer123"},
        {"email": "officer_other@gmail.com", "name": "General Officer", "role": "officer", "dept": "General", "password": "officer123"},
        {"email": "admin@gmail.com", "name": "System Admin", "role": "admin", "password": "admin123"}
    ]
    
    existing_emails = [u['email'] for u in db_data['users']]
    
    for acc in accounts:
        if acc['email'] not in existing_emails:
            acc['_id'] = str(uuid.uuid4())
            acc['password'] = get_hashed_password(acc['password'])
            db_data['users'].append(acc)
            print(f"Seeded user: {acc['email']}")

class JSONDatabase:
    def __init__(self):
        if not os.path.exists(DB_FILE):
            self.data = {
                "users": [],
                "complaints": [],
                "notifications": [],
                "departments": [
                    {"name": "Electricity", "head": "Elec Dept Head"},
                    {"name": "Water", "head": "Water Dept Head"},
                    {"name": "Roads", "head": "Roads Dept Head"},
                    {"name": "Sanitation", "head": "Sanitation Dept Head"}
                ]
            }
        else:
            with open(DB_FILE, 'r') as f:
                self.data = json.load(f)
        
        # Always run seed check
        seed_users(self.data)
        self.save()

    def save(self):
        # Create a copy to avoid mutating the original data during serialization
        def serialize(obj):
            if isinstance(obj, bytes):
                return obj.decode('utf-8')
            return str(obj)

        with open(DB_FILE, 'w') as f:
            json.dump(self.data, f, indent=4, default=serialize)

    def __getattr__(self, name):
        class Collection:
            def __init__(self, data, parent):
                self.data = data
                self.parent = parent
            def find_one(self, query):
                for item in self.data:
                    if all(item.get(k) == v for k, v in query.items()):
                        # Ensure password is bytes for bcrypt
                        if 'password' in item and isinstance(item['password'], str):
                            item['password'] = item['password'].encode('utf-8')
                        return item
                return None
            def insert_one(self, item):
                if '_id' not in item:
                    item['_id'] = str(uuid.uuid4())
                self.data.append(item)
                self.parent.save()
                class Res:
                    def __init__(self, id): self.inserted_id = id
                return Res(item['_id'])
            def find(self, query=None):
                if not query: return self.data
                res = [item for item in self.data if all(item.get(k) == v for k, v in query.items())]
                class Cursor:
                    def __init__(self, items): self.items = items
                    def sort(self, field, dir): return self.items
                    def __iter__(self): return iter(self.items)
                return Cursor(res)
            def count_documents(self, query):
                return len([item for item in self.data if all(item.get(k) == v for k, v in query.items())])
            def update_one(self, query, update):
                item = self.find_one(query)
                if item:
                    if "$set" in update:
                        item.update(update["$set"])
                    else:
                        item.update(update)
                    self.parent.save()
            def aggregate(self, pipeline):
                from collections import Counter
                counts = Counter(item.get('category') for item in self.data)
                return [{"_id": k, "count": v} for k, v in counts.items()]

        return Collection(self.data.get(name, []), self)

db_instance = JSONDatabase()

def get_db():
    return db_instance

def init_db():
    print("Database seeded and ready.")

if __name__ == "__main__":
    init_db()
