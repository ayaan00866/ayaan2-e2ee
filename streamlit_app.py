import streamlit as st
import time
import threading
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import database as db  # Ensure database.py is updated for multi-user
import requests

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Ayaan Khan Multi-User",
    page_icon="✅",
    layout="wide"
)

# --- BATMAN DARK UI CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap');

header[data-testid="stHeader"] { visibility: hidden !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }

.stApp {
    background: #050a12;
    background-image: radial-gradient(circle at top, #0a192f 0%, #050a12 100%);
    color: #ffffff !important;
    font-family: 'Outfit', sans-serif !important;
}

.main-header {
    border: 2px solid #00d2ff;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 0 15px rgba(0, 210, 255, 0.3);
    margin-bottom: 25px;
}

.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background: #0d1b2a !important;
    color: #00d2ff !important;
    border: 1px solid #1f4068 !important;
}

div.stButton > button {
    background: linear-gradient(90deg, #1e3799, #0984e3) !important;
    color: white !important;
    font-weight: bold;
    border-radius: 10px !important;
    height: 45px;
}

.console-output {
    background: #000000;
    color: #00ff00;
    font-family: 'Courier New', monospace;
    padding: 15px;
    border-radius: 10px;
    height: 250px;
    overflow-y: auto;
    border: 1px solid #333;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# --- MULTI-USER STATE CLASS ---
class UserAutomationState:
    def __init__(self, user_id):
        self.user_id = user_id
        self.running = False
        self.message_count = 0
        self.logs = []
        self.rotation_index = 0

# Har user ka state memory mein alag rakhein
if 'all_user_states' not in st.session_state:
    st.session_state.all_user_states = {}

def get_current_user_state():
    uid = st.session_state.get('user_id')
    if uid not in st.session_state.all_user_states:
        st.session_state.all_user_states[uid] = UserAutomationState(uid)
    return st.session_state.all_user_states[uid]

# --- LOGGING ---
def log_msg(msg, state):
    timestamp = time.strftime("%H:%M:%S")
    state.logs.append(f"[{timestamp}] {msg}")

# --- BROWSER ENGINE ---
def setup_engine(state):
    log_msg("Initializing Browser Engine...", state)
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    for path in ['/usr/bin/google-chrome', '/usr/bin/chromium']:
        if Path(path).exists():
            chrome_options.binary_location = path
            break
            
    try:
        return webdriver.Chrome(options=chrome_options)
    except Exception as e:
        log_msg(f"Engine Error: {str(e)[:50]}", state)
        return None

# --- WORKER THREAD ---
def automation_worker(config, username, state, uid):
    driver = None
    try:
        driver = setup_engine(state)
        if not driver: return
        
        driver.get('https://www.facebook.com/')
        time.sleep(5)
        
        # Inject Cookies
        if config['cookies']:
            for cookie in config['cookies'].split(';'):
                if '=' in cookie:
                    name, value = cookie.strip().split('=', 1)
                    driver.add_cookie({'name': name, 'value': value, 'domain': '.facebook.com'})
        
        driver.get(f"https://www.facebook.com/messages/t/{config['chat_id']}")
        time.sleep(10)
        
        msgs = [m.strip() for m in config['messages'].split('\n') if m.strip()]
        
        while state.running:
            # Find input box
            input_box = None
            for selector in ['div[contenteditable="true"]', 'textarea', '[role="textbox"]']:
                try:
                    input_box = driver.find_element(By.CSS_SELECTOR, selector)
                    if input_box: break
                except: continue
            
            if input_box:
                raw_msg = msgs[state.rotation_index % len(msgs)]
                final_msg = f"{config['name_prefix']} {raw_msg}" if config['name_prefix'] else raw_msg
                
                # JavaScript based typing (Faster & Reliable)
                driver.execute_script("arguments[0].innerText = arguments[1]", input_box, final_msg)
                input_box.send_keys(Keys.ENTER)
                
                state.message_count += 1
                state.rotation_index += 1
                log_msg(f"Sent: {final_msg[:20]}...", state)
                time.sleep(int(config['delay']))
            else:
                log_msg("Waiting for Chat Box...", state)
                time.sleep(5)
                
    except Exception as e:
        log_msg(f"Fatal Stop: {str(e)[:50]}", state)
    finally:
        state.running = False
        db.set_automation_running(uid, False)
        if driver: driver.quit()

# --- LOGIN LOGIC ---
def login_page():
    st.markdown('<div class="main-header"><h1>Ayanw\'4 🤖</h1><p>Master Multi-User System</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("UNLOCK ACCESS", use_container_width=True):
            user_id = db.verify_user(username, password)
            if user_id:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid Username or Password")

# --- MAIN DASHBOARD ---
def main_app():
    uid = st.session_state.user_id
    state = get_current_user_state()
    
    st.sidebar.markdown(f"### 👤 {st.session_state.username}")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        state.running = False
        st.session_state.logged_in = False
        st.rerun()
        
    # --- ADMIN TAB (ONLY FOR MASTER) ---
    tabs = ["⚙️ Task Setup", "🚀 Live Monitor"]
    if st.session_state.username == "AY4N":
        tabs.append("💎 Admin Panel")
    
    all_tabs = st.tabs(tabs)
    
    user_config = db.get_user_config(uid)

    with all_tabs[0]:
        st.markdown("### 🛠️ Configuration")
        c1, c2 = st.columns(2)
        with c1:
            chat_id = st.text_input("Target Chat UID", value=user_config['chat_id'])
            prefix = st.text_input("Sender Name (Prefix)", value=user_config['name_prefix'])
            delay = st.number_input("Speed (Seconds)", value=user_config['delay'], min_value=1)
        with c2:
            cookies = st.text_area("Facebook Cookies", placeholder="Paste cookies here...")
            messages = st.text_area("Message List (One per line)", value=user_config['messages'])
            
        if st.button("💾 SAVE CONFIG", use_container_width=True):
            db.update_user_config(uid, chat_id, prefix, delay, cookies or user_config['cookies'], messages)
            st.success("Configuration Saved Successfully!")

    with all_tabs[1]:
        col1, col2 = st.columns(2)
        if col1.button("▶️ START AUTOMATION", disabled=state.running, use_container_width=True):
            state.running = True
            db.set_automation_running(uid, True)
            t = threading.Thread(target=automation_worker, args=(user_config, st.session_state.username, state, uid))
            t.daemon = True
            t.start()
            st.rerun()
            
        if col2.button("⏹️ STOP AUTOMATION", disabled=not state.running, use_container_width=True):
            state.running = False
            db.set_automation_running(uid, False)
            st.rerun()

        st.markdown(f"**Current Status:** {'🟢 Running' if state.running else '🔴 Stopped'} | **Messages Sent:** `{state.message_count}`")
        
        if state.logs:
            log_content = "".join([f'<div>{l}</div>' for l in state.logs[-20:]])
            st.markdown(f'<div class="console-output">{log_content}</div>', unsafe_allow_html=True)
            if st.button("🔄 Refresh Logs"): st.rerun()

    if len(all_tabs) > 2:
        with all_tabs[2]:
            st.markdown("### 👑 Master Admin Control")
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password")
            if st.button("Create User"):
                db.create_user(new_user, new_pass)
                st.success(f"User {new_user} Created!")

# --- APP FLOW ---
if not st.session_state.get('logged_in'):
    login_page()
else:
    main_app()
    st.markdown('<div style="text-align:center; opacity:0.5; margin-top:20px;">Powered by Ayaan Khan 🦂</div>', unsafe_allow_html=True)
