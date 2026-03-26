from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import sqlite3
import os
import json
import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

# Securely load the SECRET_KEY
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    # Use a fallback key for development, but warn the developer
    print("WARNING: 'SECRET_KEY' not found in environment variables. Using a default fallback key. Do NOT use this in production!")
    app.secret_key = "default_fallback_secret_key"

# Securely load Database URL (with a fallback)
DB_NAME = os.getenv("DATABASE_URL", "database.db")
COLLEGE_DATA_FILE = "college_data.json"

# Load College Data
COLLEGE_INFO = {}
try:
    with open(COLLEGE_DATA_FILE, 'r') as f:
        COLLEGE_INFO = json.load(f)
except Exception as e:
    print(f"Warning: Could not load college data: {e}")

# Database Helper
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    import create_db
    import setup_chat_db
    
    # Ensure the scripts use the same DB connected to the app
    create_db.DB_NAME = DB_NAME
    setup_chat_db.DB_NAME = DB_NAME
    
    conn = get_db_connection()
    try:
        # Check if users table exists
        table_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
        
        if not table_exists:
            print("Database 'users' table not found. Initializing database with default data...")
            # create_db.insert_data() drops and recreates tables, then inserts default data
            create_db.insert_data()
            
            # setup_chat_db ensures chat_messages table is also created
            setup_chat_db.create_chat_table()
            print("Database initialization complete.")
    except Exception as e:
        print(f"Error during database initialization: {e}")
    finally:
        conn.close()

# Automatically initialize the database when the application starts
init_db()

# AI CHATBOT LOGIC (GEN AI UPGRADE)
# --------------------------------------------------------------------------

# Configure Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_API_KEY:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        # Using llama-3.3-70b-versatile as llama3-70b-8192 is decommissioned
        GROQ_MODEL = 'llama-3.3-70b-versatile' 
    except ImportError:
        client = None
        print("Error: 'groq' library not found. Please install it: pip install groq")
else:
    client = None
    print("WARNING: GROQ_API_KEY environment variable not set. Chatbot will fail.")

# Using deep_translator for better compatibility
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False
    print("Warning: deep_translator not found. Translation will be limited.")

def translate_text(text, dest_lang):
    """Translate text to destination language if possible."""
    if not HAS_TRANSLATOR or dest_lang != "ta":
        return text
    try:
        # deep_translator syntax
        return GoogleTranslator(source='auto', target=dest_lang).translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def get_student_data(user_id):
    """Fetch all relevant student data from DB."""
    conn = get_db_connection()
    data = {}
    try:
        # Fetch data as sqlite3.Row objects (behaves like dict)
        data['academics'] = conn.execute("SELECT * FROM academics WHERE user_id = ?", (user_id,)).fetchone()
        data['attendance'] = conn.execute("SELECT * FROM attendance WHERE user_id = ?", (user_id,)).fetchone()
        data['fees'] = conn.execute("SELECT * FROM fees WHERE user_id = ?", (user_id,)).fetchone()
        data['exams'] = conn.execute("SELECT * FROM exams WHERE user_id = ?", (user_id,)).fetchone()
        data['library'] = conn.execute("SELECT * FROM library WHERE user_id = ?", (user_id,)).fetchone()
    except Exception as e:
        print(f"DB Error fetching student data: {e}")
    finally:
        conn.close()
    return data

def get_chat_history(user_id, limit=6):
    """Fetch last N messages for context."""
    conn = get_db_connection()
    try:
        # Retrieve last N messages; subquery orders by time DESC to get latest, then outer query orders ASC for prompt
        rows = conn.execute("""
            SELECT role, message FROM (
                SELECT role, message, timestamp FROM chat_messages 
                WHERE user_id = ? 
                ORDER BY timestamp DESC LIMIT ?
            ) ORDER BY timestamp ASC
        """, (user_id, limit)).fetchall()
        return rows
    except Exception as e:
        print(f"History Error: {e}")
        return []
    finally:
        conn.close()

def save_chat_message(user_id, role, message):
    """Save a single message to SQLite."""
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO chat_messages (user_id, role, message) VALUES (?, ?, ?)", 
                     (user_id, role, message))
        conn.commit()
    except Exception as e:
        print(f"Save Msg Error: {e}")
    finally:
        conn.close()

def get_student_timetable(course, day_of_week):
    """Fetch timetable for the given course and day."""
    conn = get_db_connection()
    try:
        # day_of_week is like 'Monday', 'Tuesday'
        # The table has 'day_of_week' column
        row = conn.execute("SELECT * FROM timetables WHERE course = ? AND day_of_week = ?", 
                           (course, day_of_week)).fetchone()
        if row:
            return f"Period Order: 1:{row['p1']}, 2:{row['p2']}, 3:{row['p3']}, 4:{row['p4']}, 5:{row['p5']}, 6:{row['p6']}, 7:{row['p7']}, 8:{row['p8']}"
        return "No timetable found for today (e.g., Weekend or Holiday)."
    except Exception as e:
        print(f"Timetable Error: {e}")
        return "Error fetching timetable."
    finally:
        conn.close()

def get_library_stats():
    """Fetch total books and total available."""
    conn = get_db_connection()
    try:
        stats = conn.execute("SELECT COUNT(*) as titles, SUM(total_copies) as total_books, SUM(available_copies) as available FROM library_books").fetchone()
        return stats
    except Exception as e:
        print(f"Library Stats Error: {e}")
        return None
    finally:
        conn.close()

def search_library_books(query):
    """Search for books by title or author."""
    conn = get_db_connection()
    try:
        if not query:
            books = conn.execute("SELECT * FROM library_books").fetchall()
        else:
            # Simple LIKE search
            books = conn.execute("SELECT * FROM library_books WHERE title LIKE ? OR author LIKE ?", 
                                 (f"%{query}%", f"%{query}%")).fetchall()
        return books
    except Exception as e:
        print(f"Library Search Error: {e}")
        return []
    finally:
        conn.close()

def build_erp_context(data, timetable_text=None):
    """Format stored DB rows into a readable string for the LLM."""
    if not data: return "Student data not available."
    
    ctx = []
    
    # Timetable
    if timetable_text:
        ctx.append(f"TODAY'S TIMETABLE: {timetable_text}")

    # Academics
    aca = data.get('academics')
    if aca:
        ctx.append(f"Academics: GPA {aca['gpa']}, Subjects: {aca['subjects']}")
    
    # Attendance
    att = data.get('attendance')
    if att:
        ctx.append(f"Attendance: {att['percentage']}% ({att['attended_classes']}/{att['total_classes']} classes attended)")
        
    # Fees
    fee = data.get('fees')
    if fee:
        ctx.append(f"Fees: Total ₹{fee['total_fee']}, Paid ₹{fee['paid']}, Due ₹{fee['due']}")
        
    # Exams
    exam = data.get('exams')
    if exam:
        ctx.append(f"Last Exam: {exam['exam_name']}, Score: {exam['score']}, Result: {exam['result']}")
        
    # Library
    lib = data.get('library')
    if lib:
        ctx.append(f"Library: Books Issued: {lib['books_issued']}, Fine: ₹{lib['fine']}")
        
    return "\n".join(ctx)

@app.route("/chat", methods=["POST"])
def chat():
    # 1. Auth Check
    if "user_id" not in session:
        return jsonify({"reply": "Please log in to chat."}), 401

    user_id = session["user_id"]
    req = request.json
    user_msg = req.get("message", "").strip()
    lang = req.get("lang", "en")
    
    if not user_msg:
        return jsonify({"reply": "Empty message."})

    # 2. Check API Key
    if not client:
        return jsonify({"reply": "System Error: AI Service not configured. Please check GROQ_API_KEY."})

    # 3. Fetch Data & Identity
    student_data = None
    target_student_name = None
    
    # Get Current Day for Timetable
    # Note: Server Local Time
    try:
        current_day = datetime.datetime.now().strftime("%A") 
    except:
        current_day = "Unknown"

    # --- ADMIN SUPERPOWER START ---
    if session.get("role") == "admin":
        student_name = "Admin"
        
        # Check if Admin specifically asked about a roll number (simple heuristic)
        # Scan words in message to find something that looks like a Roll No (e.g. 101, 102, 2023001)
        conn = get_db_connection()
        possible_rolls = [word for word in user_msg.split() if word.isdigit() or (word.isalnum() and any(c.isdigit() for c in word))]
        
        found_target = False
        target_course = None
        
        for roll in possible_rolls:
            # Try to find student by roll
            user = conn.execute("SELECT * FROM users WHERE roll_no = ?", (roll,)).fetchone()
            if user:
                target_user_id = user["id"]
                target_student_name = user["username"]
                student_data = get_student_data(target_user_id)
                target_course = user["course"]
                found_target = True
                break
        
        timetable_text = None
        if found_target and target_course:
             timetable_text = get_student_timetable(target_course, current_day)
        
        conn.close()

    else:
        # Regular Student Mode
        student_name = session.get("username", "Student")
        student_data = get_student_data(user_id)
        
        # Fetch Timetable
        student_course = session.get("course")
        timetable_text = get_student_timetable(student_course, current_day)

    # Build Context
    erp_context = build_erp_context(student_data, timetable_text)
    
    # 3.5 ADD GENERAL COLLEGE CONTEXT
    general_context = json.dumps(COLLEGE_INFO, indent=2)

    # 3.6 ADD LIBRARY CONTEXT (New feature)
    lib_stats = get_library_stats()
    lib_context_str = ""
    if lib_stats:
        lib_context_str = f"LIBRARY STATUS: Total Titles: {lib_stats['titles']}, Total Volumes: {lib_stats['total_books']}, Currently Available: {lib_stats['available']}."

    # Check for book queries
    user_msg_lower = user_msg.lower()
    if "book" in user_msg_lower or "library" in user_msg_lower or "author" in user_msg_lower or "available" in user_msg_lower:
        # Extract potential book name (naive approach: assume the whole message or parts are relevant)
        # We'll just search using the user message content to be safe, filtering out common words if needed, 
        # but for now let's try searching the message against the DB.
        # Better: Search if the message seems to be asking about a specific thing.
        # Actually, let's just pass the whole message as a search query if it's not too long, 
        # or rely on the LLM to ask for a specific name if we want to be fancy.
        # But the prompt asked for "if student asks (book name) is it currently available".
        # Let's try to search the whole message as a keyword? Or key words?
        # Let's search for keywords from the message that match book titles.
        
        # Search for any books that match keywords in the user message
        relevant_books = search_library_books(user_msg) 
        # The above might be too strict if user_msg is "Is Harry Potter available?". 
        # 'Harry Potter' matches, but the full string might not if using LIKE %msg%.
        # Let's try searching for specific keywords.
        
        # Fallback: Search for all books and let LLM pick? No, too many.
        # Let's just fetch ALL titles and check strict containment in Python?
        # Or better, just inject stats first, and if user names a book, we might need a 2-step or a broad search.
        # Let's try a broader search strategy:
        # Search for *parts* of the string? 
        # Let's just getAllLibraryBooks() if the list is small (it is sample data).
        # Real world: Vector search.
        # Here: Fetch all books and filter in Python to construct context?
        
        all_books = search_library_books("") # Empty query returns all via LIKE %%? No logic above needs fix for empty.
        # Fix logic in search_library_books to handle empty query or just query everything.
        
        # Let's refine search_library_books to return everything if query is generic, or specific matches.
        # ACTUALLY, for this size, let's just inject the WHOLE library inventory if the user asks about library. It's only 10 books.
        pass
    
    # Let's just fetch all books for now since the dataset is small (10 items).
    all_books_rows = search_library_books("") # Will need to fix the LIKE %% logic if it fails or just use empty string
    # Actually LIKE '%%' works for everything.
    
    library_inventory_text = "LIBRARY INVENTORY:\n"
    for b in all_books_rows:
        library_inventory_text += f"- '{b['title']}' by {b['author']} (Available: {b['available_copies']}/{b['total_copies']})\n"
        
    # Only append if relevant to save tokens? Or just always append for "smartness"?
    # The user specifically verified "know about library".
    general_context += "\n\n" + lib_context_str + "\n" + library_inventory_text

    # 4. Fetch History
    history_rows = get_chat_history(user_id)
    history_text = "\n".join([f"{row['role'].upper()}: {row['message']}" for row in history_rows])

    # 5. Construct Prompt
    # Structure: System -> Context -> History -> User Input
    # Groq uses 'messages' list with roles
    
    messages = [
        {
            "role": "system",
            "content": f"""You are the Smart Campus Assistant for Unreal University ERP.
Your goal is to be helpful, concise, and accurate.

ROLES & CAPABILITIES:
- You are talking to: {student_name}
- If the user is ADMIN: You can answer questions about ANY student if their data is provided below.
- If the user is STUDENT: You only know about their own data.
- Today is: {current_day}

KNOWLEDGE BASE (GENERAL COLLEGE INFO):
Use this for questions about timings, bus routes, holidays, placements, etc.
{general_context}

SPECIFIC STUDENT CONTEXT (ERP DATA):
(If 'None', it means no specific student was targeted or found).
Target Student: {target_student_name if target_student_name else 'N/A'}
Data:
{erp_context}

INSTRUCTIONS:
1. Always check the GENERAL KNOWLEDGE first for generic questions.
2. Check STUDENT CONTEXT for grades, fees, attendance, and TODAY'S TIMETABLE.
3. If asking for "period order", "timetable", or "schedule", explicitly list the periods from the 'TODAY'S TIMETABLE' section.
4. If a user asks about "functions" or "events", they mean college events or celebrations. Refer to the 'functions_and_events' section in GENERAL KNOWLEDGE.
5. If data is missing (e.g. 'None'), say you don't have that info.
6. Do not hallucinate numbers. Be friendly."""
        }
    ]
    
    # Add history
    for row in history_rows:
        role = "assistant" if row['role'] == "assistant" else "user"
        messages.append({"role": role, "content": row['message']})
        
    # Add current user message
    messages.append({"role": "user", "content": user_msg})

    reply_text = "Sorry, I couldn't process that."
    
    try:
        # 6. Generate Response
        response = client.chat.completions.create(
            messages=messages,
            model=GROQ_MODEL,
        )
        reply_text = response.choices[0].message.content.strip()
    except Exception as e:
        error_msg = str(e)
        print(f"LLM Error: {error_msg}")
        if "429" in error_msg:
             reply_text = "I'm currently overloaded (Quota Exceeded). Please wait a minute and try again."
        else:
             reply_text = "I'm currently having trouble connecting to my brain. Please try again later."
    
    # 7. Save to DB (Memory)
    save_chat_message(user_id, "user", user_msg)
    save_chat_message(user_id, "assistant", reply_text)

    # 8. Translation (Optional)
    final_reply = reply_text
    if lang == "ta":
        final_reply = translate_text(reply_text, "ta")

    # 9. Return (Frontend expects 'reply' and optionally 'chat' list, 
    # but we are now using DB for history, so frontend 'chat' list in session is deprecated but 
    # we can send back empty or just the reply. The prompt said 'Previous frontend... sends POST /chat... returns JSON {reply: ...}')
    return jsonify({"reply": final_reply})


# --------------------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------------------

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    username = request.form["username"]
    password = request.form["password"]
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    conn.close()
    
    if user:
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["roll_no"] = user["roll_no"]
        session["course"] = user["course"]
        session["year"] = user["year"]
        
        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("student_home"))
    else:
        return render_template("login.html", error="Invalid Credentials")

@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    student_data = None
    search_error = None
    
    roll_no = request.form.get("roll_no") or request.args.get("roll_no")

    if roll_no:
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE roll_no = ?", (roll_no,)).fetchone()
        
        if user:
            user_id = user["id"]
            academics = conn.execute("SELECT * FROM academics WHERE user_id = ?", (user_id,)).fetchone()
            attendance = conn.execute("SELECT * FROM attendance WHERE user_id = ?", (user_id,)).fetchone()
            fees = conn.execute("SELECT * FROM fees WHERE user_id = ?", (user_id,)).fetchone()
            exams = conn.execute("SELECT * FROM exams WHERE user_id = ?", (user_id,)).fetchone()
            library = conn.execute("SELECT * FROM library WHERE user_id = ?", (user_id,)).fetchone()
            
            student_data = {
                "user": user,
                "academics": academics,
                "attendance": attendance,
                "fees": fees,
                "exams": exams,
                "library": library
            }
        else:
            search_error = "Student with Roll No " + roll_no + " not found."
            
        conn.close()

    return render_template("admin_dashboard.html", user=session, student_data=student_data, search_error=search_error, search_roll=roll_no)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/student")
def student_home():
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    user_id = session["user_id"]
    conn = get_db_connection()
    
    academics = conn.execute("SELECT * FROM academics WHERE user_id = ?", (user_id,)).fetchone()
    attendance = conn.execute("SELECT * FROM attendance WHERE user_id = ?", (user_id,)).fetchone()
    fees = conn.execute("SELECT * FROM fees WHERE user_id = ?", (user_id,)).fetchone()
    exams = conn.execute("SELECT * FROM exams WHERE user_id = ?", (user_id,)).fetchone()
    
    conn.close()
    
    return render_template("student_home.html", 
                           academics=academics, 
                           attendance=attendance, 
                           fees=fees, 
                           exams=exams,
                           user=session)

@app.route("/academics")
def academics():
    if "user_id" not in session: return redirect(url_for("login"))
    conn = get_db_connection()
    data = conn.execute("SELECT * FROM academics WHERE user_id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("academics.html", data=data)

@app.route("/attendance")
def attendance():
    if "user_id" not in session: return redirect(url_for("login"))
    conn = get_db_connection()
    data = conn.execute("SELECT * FROM attendance WHERE user_id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("attendance.html", data=data)

@app.route("/fees")
def fees():
    if "user_id" not in session: return redirect(url_for("login"))
    conn = get_db_connection()
    data = conn.execute("SELECT * FROM fees WHERE user_id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("fees.html", data=data)

@app.route("/exams")
def exams():
    if "user_id" not in session: return redirect(url_for("login"))
    conn = get_db_connection()
    data = conn.execute("SELECT * FROM exams WHERE user_id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("exams.html", data=data)

@app.route("/library")
def library():
    if "user_id" not in session: return redirect(url_for("login"))
    conn = get_db_connection()
    data = conn.execute("SELECT * FROM library WHERE user_id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("library.html", data=data)

# --------------------------------------------------------------------------
# ADMIN CRUD ROUTES
# --------------------------------------------------------------------------

@app.route("/admin/students")
def admin_students():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM users WHERE role = 'student'").fetchall()
    conn.close()
    
    return render_template("admin_students.html", students=students)

@app.route("/admin/add_student", methods=["POST"])
def add_student():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    username = data.get("roll_no") # Default username to roll_no
    password = f"pass_{data.get('roll_no')}"
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role, roll_no, course, year) VALUES (?, ?, ?, ?, ?, ?)",
                       (username, password, "student", data.get("roll_no"), data.get("course"), data.get("year")))
        user_id = cursor.lastrowid
        
        # Initialize other tables with defaults
        cursor.execute("INSERT INTO academics (user_id, gpa, subjects) VALUES (?, ?, ?)", (user_id, 0.0, "Math, Science"))
        cursor.execute("INSERT INTO attendance (user_id, total_classes, attended_classes, percentage) VALUES (?, ?, ?, ?)", (user_id, 0, 0, 0.0))
        cursor.execute("INSERT INTO fees (user_id, total_fee, paid, due) VALUES (?, ?, ?, ?)", (user_id, 50000, 0, 50000))
        cursor.execute("INSERT INTO library (user_id, books_issued, fine) VALUES (?, ?, ?)", (user_id, "None", 0))
        cursor.execute("INSERT INTO exams (user_id, exam_name, score, result) VALUES (?, ?, ?, ?)", (user_id, "N/A", 0, "N/A"))

        conn.commit()
        return jsonify({"message": "Student added successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/admin/update_student", methods=["POST"])
def update_student():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    user_id = data.get("user_id")
    
    conn = get_db_connection()
    try:
        conn.execute("UPDATE users SET roll_no = ?, course = ?, year = ? WHERE id = ?",
                     (data.get("roll_no"), data.get("course"), data.get("year"), user_id))
        conn.commit()
        return jsonify({"message": "Student updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/admin/update_academics", methods=["POST"])
def update_academics():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    user_id = data.get("user_id")
    
    conn = get_db_connection()
    try:
        conn.execute("UPDATE academics SET gpa = ?, subjects = ? WHERE user_id = ?",
                     (data.get("gpa"), data.get("subjects"), user_id))
        conn.commit()
        return jsonify({"message": "Academics updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/admin/update_attendance", methods=["POST"])
def update_attendance():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    user_id = data.get("user_id")
    
    conn = get_db_connection()
    try:
        conn.execute("UPDATE attendance SET total_classes = ?, attended_classes = ?, percentage = ? WHERE user_id = ?",
                     (data.get("total_classes"), data.get("attended_classes"), data.get("percentage"), user_id))
        conn.commit()
        return jsonify({"message": "Attendance updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/admin/update_fees", methods=["POST"])
def update_fees():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    user_id = data.get("user_id")
    
    conn = get_db_connection()
    try:
        conn.execute("UPDATE fees SET total_fee = ?, paid = ?, due = ? WHERE user_id = ?",
                     (data.get("total_fee"), data.get("paid"), data.get("due"), user_id))
        conn.commit()
        return jsonify({"message": "Fees updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/admin/update_exams", methods=["POST"])
def update_exams():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    user_id = data.get("user_id")
    
    conn = get_db_connection()
    try:
        conn.execute("UPDATE exams SET exam_name = ?, score = ?, result = ? WHERE user_id = ?",
                     (data.get("exam_name"), data.get("score"), data.get("result"), user_id))
        conn.commit()
        return jsonify({"message": "Exam details updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/admin/update_library", methods=["POST"])
def update_library():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    user_id = data.get("user_id")
    
    conn = get_db_connection()
    try:
        conn.execute("UPDATE library SET books_issued = ?, fine = ? WHERE user_id = ?",
                     (data.get("books_issued"), data.get("fine"), user_id))
        conn.commit()
        return jsonify({"message": "Library details updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/admin/delete_student/<int:user_id>", methods=["POST"])
def delete_student(user_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.execute("DELETE FROM academics WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM attendance WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM fees WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM exams WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM library WHERE user_id = ?", (user_id,))
        conn.commit()
        return jsonify({"message": "Student deleted successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(debug=True, port=5000)


