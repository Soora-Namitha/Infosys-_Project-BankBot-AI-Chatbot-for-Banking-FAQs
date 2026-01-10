"""
main_app.py - FIXED VERSION
Streamlit UI for BANKBOT NLU: Left trainer + Right visualizer + SAFE NLU History
"""

import streamlit as st
import os
import json
import sys
import subprocess
from pathlib import Path
import pandas as pd
from database.db import init_db, get_conn  # FIXED: Proper imports

# Initialize DB on startup
init_db()

st.session_state.pop("intent_classifier", None)

# Make local packages importable
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from nlu_engine.infer_intent import IntentClassifier  # noqa: E402
from nlu_engine.entity_extractor import extract as extract_entities  # noqa: E402

ENTITY_ICONS = {
    "amount": "💰",
    "account_number": "🏦",
    "name": "👤",
    "date": "📅",
    "time": "⏰",
    "location": "📍",
}

# ----------------------- Paths -----------------------
INTENTS_PATH = BASE_DIR / "nlu_engine" / "intents.json"
MODEL_DIR = BASE_DIR / "models" / "intent_model"
LOG_PATH = BASE_DIR / "models" / "training.log"
os.makedirs(MODEL_DIR.parent, exist_ok=True)

# -------------------- Page config --------------------
st.set_page_config(page_title="BankBot NLU", layout="wide", page_icon="💳")

# --- Global styling ---
st.markdown("""
<style>
.app-title {font-size: 55px; font-weight: 600; letter-spacing: 0.0em; text-transform: uppercase; color: #60A5FA; margin-bottom: 0.3rem;}
.app-subtitle {font-size: 20px; margin-bottom: 1.4rem;}
.app-subtitle-name {font-weight: 800; color: #60A5FA;}
.stButton>button {border-radius: 6px; background-color: #0EA5E9; color: white; border: none;}
.stButton>button:hover {background-color: #0369A1;}
.block-container {padding-top: 1.2rem; padding-bottom: 1.2rem;}
.stApp {background-color: #0f1728;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-title">BankBot NLU – Intent & Entity Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle"><span class="app-subtitle-name">Soora Namitha</span> • Train intents and test your NLU model</div>', unsafe_allow_html=True)

# --------------------- Sidebar -----------------------
with st.sidebar:
    st.header("⚙️ Controls")
    st.markdown("Use this panel to configure training and view help.")
    st.markdown("---")
    st.markdown("**Status**")
    if os.path.isdir(MODEL_DIR) and any(MODEL_DIR.iterdir()):
        st.success("✅ Trained intent model found.")
    else:
        st.warning("⚠️ No trained model yet.")
    st.markdown("---")
    if st.checkbox("Show quick help", value=True):
        st.info("1. Edit or add intents on the left.\n2. Train the model.\n3. Test queries on the right.")

# --------------------- Utilities ---------------------
def load_intents_file() -> dict:
    if not INTENTS_PATH.exists():
        return {"intents": []}
    with open(INTENTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_intents_file(data: dict) -> None:
    with open(INTENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def model_exists() -> bool:
    return os.path.isdir(MODEL_DIR) and any(MODEL_DIR.iterdir())

def start_training_subprocess(epochs: int, batch_size: int, lr: float) -> subprocess.Popen:
    cmd = [
        sys.executable, str(BASE_DIR / "nlu_engine" / "train_intent.py"),
        "--intents", str(INTENTS_PATH), "--model_name", "distilbert-base-uncased",
        "--output_dir", str(MODEL_DIR), "--epochs", str(epochs),
        "--batch_size", str(batch_size), "--lr", str(lr),
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

# ---------------------- TABS -----------------------
tab1, tab2 = st.tabs(["👈 Edit & Train", "📊 NLU History"])

with tab1:
    left_col, right_col = st.columns([1.3, 1.0])

    # ===================== Left: Trainer =====================
    with left_col:
        st.markdown("### 1️⃣ Edit & Train Intents")
        data = load_intents_file()
        intents = data.get("intents", [])

        for idx, intent in enumerate(intents):
            name = intent.get("name", f"intent_{idx}")
            examples = intent.get("examples", [])
            with st.expander(f"✏️ {name} ({len(examples)} examples)", expanded=False):
                new_name = st.text_input("Intent name", value=name, key=f"name_{idx}")
                examples_text = "\n".join(examples)
                new_examples_text = st.text_area("Examples (one per line)", value=examples_text, height=150, key=f"examples_{idx}")
                intents[idx]["name"] = new_name
                intents[idx]["examples"] = [line.strip() for line in new_examples_text.split("\n") if line.strip()]

        st.markdown("---")
        st.markdown("#### ➕ Create new intent")
        with st.form("new_intent_form"):
            new_intent_name = st.text_input("New intent name")
            new_intent_examples_raw = st.text_area("Examples (one per line)", height=150, 
                                                 placeholder="Example:\nCheck my balance\nHow much money is in my account\n...")
            submitted_new = st.form_submit_button("Add intent")

        if submitted_new:
            cleaned_name = new_intent_name.strip()
            if not cleaned_name:
                st.error("Please enter an intent name.")
            else:
                existing_names = {it.get("name", "") for it in intents}
                if cleaned_name in existing_names:
                    st.error(f"Intent '{cleaned_name}' already exists.")
                else:
                    examples = [line.strip() for line in new_intent_examples_raw.splitlines() if line.strip()]
                    if not examples:
                        st.error("Please add at least one example sentence.")
                    else:
                        intents.append({"name": cleaned_name, "examples": examples})
                        save_intents_file({"intents": intents})
                        st.success(f"Intent '{cleaned_name}' added!")

        if st.button("💾 Save all intents.json"):
            save_intents_file({"intents": intents})
            st.success("intents.json saved.")

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

    # ===================== Right: NLU Tester =====================
    with right_col:
        st.markdown("### 2️⃣ NLU Visualizer")
        if not model_exists():
            st.warning("⚠️ No trained model. Train one on the left first.")
        else:
            if "intent_classifier" not in st.session_state:
                try:
                    st.session_state.intent_classifier = IntentClassifier(str(MODEL_DIR))
                except Exception as e:
                    st.error(f"Could not load model: {e}")
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

with tab2:
    st.markdown("### 🗂️ NLU History (Rasa Tests Only)")
    with get_conn() as conn:  # ✅ FIXED: Proper connection
        nlu_history = pd.read_sql("""
            SELECT user_query as "Query", 
                   predicted_intent as "Intent", 
                   ROUND(confidence*100,0)||'%' as "Confidence",
                   substr(timestamp, 1, 10) as "Date"
            FROM nlu_history 
            ORDER BY id DESC LIMIT 20
        """, conn)
    
    st.dataframe(nlu_history, use_container_width=True, hide_index=True, column_config={
        "Query": st.column_config.TextColumn("Query", width="medium"),
        "Intent": st.column_config.TextColumn("Intent", width="medium"),
        "Confidence": st.column_config.TextColumn("Confidence", width="small"),
        "Date": st.column_config.TextColumn("Date", width="small")
    })
