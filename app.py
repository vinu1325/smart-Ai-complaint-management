from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import get_db, init_db
from nlp_utils import classify_complaint, detect_duplicate
import datetime
import bcrypt
import jwt
import os
from bson import ObjectId

app = Flask(__name__, static_folder='static')
CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_super_secret_key_vinu')
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print("Connecting to MongoDB...")
db = get_db()
print("Initializing database...")
try:
    init_db() # Ensure DB is seeded on start
    print("Database initialization complete.")
except Exception as e:
    print(f"Database initialization failed: {e}")

# --- Utils ---
def create_notification(user_id, title, message, role=None, dept=None):
    notif = {
        "user_id": str(user_id) if user_id else None,
        "role": role,
        "dept": dept,
        "title": title,
        "message": message,
        "read": False,
        "created_at": datetime.datetime.now()
    }
    db.notifications.insert_one(notif)

# --- Auth Middleware ---
def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db.users.find_one({"_id": ObjectId(data['id'])})
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# --- Routes ---

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if db.users.find_one({"email": data['email']}):
        return jsonify({"message": "User already exists"}), 400
    
    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    role = data.get('role', 'user')
    dept = data.get('dept', None)
    
    user_id = db.users.insert_one({
        "name": data['name'],
        "phone": data['phone'],
        "email": data['email'],
        "password": hashed_pw,
        "role": role,
        "dept": dept
    }).inserted_id
    
    token = jwt.encode({
        'id': str(user_id),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'])

    return jsonify({
        "message": "User registered",
        "token": token,
        "role": role,
        "name": data['name'],
        "dept": dept
    }), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    print(f"Login attempt for: {data.get('email')}")
    user = db.users.find_one({"email": data['email']})
    if user:
        print("User found, checking password...")
        # Ensure password is bytes for bcrypt
        pw = user['password']
        if isinstance(pw, str):
            pw = pw.encode('utf-8')
            
        if bcrypt.checkpw(data['password'].encode('utf-8'), pw):
            print("Password match!")
            token = jwt.encode({
                'id': str(user['_id']),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'])
            
            if isinstance(token, bytes):
                token = token.decode('utf-8')
                
            return jsonify({
                "token": token,
                "role": user['role'],
                "name": user['name'],
                "dept": user.get('dept'),
                "id": str(user['_id'])
            })
        else:
            print("Password mismatch.")
    else:
        print("User not found.")
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/complaints', methods=['POST'])
@token_required
def create_complaint(current_user):
    # Support multipart/form-data for image upload
    title = request.form.get('title')
    description = request.form.get('description')
    location = request.form.get('location')
    image = request.files.get('image')
    
    # NLP Auto-Classification
    category, priority, deadline = classify_complaint(description)
    
    # Check for duplicates using Cosine Similarity
    existing = list(db.complaints.find({}))
    is_duplicate, original = detect_duplicate(description, existing)
    
    if is_duplicate:
        return jsonify({
            "message": "Potential duplicate detected!",
            "original_id": str(original['_id']),
            "confidence": "High"
        }), 200 # User might still want to submit, or handle it as warning

    filename = None
    if image:
        filename = f"{datetime.datetime.now().timestamp()}_{image.filename}"
        image.save(os.path.join(UPLOAD_FOLDER, filename))

    complaint = {
        "user_id": current_user['_id'],
        "user_name": current_user['name'],
        "user_phone": current_user.get('phone'),
        "title": title,
        "description": description,
        "location": location,
        "category": category,
        "priority": priority,
        "status": "Pending",
        "image_path": filename,
        "created_at": datetime.datetime.now(),
        "deadline": deadline,
        "last_alert_sent": False,
        "viewed_by_officer": False
    }
    
    res = db.complaints.insert_one(complaint)
    
    # Notify User (Confirmation)
    create_notification(current_user['_id'], "Complaint Filed", f"Successfully submitted: {title}")
    
    # Notify Dept Officers
    create_notification(None, "New Dept Complaint", f"New {category} complaint: {title}", role='officer', dept=category)
    
    # Notify Admin (Global)
    create_notification(None, "New System Complaint", f"New complaint filed in {category} by {current_user['name']}", role='admin')
    
    return jsonify({"message": "Complaint filed successfully", "id": str(res.inserted_id)}), 201

@app.route('/complaints/<id>/viewed', methods=['PATCH'])
@token_required
def mark_viewed(current_user, id):
    if current_user['role'] not in ['officer', 'admin']:
        return jsonify({"message": "Unauthorized"}), 403
    
    db.complaints.update_one({"_id": ObjectId(id)}, {"$set": {"viewed_by_officer": True}})
    return jsonify({"message": "Marked as viewed"})

@app.route('/complaints', methods=['GET'])
@token_required
def get_complaints(current_user):
    role = current_user['role']
    query = {}
    if role == 'user':
        query = {"user_id": current_user['_id']}
    elif role == 'officer':
        query = {"category": current_user['dept']}
    # Admin sees all
    
    complaints = list(db.complaints.find(query).sort("created_at", -1))
    for c in complaints:
        c['_id'] = str(c['_id'])
        c['user_id'] = str(c['user_id'])
        # Backward compatibility for phone numbers
        if 'user_phone' not in c:
            user = db.users.find_one({"_id": ObjectId(c['user_id'])})
            c['user_phone'] = user.get('phone', 'N/A') if user else 'N/A'
            
    return jsonify(complaints)

@app.route('/complaints/<id>/status', methods=['PATCH'])
@token_required
def update_status(current_user, id):
    if current_user['role'] not in ['officer', 'admin']:
        return jsonify({"message": "Unauthorized"}), 403
    
    new_status = request.json.get('status')
    db.complaints.update_one({"_id": ObjectId(id)}, {"$set": {"status": new_status, "updated_at": datetime.datetime.now()}})
    
    # Notify User
    comp = db.complaints.find_one({"_id": ObjectId(id)})
    create_notification(comp['user_id'], "Status Updated", f"Your complaint '{comp['title']}' is now {new_status}")
    
    # Notify Admin
    create_notification(None, "Status Changed", f"Complaint '{comp['title']}' updated to {new_status} by {current_user['name']}", role='admin')
    
    return jsonify({"message": "Status updated"})

@app.route('/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    # Fetch notifications strictly relevant to user role/dept
    role = current_user['role']
    notif_query = {"user_id": str(current_user['_id'])} # Personal notifications
    
    if role == 'officer':
        query = {
            "$or": [
                notif_query,
                {"role": "officer", "dept": current_user.get('dept')}
            ]
        }
    elif role == 'admin':
        query = {
            "$or": [
                notif_query,
                {"role": "admin"}
            ]
        }
    else: # Normal user
        query = notif_query
    
    user_n = list(db.notifications.find(query).sort("created_at", -1).limit(10))
    
    for n in user_n: 
        if '_id' in n: n['_id'] = str(n['_id'])
        if 'user_id' in n: n['user_id'] = str(n['user_id'])
    return jsonify(user_n)

@app.route('/notifications/read', methods=['POST'])
@token_required
def mark_read(current_user):
    query = {
        "$or": [
            {"user_id": str(current_user['_id'])},
            {"role": current_user['role'], "dept": current_user.get('dept')}
        ]
    }
    db.notifications.update_many(query, {"$set": {"read": True}})
    return jsonify({"message": "All marked as read"})

@app.route('/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    if current_user['role'] != 'admin':
        return jsonify({"message": "Forbidden"}), 403
    
    all_complaints = list(db.complaints.find({}))
    total = len(all_complaints)
    resolved_list = [c for c in all_complaints if c.get('status') == 'Resolved']
    resolved_count = len(resolved_list)
    pending_count = total - resolved_count
    
    # Category Stats with Resolution Rate
    categories = list(set(c.get('category') for c in all_complaints))
    category_analysis = []
    for cat in categories:
        cat_items = [c for c in all_complaints if c.get('category') == cat]
        cat_resolved = [c for c in cat_items if c.get('status') == 'Resolved']
        
        # Calculate Average Resolution Time (in hours)
        res_times = []
        for c in cat_resolved:
            if 'updated_at' in c and 'created_at' in c:
                c_at = c['created_at']
                u_at = c['updated_at']
                if isinstance(c_at, str): c_at = datetime.datetime.fromisoformat(c_at)
                if isinstance(u_at, str): u_at = datetime.datetime.fromisoformat(u_at)
                diff = (u_at - c_at).total_seconds() / 3600
                res_times.append(diff)
        
        avg_res_time = round(sum(res_times) / len(res_times), 1) if res_times else 0
        
        category_analysis.append({
            "category": cat,
            "count": len(cat_items),
            "resolved": len(cat_resolved),
            "resolution_rate": round((len(cat_resolved) / len(cat_items)) * 100, 1) if cat_items else 0,
            "avg_res_time": avg_res_time
        })

    # Daily Trend (Last 7 days)
    now = datetime.datetime.now()
    trend = []
    for i in range(6, -1, -1):
        day = now - datetime.timedelta(days=i)
        day_str = day.strftime('%Y-%m-%d')
        count = sum(1 for c in all_complaints if (c['created_at'].strftime('%Y-%m-%d') if isinstance(c['created_at'], datetime.datetime) else c['created_at'][:10]) == day_str)
        trend.append({"day": day.strftime('%a'), "count": count})

    # SLA Breach Alert Check
    escalated = [str(c['_id']) for c in all_complaints if c.get('status') != 'Resolved' and (c['deadline'] < now if isinstance(c['deadline'], datetime.datetime) else datetime.datetime.fromisoformat(c['deadline']) < now)]
    
    return jsonify({
        "total": total,
        "pending": pending_count,
        "resolved": resolved_count,
        "category_stats": category_analysis,
        "daily_trend": trend,
        "escalations": escalated
    })

# Serve static files
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
