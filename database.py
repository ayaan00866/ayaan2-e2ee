import sqlite3
import hashlib

def get_db():
    conn = sqlite3.connect('users_data.db', check_same_thread=False)
    return conn

# Database table banana
conn = get_db()
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
               (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, 
                chat_id TEXT, name_prefix TEXT, delay INTEGER, cookies TEXT, messages TEXT, running BOOLEAN)''')
conn.commit()

def verify_user(username, password):
    cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    return user[0] if user else None

def create_user(username, password):
    try:
        cursor.execute("INSERT INTO users (username, password, chat_id, name_prefix, delay, cookies, messages, running) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (username, password, '', '', 60, '', '', False))
        conn.commit()
        return True
    except:
        return False

def get_user_config(user_id):
    cursor.execute("SELECT chat_id, name_prefix, delay, cookies, messages FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    return {'chat_id': row[0], 'name_prefix': row[1], 'delay': row[2], 'cookies': row[3], 'messages': row[4]}

def update_user_config(user_id, chat_id, prefix, delay, cookies, messages):
    cursor.execute("UPDATE users SET chat_id=?, name_prefix=?, delay=?, cookies=?, messages=? WHERE id=?",
                   (chat_id, prefix, delay, cookies, messages, user_id))
    conn.commit()

def set_automation_running(user_id, status):
    cursor.execute("UPDATE users SET running=? WHERE id=?", (status, user_id))
    conn.commit()

# --- PEHLI BAAR ADMIN BANANE KE LIYE ---
if not verify_user("AY4N", "KH4N"):
    create_user("AY4N", "KH4N")
  
