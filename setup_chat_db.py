import sqlite3

DB_NAME = "database.db"

def create_chat_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create chat_messages table
    print("Creating chat_messages table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Table 'chat_messages' created successfully (if it didn't exist).")

if __name__ == "__main__":
    create_chat_table()
