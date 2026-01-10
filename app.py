# app.py
import sys

from typer import style


sys.path.insert(0, '.')
import streamlit as st
st.set_page_config(layout="wide")


from database.db import init_db,get_conn
init_db()

try:
    from nlu_engine.infer_intent import IntentClassifier
    from nlu_engine.entity_extractor import extract_entities
except ImportError as e:
    
    IntentClassifier = None
    extract_entities = lambda text: []

    def extract_entities(text):  # ✅ REAL FALLBACK
        import re
        entities = {}
        # patterns = {"amount": r'\b\d+[kK]?\b', "account": r'\b\d{10}\b'}
        patterns = {
        "amount":r'\b(?:\d{1,3}(?:,\d{3})*|₹?\d{1,4})\s*(?:rupees?|rs\.?|inr)?\b',  # ₹10,000, 5000, 10K
        "account": r'(?:account|to\s+acc(?:ount)?)\s*(\d{8,12})\b'  # Flexible 987543210
         }
        for key, pat in patterns.items():
            matches = re.findall(pat, text, re.IGNORECASE)
            if matches: entities[key] = matches
        return entities
  
import json
import os
import sqlite3 
import pandas as pd
import subprocess
import time
from pathlib import Path
import plotly.express as px  # Line 6

from database.bank_curd import create_account, list_accounts
#from main_app import ENTITY_ICONS, MODEL_DIR, model_exists
 # Creates chat_history table on startup
# Quick create nlu_engine/infer_intent.py





from dialogue_manager.dialogue_handler import DialogueManager
from nlu_engine.nlu_router import run_nlu



BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = Path("./models/intent_model")
LOG_PATH = Path("./models/training.log")
INTENTS_PATH = BASE_DIR / "nlu_engine" / "intents.json"

ENTITY_ICONS = {
    "amount": "💰","account_number": "🏦","card": "💳","location": "📍","time": "⏰",
}




def model_exists():
    return MODEL_DIR.exists() and any(MODEL_DIR.iterdir())

def start_training_subprocess(epochs: int, batch_size: int, lr: float) -> subprocess.Popen:
    cmd = [
        sys.executable, str(BASE_DIR / "nlu_engine" / "train_intent.py"),
        "--intents", str(INTENTS_PATH), "--model_name", "distilbert-base-uncased",
        "--output_dir", str(MODEL_DIR), "--epochs", str(epochs),
        "--batch_size", str(batch_size), "--lr", str(lr),
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    














# ---------- SESSION STATE ----------
if "dm" not in st.session_state:
    st.session_state.dm = DialogueManager()
if "messages" not in st.session_state:
    st.session_state.messages = []
st.set_page_config(page_title="BankBot AI", layout="wide")

# GLASSMORPHISM - Add this ONE line


       


# ---------- PAGES ----------
def page_home():
    st.title("🏠 Home")

           
    st.markdown(
        """
        <style>
        .stApp {
        background-color: #ffffff;
        color: #111827;
    }
        .hero {
            padding: 26px 30px;
            border-radius: 18px;
            background: radial-gradient(circle at top left, #22c55e 0, #0f172a 40%, #020617 100%);
            border: 1px solid #22c55e33;
            margin-bottom: 22px;
        }
        .hero-title {
            font-size: 38px;
            font-weight: 900;
            color: #f9fafb;
            margin-bottom: 6px;
        }
        .hero-sub {
            font-size: 16px;
            color: #e5e7eb;
        }
        .hero-badge {
            display:inline-block;
            padding:4px 10px;
            border-radius:999px;
            background:#22c55e22;
            color:#bbf7d0;
            font-size:12px;
            margin-bottom:8px;
        }
        .tile {
            padding: 18px 20px;
            border-radius: 16px;
            color: #f9fafb;
            border: 1px solid #1f2937;
            box-shadow: 0 10px 25px rgba(15,23,42,0.7);
            margin-bottom: 16px;
        }
        .tile h3 {
            margin: 0 0 6px 0;
            font-size: 20px;
        }
        .tile p {
            margin: 0;
            font-size: 14px;
            color: #e5e7eb;
        }
        .grad-pink {
            background: linear-gradient(135deg, #db2777, #7c3aed);
        }
        .grad-blue {
            background: linear-gradient(135deg, #2563eb, #0891b2);
        }
        .grad-amber {
            background: linear-gradient(135deg, #f97316, #eab308);
        }
        .grad-teal {
            background: linear-gradient(135deg, #0f766e, #22c55e);
        }
        .pill-row span {
            display:inline-block;
            padding:4px 10px;
            border-radius:999px;
            font-size:11px;
            background:#111827;
            color:#e5e7eb;
            margin-right:6px;
            margin-top:4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # HERO SECTION
    st.markdown(
        """
        <div class="hero">
            <div class="hero-badge">🏦 BankBot AI • Milestone 2</div>
            <div class="hero-title">BANKBOT- AI Chatbot For Banking FAQ's </div>
            <div class="hero-sub">
                Intent & entity powered chatbot connected to a live SQLite bank database.
                Explore NLU, dialogue and data from a single place.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    # LEFT COLUMN – milestone + NLU
    with col1:
        st.markdown(
            """
            <div class="tile grad-pink">
                <h3>📌 Milestone 2 – What you built</h3>
                <p>
                    • Intent recognition for <b>transfer money</b>, <b>check balance</b>,
                    <b>find ATM</b> and <b>card block</b>.<br>
                    • Entity extraction for <b>amount</b>, <b>currency</b>,
                    <b>account number</b> and <b>location</b>.<br>
                    • A dialogue manager that can handle multi‑turn flows
                    like balance enquiry and fund transfer with password check.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="tile grad-amber">
                <h3>🧠 User Query / NLU Demo</h3>
                <p>
                    Playground to inspect the NLU engine.<br>
                    • Type any banking question and see top intents with scores.<br>
                    • Check extracted entities to debug training data.<br>
                    Perfect for explaining how your model “understands” the user.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # RIGHT COLUMN – chatbot + database
    with col2:
        st.markdown(
            """
            <div class="tile grad-blue">
                <h3>💬 Chatbot</h3>
                <p>
                    Full end‑to‑end BankBot conversation UI.<br>
                    • Handles balance check and money transfer, step by step.<br>
                    • Asks for account number, amount, password and receiver.<br>
                    • Shows real responses from the database (including errors).
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="tile grad-teal">
                <h3>🗄️ Database & History</h3>
                <p>
                    • Create and list accounts stored in SQLite for testing flows.<br>
                    • Chatbot page keeps an in‑session conversation history,<br>
                      so you can scroll and show complete scenarios during your viva.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="pill-row">
            <span>🐍 Python</span>
            <span>🤗 Transformers – Intent Model</span>
            <span>🔍 Rule‑based Entity Extractor</span>
            <span>💾 SQLite DB</span>
            <span>🌐 Streamlit</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    
def page_user_query():

    st.title("🧠 User Query – NLU Demo")
    st.write(
        "The detailed NLU training and visualization UI runs in **main_app.py**.\n\n"
        "Open a new terminal in this project folder and run:\n\n"
        "`streamlit run main_app.py`\n\n"
        "Then use that page to view intents and entities interactively."
    )

def page_chatbot():
    st.markdown("""
<style>
/* Full app background */
.stApp {
    background: linear-gradient(135deg,#0f766e, #22c55e);  /* dark blue gradient */
    color: #e5e7eb;
}     
/* User message bubble */
div[data-testid="stChatMessage"][data-baseweb="user"] {
    background: #14532d;
    color: #e5e7eb;
}
/* BOT messages: text color */
div[data-testid="stChatMessage"][data-baseweb="assistant"]
    div[data-testid="stMarkdownContainer"] p {
    color: #111827 !important;     /* near‑black */
}

/* If you want ONLY bot grey and user white: */
div[data-testid="stChatMessage"][data-baseweb="assistant"] div[data-testid="stMarkdownContainer"] p {
    color: #9ca3af !important;   /* bot text grey */
}
div[data-testid="stChatMessage"][data-baseweb="user"] div[data-testid="stMarkdownContainer"] p {
    color: #f9fafb !important;   /* user text light */
}
                  
/* Chat container spacing */
section[data-testid="stSidebar"] + div [data-testid="stVerticalBlock"] {
    padding-top: 0.5rem;
}

/* Chat bubbles */
div[data-testid="stChatMessage"] {
    border-radius: 16px;
    margin-bottom: 0.4rem;
}
div[data-testid="stChatMessage"][data-baseweb="user"] {
    background: linear-gradient(135deg,#4ade80,#16a34a);
    color: #020617;
}
div[data-testid="stChatMessage"][data-baseweb="assistant"] {
    background: #020617;
    border: 1px solid #1f2937;
}

/* Chat input */
div[data-baseweb="textarea"] textarea {
    border-radius: 999px !important;
    background:#020617 !important;
    border:1px solid #334155 !important;
    color:#e5e7eb !important;
}
</style>
""", unsafe_allow_html=True)


    st.title("🏬Bank Chatbot")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "dm" not in st.session_state:
        st.session_state.dm = DialogueManager()

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.session_state.dm.reset()
        

    # show chat history
    for role, text in st.session_state.messages:
        if role == "bot":
            with st.chat_message("assistant", avatar="🤖"):
                st.write(text)
        else:
              with st.chat_message("user", avatar="🧑‍💻"):
                  st.write(text)
                  

            
            
    with st.form("chat_form", clear_on_submit=True):
        user_text = st.text_input("Type your message here...")
        submitted = st.form_submit_button("Send")

    if submitted and user_text.strip():
        text = user_text.strip()

        # NLU is called every turn, but DM will ignore intent while in_flow
        intent, entities = run_nlu(text)

        st.session_state.messages.append(("user", text))
        reply = st.session_state.dm.handle(intent, entities, text)
        st.session_state.messages.append(("bot", reply))

def page_database():
    st.markdown("""
    <style>
    /* Page background */
    .stApp {
        background: linear-gradient(135deg, #134e5e, #71b280);
        color: #f9fafb;
    }

    /* Card around the form */
    .db-card {
        background: rgba(15,23,42,0.9);
        border-radius: 18px;
        padding: 24px 28px;
        border: 1px solid #22c55e55;
        box-shadow: 0 20px 40px rgba(15,23,42,0.7);
    }

    /* Input labels */
    label {
        color: #e5e7eb !important;
        font-weight: 500;
    }

    /* Inputs */
    .stTextInput input, .stNumberInput input {
        background-color: #020617 !important;
        color: #e5e7eb !important;
        border-radius: 999px !important;
        border: 1px solid #4b5563 !important;
    }

    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg,#22c55e,#16a34a) !important;
        color: #020617 !important;
        border-radius: 999px !important;
        border: none !important;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title(" 💾Database Operations")

    st.subheader("Create New Account")
    with st.form("create_account_form"):
        name = st.text_input("User name")
        acc_no = st.text_input("Account number")
        acc_type = st.selectbox("Account type", ["savings", "current"])
        balance = st.number_input("Initial balance", min_value=0, step=1000)
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Create account")

    if submitted:
        if not (name and acc_no and password):
            st.error("Please fill all required fields.")
        else:
            msg = create_account(name, acc_no, acc_type, int(balance), password)
            st.success(msg)

    st.subheader("Existing Accounts")
    rows = list_accounts()
    if rows:
        st.table(
            {
                "Account Number": [r[0] for r in rows],
                "User Name": [r[1] for r in rows],
            }
        )
    else:
        st.info("No accounts found.") 

def page_chat_history():
        st.header("💬 Chat History")
    
    # 🔥 SAFETY FIRST
        conn = get_conn()
        if conn is None:
            st.error("❌ Database connection failed!")
            st.info("Run `init_db()` or check bankbot.db")
            return  # EXIT before query!
    
        try:
            history_df = pd.read_sql("""
            SELECT timestamp, user_query, predicted_intent,
                   confidence, entities
            FROM chat_history 
            ORDER BY timestamp DESC 
            LIMIT 100
        """, conn)
        
            st.dataframe(history_df)
        
        except Exception as e:
            st.error(f"Query failed: {e}")
        finally:
            conn.close()

    
    # st.title("📈 Chat History")
    # import pandas as pd
    
    # conn = get_conn()
    # history_df = pd.read_sql("""
    #     SELECT timestamp, user_query, predicted_intent, 
    #            confidence, success 
    #     FROM chat_history 
    #     ORDER BY timestamp DESC 
    #     LIMIT 100
    # """, conn)
    # conn.close()
    
    # if not history_df.empty:
    #     st.dataframe(history_df, use_container_width=True)
    #     csv = history_df.to_csv(index=False)
    #     st.download_button("📥 Export CSV", csv, "chat_history.csv")
    # else:
    #     st.info("👆 Use Chatbot first to see history!")

def page_admin_panel():
    st.title("🔧 Admin Dashboard")

   
    # 🔥 INLINE CSS - DARK GLASS + VISIBLE WHITE TEXT
    st.markdown("""
    <style>
    /* Gradient Background */
    .stApp { 
      background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 25%, #10b981 50%, #f59e0b 75%, #f97316 100%) !important;
      background-size: 400% 400% !important;
      animation: gradientShift 20s ease infinite !important;
    }
    @keyframes gradientShift {
      0%, 100% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
    }
    
    /* Dark Glass Hero & Cards */
    .glass-hero, .glass-card, [data-testid="metric-container"], [data-testid="stDataFrame"] {
      background: rgba(17, 24, 39, 0.95) !important;
      backdrop-filter: blur(25px) !important;
      border: 1px solid rgba(255, 255, 255, 0.3) !important;
      border-radius: 24px !important;
      padding: 24px !important;
      margin: 12px 0 !important;
      box-shadow: 0 12px 40px rgba(0,0,0,0.4) !important;
      transition: all 0.4s ease !important;
    }
    .glass-hero:hover, [data-testid="metric-container"]:hover {
      transform: translateY(-6px) !important;
      box-shadow: 0 20px 60px rgba(16,185,129,0.4) !important;
    }
    
    /* Glowing White Metrics */
    [data-testid="stMetricLabel"] { color: #f1f5f9 !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { 
      color: #ffffff !important; 
      text-shadow: 0 2px 12px rgba(255,255,255,0.9) !important;
      font-size: 2.4em !important; 
      font-weight: 800 !important; 
    }
    
    /* Rainbow Glass Buttons */
    div[data-testid="stButton"] button {
      background: rgba(255,255,255,0.18) !important;
      backdrop-filter: blur(25px) !important;
      border: 2px solid rgba(255,255,255,0.4) !important;
      border-radius: 20px !important;
      color: #ffffff !important;
      font-weight: 700 !important;
      text-shadow: 0 1px 4px rgba(0,0,0,0.6) !important;
      padding: 16px 28px !important;
      min-height: 56px !important;
      transition: all 0.3s cubic-bezier(0.25,0.46,0.45,0.94) !important;
    }
    div[data-testid="stButton"] button:hover {
      transform: translateY(-4px) scale(1.02) !important;
      box-shadow: 0 16px 50px rgba(0,0,0,0.5) !important;
      background: rgba(255,255,255,0.28) !important;
      border-color: #10b981 !important;
    }
    
    /* Button Colors by Column */
    button:nth-of-type(1):hover { background: rgba(16,185,129,0.4) !important;border-radius: 20px !important; border: 2px solid #10b981 !important;color:black !important; }
    button:nth-of-type(2):hover { background: rgba(59,130,246,0.4) !important;border-radius: 20px !important; border: 2px solid #3b82f6 !important;color:black !important; }
    button:nth-of-type(3):hover { background: rgba(239,68,68,0.4) !important;border-radius: 20px !important; border: 2px solid #ef4444 !important;color:black !important; }
    button:nth-of-type(4):hover { background: rgba(245,158,11,0.4) !important;border-radius: 20px !important; border: 2px solid #f59e0b !important;color:black !important; }
    button:nth-of-type(5):hover { background: rgba(168,85,247,0.4) !important;border-radius: 20px !important; border: 2px solid #a855f7 !important;color:black !important; }
    /* Glass Sidebar & Tabs */
    section[data-testid="stSidebar"] { 
      background: rgba(17,24,39,0.98) !important; 
      backdrop-filter: blur(30px) !important; 
    }
    div[data-testid="stTab"] { 
      background: rgba(255,255,255,0.12) !important; 
      color: #e2e8f0 !important; 
      border-radius: 16px !important; 
    }
    div[data-testid="stTab"]:hover { background: rgba(16,185,129,0.25) !important; }
    /* 🔥 ANIMATED BLACK BOXES + HOVER EFFECTS */
div[data-testid="stPlotlyChart"],
div[role="figure"] {
    background: rgba(17, 24, 39, 0.95) !important;  /* Your black box */
    backdrop-filter: blur(20px) !important;
    border-radius: 20px !important;
    border: 1px solid rgba(59, 130, 246, 0.5) !important;  /* Blue glow border */
    box-shadow: 
        0 20px 60px rgba(0,0,0,0.6),
        0 0 30px rgba(59, 130, 246, 0.3) !important;  /* Blue outer glow */
    animation: boxFloat 6s ease-in-out infinite !important;
    transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
    margin: 15px 0 !important;
    padding: 2px !important;
}

div[data-testid="stPlotlyChart"]:hover,
div[role="figure"]:hover {
    transform: translateY(-15px) scale(1.02) !important;
    box-shadow: 
        0 35px 80px rgba(0,0,0,0.8),
        0 0 50px rgba(16, 185, 129, 0.6) !important;  /* Green hover glow */
    animation-duration: 2s !important;
}

@keyframes boxFloat {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-8px) rotate(0.5deg); }
}

/* 📊 SMOOTH CHART ANIMATIONS */
.plotly .cartesianlayer path,
.plotly .pie path {
    stroke-width: 2px !important;
    stroke: rgba(255,255,255,0.3) !important;
    filter: drop-shadow(0 4px 12px rgba(0,0,0,0.5)) !important;
    transition: all 0.3s ease !important;
}

.plotly .cartesianlayer path:hover,
.plotly .pie path:hover {
    filter: drop-shadow(0 0 20px currentColor) !important;
    stroke-width: 4px !important;
    transform: scale(1.1) !important;
}

/* ✨ LEGEND GLOW */
.plotly .legendtext,
.plotly .legendsmarker {
    filter: drop-shadow(0 2px 8px rgba(0,0,0,0.7)) !important;
    transition: all 0.3s ease !important;
}

.plotly .legendtext:hover {
    color: #10b981 !important;  /* Green hover */
    transform: scale(1.05) !important;
}
/* 🎯 CLICKABLE PIE SLICE HIGHLIGHT */
.plotly .pie path {
    cursor: pointer !important;
    stroke: rgba(255,255,255,1) !important;
    stroke-width: 4px !important;
    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
}

.plotly .pie path:hover {
    transform: scale(1.15) translate(5px, -5px) !important;
    filter: drop-shadow(0 10px 30px currentColor) !important;
    stroke-width: 6px !important;
    stroke: rgba(255,255,255,1.5) !important;
}

.plotly .pie path[fill='#F59E0B']:hover {  /* Gold slice */
    filter: drop-shadow(0 15px 40px #F59E0B) !important;
}

.plotly .pie path[fill='#DC2626']:hover {  /* Red slice */
    filter: drop-shadow(0 15px 40px #DC2626) !important;
}

/* Clicked slice stays highlighted */
.plotly .pie path[clicked=true] {
    transform: scale(1.2) !important;
    stroke-width: 8px !important;
    filter: drop-shadow(0 20px 50px currentColor) !important;
}


    </style>
    """, unsafe_allow_html=True)
    
    

    
    # Your existing admin code continues here...
    st.markdown('<div class="glass-hero"><h1 style="color:#ffffff;text-align:center;">⚙️ Admin Dashboard</h1></div>', unsafe_allow_html=True)
    # metrics, buttons, charts...


    

    


    
    import pandas as pd
    from database.db import get_conn

    conn = get_conn()
    total = pd.read_sql("SELECT COUNT(*) FROM chat_history", conn).iloc[0,0]
    success_rate = pd.read_sql("SELECT AVG(CASE WHEN success=1 THEN 1 ELSE 0 END)*100 FROM chat_history", conn).iloc[0,0]
    low_conf = pd.read_sql("SELECT COUNT(*) FROM chat_history WHERE confidence < 0.7", conn).iloc[0,0]
    num_intents = pd.read_sql("SELECT COUNT(DISTINCT predicted_intent) FROM chat_history WHERE predicted_intent IS NOT NULL", conn).iloc[0,0]
    num_entities = pd.read_sql("SELECT COUNT(*) FROM chat_history WHERE predicted_intent IS NOT NULL", conn).iloc[0,0] or 0
    
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Queries", total)
    col2.metric("Success Rate", f"{success_rate:.1f}%")
    col3.metric("Low Confidence", low_conf)
    col4, col5, col6 = st.columns(3)
    col4.metric("Intents", num_intents)
    col5.metric("Entities", num_entities)
    col6.metric("Avg Confidence", f"{pd.read_sql('SELECT AVG(confidence) FROM chat_history', get_conn()).iloc[0,0]:.2f}")
    

    # Sidebar navigation like your design
    st.sidebar.markdown("### 📊 Quick Actions")
    if st.sidebar.button("🔄 Refresh"):
        st.rerun()
    # if st.sidebar.button("📤 Export CSV"):
    #     st.download_button("Download", pd.read_sql("SELECT * FROM chat_history", get_conn()).to_csv(), "admin_export.csv")
    #     conn.close()
    # 5 TABS exactly like your design
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Chat Analytics", "🔍 Query Analytics", "🧠 Training Editor", "❓ Knowledge Base", "📤 Export Logs"])

    with tab1:
        st.subheader("📊 Chat Analytics - Live Dashboard")


        import plotly.express as px
        from database.db import get_conn
        
            
        


    
    # Session state for intent buttons
        if 'show_transfer' not in st.session_state:
            st.session_state.show_transfer = False
        if 'show_balance' not in st.session_state:
            st.session_state.show_balance = False
        if 'show_card' not in st.session_state:
            st.session_state.show_card = False
        if 'show_atm' not in st.session_state:
            st.session_state.show_atm = False
        if 'show_overall' not in st.session_state:
            st.session_state.show_overall = False
    
    # INTENT BUTTONS (Click to show specific pie charts)
        col1, col2, col3, col4 ,col5= st.columns(5)
        with col1:
            if st.button("💰 Transfer Money", key="btn_transfer"):
                st.session_state.show_transfer = True
            # Hide others
                st.session_state.show_balance = False
                st.session_state.show_overall = False
                st.session_state.show_card = False
                st.session_state.show_atm = False
                st.rerun()
    
        with col2:
            if st.button("💳 Check Balance", key="btn_balance"):
                st.session_state.show_balance = True
                st.session_state.show_transfer = False
                st.session_state.show_card = False
                st.session_state.show_atm = False
                st.rerun()
    
        with col3:
            if st.button("🚫 Card Block", key="btn_card"):
                st.session_state.show_card = True
                st.session_state.show_transfer = False
                st.session_state.show_balance = False
                st.session_state.show_atm = False
                st.rerun()
    
        with col4:
            if st.button("🏧 Find ATM", key="btn_atm"):
                st.session_state.show_atm = not st.session_state.show_atm
                st.session_state.show_transfer = False
                st.session_state.show_balance = False
                st.session_state.show_card = False
                st.rerun()
        with col5:
            if st.button("📊 Overall Analytics"):
               st.session_state.show_overall = True
               st.session_state.show_transfer = False
               st.session_state.show_balance = False
               st.session_state.show_card = False
               st.session_state.show_atm = False
               st.rerun()
        st.markdown("---")

        
        if st.session_state.show_overall:
            st.markdown("---")
            st.subheader("📈 Overall Analytics")

    
    # Overall Pie Chart
            intent_df = pd.read_sql("""
        SELECT predicted_intent, COUNT(*) as count
        FROM chat_history WHERE predicted_intent IS NOT NULL
        GROUP BY predicted_intent ORDER BY count DESC
    """, conn)
    
            if not intent_df.empty:
                fig_overall = px.pie(intent_df, values='count', names='predicted_intent',
                           title="🎯 All Intents Distribution")
                fig_overall.update_traces(textposition='inside', textinfo='percent+label')
                fig_overall.update_layout(
                    clickmode='event+select',
                    hovermode='closest'
                )

               

                st.plotly_chart(fig_overall, use_container_width=True, config={'displayModeBar': True,})

        
        # Overall Success Bar
           # 📊 % OF QUESTIONS BY INTENT (Perfect Y-axis!)
            usage_df = pd.read_sql("""
    SELECT predicted_intent,
           COUNT(*) as question_count,
           ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM chat_history WHERE predicted_intent IS NOT NULL), 1) as usage_pct
    FROM chat_history 
    WHERE predicted_intent IS NOT NULL
    GROUP BY predicted_intent
    ORDER BY question_count DESC
""", conn)

# Usage Distribution Bar Chart
            fig_usage = px.bar(usage_df, x='predicted_intent', y='usage_pct',
                  title="📈 % of Questions by Intent (Usage Distribution)",
                  color='usage_pct', color_continuous_scale='Viridis')
            fig_usage.update_layout(xaxis_tickangle=-45, height=450)
           


            fig_usage.update_yaxes(title="% of Total Questions")
            st.plotly_chart(fig_usage, use_container_width=True)

    
    # SPECIFIC INTENT PIE CHARTS (Button-triggered)
        st.markdown("---")
    
        if st.session_state.show_transfer:
            st.subheader("💰 Transfer Money Analytics")
            # 2 COLUMNS: Pie + Bar (Transfer Money ONLY)
            col1, col2 = st.columns(2)

            # PIE: Transfer Money Intent Contribution (from ALL history)
            with col1:
                transfer_pct = pd.read_sql("""
        SELECT 
            'Transfer Money' as category, 
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM chat_history WHERE predicted_intent IS NOT NULL), 1) as pct
        FROM chat_history WHERE predicted_intent='transfer_money'
    """, conn).iloc[0,1] if pd.read_sql("SELECT COUNT(*) FROM chat_history WHERE predicted_intent='transfer_money'", conn).iloc[0,0] > 0 else 0
    
                pie_data = pd.DataFrame({
        'category': ['Transfer Money', 'Other Intents'],
        'pct': [transfer_pct, 100 - transfer_pct]
    })
                fig_pie = px.pie(pie_data, values='pct', names='category',
                   title=f"💰 Transfer Money: {transfer_pct}% of Total",
                   color_discrete_sequence=['#7C3AED', "#72083D" ])  # Peach + Transparent!
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(
                    clickmode='event+select',
                    hovermode='closest'
                )
                
                st.plotly_chart(fig_pie, use_container_width=True,config={'displayModeBar': True, 'staticPlot': False})
                
                
            with col2:
        # BAR: Top Transfer Queries
                transfer_queries = pd.read_sql("""
            SELECT user_query, COUNT(*) as count
            FROM chat_history WHERE predicted_intent='transfer_money'
            GROUP BY user_query ORDER BY count DESC LIMIT 5
        """, conn)
                fig_bar = px.bar(transfer_queries, x='count', y='user_query',
                        orientation='h', title="Top Transfer Queries")
                
                st.plotly_chart(fig_bar, use_container_width=True)

            
        if st.session_state.show_balance:
            st.subheader("💳 Check Balance Analytics")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                # Check Balance % + Empty space

        # Check Balance % + Empty space
                balance_pct = pd.read_sql("""
            SELECT 
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM chat_history WHERE predicted_intent IS NOT NULL), 1) as pct
            FROM chat_history WHERE predicted_intent='check_balance'
        """, conn).iloc[0,0] if pd.read_sql("SELECT COUNT(*) FROM chat_history WHERE predicted_intent='check_balance'", conn).iloc[0,0] > 0 else 0
        
                pie_data = pd.DataFrame({
            'category': ['Check Balance', 'Other Intents'],
            'pct': [balance_pct, 100 - balance_pct]
        })
        
                fig_pie = px.pie(pie_data, values='pct', names='category',
                       title=f"💳 Check Balance: {balance_pct}% of Total",
                       color_discrete_sequence=['#3b82f6', "#991111"])  # Blue + Transparent!
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
    
            with col_b2:
                # Top Check Balance queries
             
                balance_queries = pd.read_sql("""
            SELECT user_query, COUNT(*) as count
            FROM chat_history WHERE predicted_intent='check_balance'
            GROUP BY user_query ORDER BY count DESC LIMIT 5
        """, conn)
                if not balance_queries.empty:
                    fig_bar = px.bar(balance_queries, x='count', y='user_query',
                           orientation='h', title="Top Check Balance Queries")
                    st.plotly_chart(fig_bar, use_container_width=True)

             
        # Top Check Balance queries
             
           
        if st.session_state.show_card:
            st.subheader("🚫 Card Block Analytics")
            card_df = pd.read_sql("""
            SELECT predicted_intent, 
                   ROUND(confidence*100,0)||'%' as confidence,
                   COUNT(*) as count
            FROM chat_history WHERE predicted_intent='card_block'
            GROUP BY confidence ORDER BY confidence DESC
        """, conn)
            if not card_df.empty:
                fig_c = px.pie(card_df, values='count', names='confidence',
                          title="Card Block: Confidence Distribution")
                st.plotly_chart(fig_c, use_container_width=True)
            
        if st.session_state.show_atm:
            st.subheader("🏧 Find ATM Analytics")
            atm_df = pd.read_sql("""
            SELECT predicted_intent, 
                   ROUND(confidence*100,0)||'%' as confidence,
                   COUNT(*) as count
            FROM chat_history WHERE predicted_intent='find_atm'
            GROUP BY confidence ORDER BY confidence DESC
        """, conn)
            if not atm_df.empty:
                fig_a = px.pie(atm_df, values='count', names='confidence',
                          title="Find ATM: Confidence Distribution")
                st.plotly_chart(fig_a, use_container_width=True)

        st.markdown("---")
        st.subheader("💬 Recent Chat Activity")
        recent_df = pd.read_sql("""
    SELECT user_query, predicted_intent, 
           ROUND(confidence*100,0)||'%' as confidence,
           CASE WHEN success=1 THEN '✅' ELSE '❌' END as success,
           substr(timestamp, 1, 16) as timestamp
           FROM chat_history ORDER BY id DESC LIMIT 100  
""", conn)
        st.dataframe(recent_df, use_container_width=True)
    with tab2:
        # ===== NEW QUERY ANALYTICS TAB =====
        st.subheader("🔍 Query Analytics")

        # 4 Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Queries", pd.read_sql("SELECT COUNT(*) FROM nlu_history", conn).iloc[0,0])
        col2.metric("Intents", pd.read_sql("SELECT COUNT(DISTINCT predicted_intent) FROM nlu_history WHERE predicted_intent IS NOT NULL", conn).iloc[0,0])
        col3.metric("Low Confidence", pd.read_sql("SELECT COUNT(*) FROM nlu_history WHERE confidence < 0.8", conn).iloc[0,0])
        col4.metric("Today", pd.read_sql("SELECT COUNT(*) FROM nlu_history WHERE date(timestamp) = date('now')", conn).iloc[0,0])
        st.markdown("---")

        # CHARTS FROM YOUR HISTORY DATA
        col_chart1, col_chart2 = st.columns(2)
    
        with col_chart1:
            st.markdown("### 🎯 Intent Distribution")
            # PIE CHART: Intent breakdown (9 queries → 4 intents)
            intent_df = pd.read_sql("""
            SELECT predicted_intent, COUNT(*) as count
            FROM nlu_history WHERE predicted_intent IS NOT NULL
            GROUP BY predicted_intent ORDER BY count DESC
        """, conn)
        
            if not intent_df.empty:
                fig_pie = px.pie(intent_df, values='count', names='predicted_intent',
                           title="Intent Distribution", hole=0.4)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
    
        with col_chart2:
            st.markdown("### 📊 Confidence Distribution")
        # BAR CHART: Confidence levels (all 100%)
            conf_df = pd.read_sql("""
            SELECT ROUND(confidence*100,0) as conf_pct, COUNT(*) as count
            FROM nlu_history WHERE confidence IS NOT NULL
            GROUP BY conf_pct ORDER BY conf_pct
        """, conn)
        
            if not conf_df.empty:
                fig_bar = px.bar(conf_df, x='conf_pct', y='count', 
                           title="Confidence Levels",
                           labels={'conf_pct': 'Confidence %', 'count': 'Queries'})
                fig_bar.update_xaxes(tickmode='linear', tick0=0, dtick=10)
                st.plotly_chart(fig_bar, use_container_width=True)
     

    # PERFECT TABLE (like your screenshot)
        st.markdown("### Recent Queries")
        recent_df = pd.read_sql("""
        SELECT user_query as "Query", 
               predicted_intent as "Intent", 
               ROUND(confidence*100,0)||'%' as "Confidence",
               substr(timestamp, 1, 10) as "Date"
        FROM nlu_history 
        WHERE predicted_intent IS NOT NULL
        ORDER BY id DESC LIMIT 10
    """, conn)
        st.dataframe(recent_df, use_container_width=True, hide_index=True,column_config={
                    "Query": st.column_config.TextColumn("Query", width="medium"),
                    "Intent": st.column_config.TextColumn("Intent", width="medium"),
                    "Confidence": st.column_config.TextColumn("Confidence", width="small"),
                    "Date": st.column_config.TextColumn("Date", width="small")
                })
        
    with tab3:
        st.markdown("### 🧠 Training Editor")
        left_col, right_col = st.columns([1.3, 1.0])
        # LEFT: Intent Editor + Add Example
        intents_path = "./nlu_engine/intents.json"
        # 🔥 AUTO-CREATE folder & file if missing
        os.makedirs("nlu_engine", exist_ok=True)
         # 🔥 LIVE MEMORY - Examples NEVER LOST!
        if 'live_intents' not in st.session_state:
            st.session_state.live_intents = []
        intents = st.session_state.live_intents
        # Initial load ONLY
        if not intents:
            try:
                with open(intents_path, 'r') as f:
                    data = json.load(f)
                    intents.extend(data.get("intents", []))  # Add, don't replace!
                    st.session_state.live_intents = intents
            except:
                st.session_state.live_intents = []
                pass
        data = {"intents": intents}  # ✅ CRITICAL LINE!

        with left_col:
            # # ULTRA-SAFE JSON load
            # intents = []
            # try:

        
            #     if os.path.exists(intents_path):
            #         with open(intents_path, 'r', encoding='utf-8') as f:
            #             content = f.read().strip()
            #             if content.startswith('{'):
            #                 data = json.loads(content)
            #                 intents = data.get("intents", [])
            #             else:
            #                 raise ValueError("Invalid start")
            #     else:
            #         # CREATE FRESH FILE
            #         data = {"intents": []}
            #         with open(intents_path, 'w', encoding='utf-8') as f:
            #             json.dump(data, f, indent=2)
            #         st.success("✅ Created new intents.json!")
            # except:
            #     # FORCE CREATE
            #     data = {"intents": []}
            #     with open(intents_path, 'w', encoding='utf-8') as f:
            #         json.dump(data, f, indent=2)
            #     intents = []
            #     st.success("✅ Reset intents.json!")
            # # Show current intents
            if intents:
                st.info(f"📊 {len(intents)} intents loaded")
                # Edit each
                for i, intent in enumerate(intents):
                    with st.expander(f"✏️ {intent.get('name', 'New Intent')} ({len(intent.get('examples', []))} examples)"):

                        intent['name'] = st.text_input("Intent Name:", value=intent.get('name', ''), key=f'name_{i}')
                        examples_text = '\n'.join(intent.get('examples', []))
                        new_examples = st.text_area("Training Examples:", value=examples_text, height=120, key=f'ex_{i}')
                        intent['examples'] = [ex.strip() for ex in new_examples.split('\n') if ex.strip()]
            else:
                st.info("👆 Create your first intent!")
            # === ➕ ADD EXAMPLE ===
            st.markdown("---")
            st.markdown("#### ➕ Quick Add Example")
            if len(intents) > 0:
    # Safe index
                    selected_idx = st.selectbox("Select intent:", 
                              range(len(intents)),
                              format_func=lambda i: f"{intents[i].get('name', 'Intent')} ({len(intents[i].get('examples', []))} ex)")
    
                    example_text = st.text_input("New example:", placeholder="show balance")
    
                    if st.button("➕ ADD NOW") and example_text.strip():
        # Add directly to LIVE memory
                        intents[selected_idx]['examples'].append(example_text.strip())
        
        # Save to disk IMMEDIATELY
                        save_data = {"intents": intents}
                        try:
                            with open(intents_path, 'w', encoding='utf-8') as file:
                                json.dump(save_data, file, indent=2)
            
            # Update session
                            st.session_state.live_intents = intents
            
                            st.success(f"✅ Added! Total: {len(intents[selected_idx]['examples'])} examples")
                            st.rerun()
            
                        except Exception as save_error:
                            st.error(f"💾 Save failed: {save_error}")
            else:
                st.warning("⚠️ No intents - create first!")

                    
            #===NEW Intent===
            st.markdown("#### ➕ Create New Intent")
            # with st.form("create_intent"):
            new_intent_name = st.text_input("Intent name:", placeholder="check_balance")
            new_intent_examples = st.text_area("Add 3-5 examples:", height=100, 
                                             placeholder="What's my balance?\nShow account balance\nCheck savings")
            # ✅ FIXED: Calculate ex_list BEFORE if statement
            ex_list = [ex.strip() for ex in new_intent_examples.splitlines() if ex.strip()]
            if st.button("🚀 Create Intent", type="primary") and new_intent_name.strip():
                if len(ex_list) >= 2:
                    intents.append({
            "name": new_intent_name.strip(),
            "examples": ex_list
        })
                    data["intents"] = intents
                    with open(intents_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    st.balloons()
                    st.success(f"✅ '{new_intent_name}' created with {len(ex_list)} examples!")
                    st.rerun()




            # === SAVE & TRAIN ===
            col_save, col_train = st.columns(2)
            with col_save:
                if st.button("💾 Save Changes", use_container_width=True):
                    data["intents"] = intents
                    with open(intents_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    st.success("✅ Changes saved to intents.json!")
            with col_train:
                st.markdown("---")
                st.markdown("### 🚀 Train intent model")
                epochs = st.number_input("Epochs", min_value=1, max_value=20, value=3)
                batch_size = st.number_input("Batch size", min_value=4, max_value=64, value=16)
                lr = st.number_input("Learning rate", min_value=1e-5, max_value=1e-2, value=5e-5, format="%.5f")

                if st.button("Start training"):
                    proc = start_training_subprocess(int(epochs), int(batch_size), float(lr))
                    st.info("Training started. Streaming logs below...")
                    log_lines = []
                    placeholder = st.empty()
                    for line in proc.stdout:
                        log_lines.append(line.rstrip())
                        placeholder.text("\n".join(log_lines[-25:]))
                    proc.wait()
                    if proc.returncode == 0:
                        st.success("✅ Training finished!")
                    else:
                        st.error(f"Training failed (code {proc.returncode}).")

                if LOG_PATH.exists():
                    with st.expander("📄 View latest training.log"):
                        with open(LOG_PATH, "r", encoding="utf-8") as f:
                            st.text(f.read())
            #     st.markdown("### 🎯 Train Model")
            #     epochs = st.slider("Epochs:", 1, 10, 3)
            #     batch_size = st.slider("Batch size:", 8, 32, 16)
            #     lr = st.number_input("Learning rate:", 1e-5, 5e-5, 3e-5, format="%.0e")
            #     if st.button("🚀 Train Model", type="primary", use_container_width=True):
            #         with st.spinner("🔄 Training DistilBERT... (~2-3 min)"):
            #             result = subprocess.run([  # ✅ No local import
            #                 sys.executable, "-m", "nlu_engine.train_intent",
            #                 "--epochs", str(epochs),
            #                 "--batch_size", str(batch_size),  # ✅ Match argparse
            #                 "--lr", str(lr)
            # ], capture_output=True, text=True, timeout=300)
            
            #             if result.returncode == 0:
            #                 st.success("✅ Model trained!")
            #                 st.info("Check: `dir models\\intent_model`")
            #                 st.rerun()
            #             else:
            #                 st.error("Failed:")
            #                 st.code(result.stdout)
            #                 st.code(result.stderr)
                

                #     cmd = [
                #     "python", "nlu_engine/train_intent.py",
                #   "--intents", intents_path,
                #    "--output_dir", "./models/intent_model",
                #    "--epochs", str(epochs),
                #    "--batch_size", str(batch_size),
                #   "--lr", str(lr)
                # ] 
                #     with st.spinner("Training DistilBERT... (~2min)"):
                #         result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
                #     if result.returncode == 0:
                #         st.success("✅ Model trained! Refresh → Real NLU works!")
                #         st.rerun()
                #     else:
                #         st.error("Training failed:")
                #         st.code(result.stderr)
                    
        with right_col:
            st.markdown("### 2️⃣ NLU Visualizer")

            if not model_exists():
                st.warning("⚠️ No trained model. Train one on the left first.")
            else:
                if "intent_classifier" not in st.session_state:
                    try:
                        from nlu_engine.infer_intent import IntentClassifier 
                        st.session_state.intent_classifier = IntentClassifier(str(MODEL_DIR))
                        st.success("✅ Model loaded!")
                    except Exception as e:
                        st.error(f"Could not load model: {e}")
                        st.session_state.intent_classifier = None
                ic = st.session_state.get("intent_classifier", None)
                preset = st.selectbox("Example queries", ["Custom", "Check balance", "Transfer money", "Block card", "Find ATM"])
                example_map = {
                "Check balance": "What is my account balance?",
                "Transfer money": "Transfer 5000 rupees to account 1234567890.",
                "Block card": "Block my debit card immediately.",
                "Find ATM": "Where is the nearest ATM near me?",
            }
                default_text = "Show balance for my savings account, I want to send 1000 rupees to account 9876543210." if preset == "Custom" else example_map[preset]
                user_text = st.text_area("User Query", value=default_text, height=140)
                top_k = st.number_input("Top intents to show", min_value=1, max_value=5, value=4, step=1)
                run = st.button("🔍 Analyze")
                intents_pred = []
                entities = {}
                if run and ic is not None:
                    with st.spinner("Predicting intent and extracting entities..."):
                        intents_pred = ic.predict(user_text, topk=int(top_k))
                        entities = extract_entities(user_text)
                        # ===== FIXED SAFE NLU SAVE =====
                        if intents_pred:  # ✅ SAFETY CHECK - NO CRASH!
                            with get_conn() as nlu_conn:
                                cursor = nlu_conn.cursor()
                                cursor.execute("""
                                INSERT INTO nlu_history (user_query, predicted_intent, confidence)
                                VALUES (?, ?, ?)
                            """, (user_text, intents_pred[0]['intent'], intents_pred[0]['score']))
                                nlu_conn.commit()
                                st.success("✅ Saved to NLU History!")
                        else:
                            st.warning("⚠️ No intent predictions found")
                        
                if intents_pred:
                    col_intent, col_entity = st.columns(2)
                    with col_intent:
                        st.markdown("#### Intent Recognition")
                        st.table({"Intent": [item["intent"] for item in intents_pred], "Score": [f"{item['score']:.2f}" for item in intents_pred]})
                    with col_entity:
                        st.markdown("#### Entity Extraction")
                        if entities:
                            with st.expander("View extracted entities"):
                                for key, vals in entities.items():
                                    icon = ENTITY_ICONS.get(key.lower(), "🔹")
                                    for v in vals:
                                        st.write(f"{icon} **{key.title()}**: {v}")
                        else:
                            st.info("No entities found.")
                    


    










            
        # st.subheader("Edit Training Data (intents.json)")
        # st.info("📝 Coming soon: Edit intents + retrain NLU")
    with tab4:
        st.subheader("Manage FAQs")
        st.info("❓ Add/Edit Q&A pairs for knowledge base")
    with tab5:
        st.subheader("Export Data")
        csv = pd.read_sql("SELECT * FROM chat_history", conn).to_csv(index=False)
        st.download_button("📥 Export Full History", csv, "bankbot_full_history.csv")
    
    st.markdown("---")
    st.caption("👨‍💼 Admin User | Last updated: Now")
    conn.close()


    # ---------- SIMPLE LOGIN GATE ----------
# ---------- SIDEBAR LOGIN + NAV ----------

# 1) Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# 2) Sidebar login UI
with st.sidebar:
    st.markdown(
        """
        <style>
        
        .sb-login-card {
            padding: 18px 16px;
            border-radius: 18px;
            background: linear-gradient(135deg,#22c55e,#0ea5e9);
            box-shadow: 0 12px 30px rgba(15,23,42,0.85);
            border: 1px solid #22c55e55;
        }
        .sb-login-title {
            font-weight: 800;
            font-size: 18px;
            color: #f9fafb;
            margin-bottom: 4px;
        }
        .sb-login-sub {
            font-size: 12px;
            color: #e5e7eb;
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


    if not st.session_state.logged_in:
        st.markdown(
            """
            <div class="sb-login-card">
                <div class="sb-login-title">🔐 BankBot Login</div>
                <div class="sb-login-sub">Please enter your credentials to access the pages.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

   
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username.strip() == "" or password.strip() == "":
                st.error("Please enter account number, username and password.")
            else:
                
                st.session_state.logged_in = True
                st.session_state.username = username.strip()
                st.success(
                        f"Welcome {st.session_state.username}, you can navigate to the pages now."
                )
                
                   
    else:
          
          
          st.write(f"Welcome **{st.session_state.username}** 👋")
          if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

# 3) If not logged in, show only info in main area
if not st.session_state.logged_in:
    st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #22c55e 0, #0f172a 40%, #020617 100%);
        
        color: #e5e7eb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

    st.title("🏦 BankBot Login")
    st.info("📋Please log in from the sidebar to access the pages.")
else:
    # 4) Navigation only after login
    st.sidebar.markdown("### Navigation")
    pages = {
    "🏠Home": "home",
    "🧠User Query": "user_query", 
    "💬Chatbot": "chatbot",
    "🗄️Database": "database",
    "📈Chat History": "chat_history",      # NEW
    "🔧Admin Panel": "admin_panel"         # NEW
}
    page = st.sidebar.selectbox("Go to", list(pages.keys()))


    if page == "🏠Home":
        page_home()
    elif page == "🧠User Query":
        page_user_query()
    elif page == "💬Chatbot":
        page_chatbot()
    elif page == "🗄️Database":
        page_database()
    elif page == "📈Chat History":
        page_chat_history()           # NEW
    elif page == "🔧Admin Panel":
        page_admin_panel()   

 

