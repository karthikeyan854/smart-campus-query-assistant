import sqlite3
import random

DB_NAME = "database.db"

def create_connection():
    return sqlite3.connect(DB_NAME)

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        roll_no TEXT,
        course TEXT,
        year TEXT
    )''')

    # 2. Academics Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS academics (
        user_id INTEGER,
        gpa REAL,
        subjects TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # 3. Attendance Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
        user_id INTEGER,
        total_classes INTEGER,
        attended_classes INTEGER,
        percentage REAL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # 4. Exams Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS exams (
        user_id INTEGER,
        exam_name TEXT,
        score INTEGER,
        result TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # 5. Fees Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS fees (
        user_id INTEGER,
        total_fee INTEGER,
        paid INTEGER,
        due INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # 6. Library Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS library (
        user_id INTEGER,
        books_issued TEXT,
        fine INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # 7. FAQ Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT
    )''')

    # 8. Timetables Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS timetables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course TEXT,
        day_of_week TEXT,
        p1 TEXT,
        p2 TEXT,
        p3 TEXT,
        p4 TEXT,
        p5 TEXT,
        p6 TEXT,
        p7 TEXT,
        p8 TEXT
    )''')

    conn.commit()
    conn.close()
    print("Tables created successfully.")

def insert_data():
    conn = create_connection()
    cursor = conn.cursor()

    # Drop existing tables to ensure clean state
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS academics")
    cursor.execute("DROP TABLE IF EXISTS attendance")
    cursor.execute("DROP TABLE IF EXISTS exams")
    cursor.execute("DROP TABLE IF EXISTS fees")
    cursor.execute("DROP TABLE IF EXISTS library")
    cursor.execute("DROP TABLE IF EXISTS faq")
    cursor.execute("DROP TABLE IF EXISTS timetables")
    print("Existing tables dropped.")

    create_tables() # Re-create tables

    # User: Admin
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                   ("admin", "admin123", "admin"))

    # Users: 10 Students
    courses = ["BCA", "B.Tech", "B.Sc"]
    years = ["Year 1", "Year 2", "Year 3"]

    print("Generating students...")
    for i in range(1, 11):
        # NEW LOGIC: Username is Roll No, Password is based on Roll No
        roll_no = f"2024{i:03d}"  # e.g., 2024001
        username = roll_no
        password = f"pass_{roll_no}" # e.g., pass_2024001
        
        role = "student"
        course = random.choice(courses)
        year = random.choice(years)
        
        cursor.execute("INSERT INTO users (username, password, role, roll_no, course, year) VALUES (?, ?, ?, ?, ?, ?)", 
                       (username, password, role, roll_no, course, year))
        
        user_id = cursor.lastrowid
        
        # Academics
        gpa = round(random.uniform(6.0, 9.5), 2)
        cursor.execute("INSERT INTO academics (user_id, gpa, subjects) VALUES (?, ?, ?)", 
                       (user_id, gpa, "Math, Programming, DB, English"))
        
        # Attendance
        total = 100
        attended = random.randint(70, 100)
        percentage = (attended / total) * 100
        cursor.execute("INSERT INTO attendance (user_id, total_classes, attended_classes, percentage) VALUES (?, ?, ?, ?)", 
                       (user_id, total, attended, percentage))
        
        # Exams
        score = random.randint(40, 100)
        result = "Pass" if score >= 50 else "Fail"
        cursor.execute("INSERT INTO exams (user_id, exam_name, score, result) VALUES (?, ?, ?, ?)", 
                       (user_id, "Semester 1", score, result))
        
        # Fees
        total_fee = 50000
        paid = random.choice([25000, 50000, 10000])
        due = total_fee - paid
        cursor.execute("INSERT INTO fees (user_id, total_fee, paid, due) VALUES (?, ?, ?, ?)", 
                       (user_id, total_fee, paid, due))
        
        # Library
        cursor.execute("INSERT INTO library (user_id, books_issued, fine) VALUES (?, ?, ?)", 
                       (user_id, "Python Basics", 0))

    # FAQ Data - Extensive List
    faqs = [
        # General Info
        ("When does the college start?", "Classes begin at 9:00 AM sharp."),
        ("Where is Unreal University located?", "We are located at 123 Innovation Drive, Tech City."),
        ("How can I contact administration?", "You can email admin@unrealuni.edu or call +1-800-UNREAL."),
        ("Is there parking available?", "Yes, student parking is available in Lot B behind the sports complex."),
        
        # Academics
        ("What is the passing criteria?", "You need a minimum of 50% in both internal and external exams to pass."),
        ("Who is the HOD of BCA?", "Dr. Alan Turing is the HOD of BCA."),
        ("Who is the HOD of B.Tech?", "Dr. Grace Hopper is the HOD of B.Tech."),
        ("How do I apply for a leave?", "Leave applications must be submitted through the student portal 2 days in advance."),
        ("What are the library hours?", "The library is open from 8:00 AM to 8:00 PM on weekdays."),
        
        # Facilities
        ("Is there Wi-Fi on campus?", "Yes, free Wi-Fi is available. Use your Roll No as the username."),
        ("What is the cafeteria menu?", "The cafeteria serves North Indian, South Indian, and Continental dishes."),
        ("Is there a gym?", "Yes, a state-of-the-art gym is available in the Student Center."),
        ("Are there hostel facilities?", "Yes, we have separate hostels for boys and girls with AC and non-AC rooms."),
        ("What is the hostel fee?", "Hostel fee ranges from $2000 to $4000 per semester depending on the room."),
        
        # Exams & Fees
        ("How to pay fees?", "You can pay fees online via this portal or at the accounts office."),
        ("What is the fine for late fee payment?", "A fine of $50 per week is charged for late payments."),
        ("When are the semester exams?", "Semester exams generally commence in May and December."),
        ("How can I get my transcript?", "Transcripts can be requested from the Exam Cell."),
        
        # Activities
        ("Are there sports clubs?", "Yes, we have Cricket, Football, Basketball, and eSports clubs."),
        ("When is the annual fest?", "Our annual tech fest 'Unreal Tech' happens in March."),
        ("Can I start a new club?", "Yes, submit a proposal to the Student Council for approval.")
    ]
    cursor.executemany("INSERT INTO faq (question, answer) VALUES (?, ?)", faqs)

    # Timetable Data
    # Sample data for BCA, B.Tech, B.Sc
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    departments = ["BCA", "B.Tech", "B.Sc"]
    
    # Generic subjects to fill periods
    subjects_pool = {
        "BCA": ["Programming", "Web Dev", "Maths", "English", "Lab", "OS", "Networks", "Library"],
        "B.Tech": ["Physics", "Chemistry", "Maths", "C++", "Mechanics", "Workshop", "Electronics", "Sports"],
        "B.Sc": ["Botany", "Zoology", "Chem", "English", "Tamil", "Lab", "NSS", "Library"]
    }
    
    timetable_data = []
    
    for dept in departments:
        for day in days:
             # Just randomizing for variety
             pool = subjects_pool[dept]
             periods = [random.choice(pool) for _ in range(8)]
             timetable_data.append(
                 (dept, day, periods[0], periods[1], periods[2], periods[3], periods[4], periods[5], periods[6], periods[7])
             )
    
    cursor.executemany('''INSERT INTO timetables (course, day_of_week, p1, p2, p3, p4, p5, p6, p7, p8) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', timetable_data)

    # 9. Library Books Table (NEW)
    cursor.execute('''CREATE TABLE IF NOT EXISTS library_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        author TEXT,
        total_copies INTEGER,
        available_copies INTEGER
    )''')

    # Populate Library Books
    books = [
        ("Python Crash Course", "Eric Matthes", 10, 8),
        ("Introduction to Algorithms", "Cormen", 5, 2),
        ("Clean Code", "Robert C. Martin", 8, 5),
        ("Artificial Intelligence: A Modern Approach", "Russell & Norvig", 6, 1),
        ("Design Patterns", "Gamma et al.", 7, 7),
        ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", 3, 0),
        ("The Great Gatsby", "F. Scott Fitzgerald", 4, 3),
        ("Calculus", "James Stewart", 15, 12),
        ("Physics for Scientists", "Serway", 12, 10),
        ("Operating System Concepts", "Silberschatz", 20, 15)
    ]
    cursor.executemany("INSERT INTO library_books (title, author, total_copies, available_copies) VALUES (?, ?, ?, ?)", books)
    print("Library books inserted.")

    conn.commit()
    conn.close()
    print("Sample data inserted successfully.")

if __name__ == "__main__":
    create_tables()
    insert_data()
