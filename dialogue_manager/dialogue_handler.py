# dialogue_manager/dialogue_handler.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_conn 
# CORRECT (absolute path from project root):
from experiments.llm_groq import groq_answer
from nlu_engine.entity_extractor import extract as extract_entities


  # ADD THIS


from nlu_engine.entity_extractor import extract as extract_entities
from database.bank_curd import (
    get_balance,
    get_account,
    list_accounts,
    transfer_money,
    check_balance,      # for balance flow
        # for transfer receiver list
)
def log_interaction(user_text, intent, confidence=0.85, entities=None, success=True):
    """Log every interaction with REAL intent from NLU"""
    from database.db import get_conn
    conn = get_conn()
    
    real_intent = intent if intent else "unknown"
    
    conn.execute("""
        INSERT INTO chat_history (user_query, predicted_intent, confidence, success)
        VALUES (?, ?, ?, ?)
    """, (user_text, real_intent, confidence, success))
    conn.commit()
    conn.close()


class DialogueManager:
    def __init__(self):
        self.reset()

    def reset(self):
        # overall conversation state
        self.in_flow = False          # True when in a multi‑turn flow
        self.active_intent = None     # locked intent inside a flow

        # slots for current flow
        self.awaiting = None          # which piece we are waiting for
        self.slots = {}               # e.g. {"from_account": "...", "amount": 1000, ...}

        # fallback tracking
        self.fallback_count = 0

    # ================= MAIN HANDLER =================
    def handle(self, intent, entities, user_text: str) -> str:
        # ---------- INTENT LOCK ----------
        if self.in_flow:
            # keep using the active intent while in flow
            intent = self.active_intent
        else:
            # new turn, new intent
            
            self.active_intent = intent
        # ✅ ADD ENTITY COUNTING HERE:
        bank_entities_extracted = extract_entities(user_text)
        banking_entities = ['account_number', 'amount', 'location', 'atm']
        
        # ---------- FALLBACK ----------
        if intent is None:
            # self.fallback_count += 1
            # if self.fallback_count >= 3:
            #     self.reset()
            #     return "I am unable to help on this. Let me connect you to a human agent."
            # return "Sorry, I didn't understand. Please try again."
            prompt = ("You are BankBot, a helpful banking assistant.\n"
        "Answer clearly in simple English. Do not perform real transactions.\n\n"
        f"User: {user_text}\n\nAnswer:"
    )       
            answer=groq_answer(prompt)
            log_interaction(user_text, intent, 0.85, entities)  # Uses REAL intent!
            #self.fallback_count = 0
            # conn = get_conn()
            # conn.execute("""
            #    INSERT INTO chat_history (user_query, predicted_intent, confidence, success)
            #    VALUES (?, ?, ?, ?)
            #    """, (user_text, "llm_fallback", 0.85, True))
            # conn.commit()
            # conn.close()
            return answer


        # ---------- GREET ----------
        if intent == "greet":
            log_interaction(user_text, intent, 1.0, entities)

            # self.reset()
            # conn = get_conn()
            # conn.execute("INSERT INTO chat_history (user_query, predicted_intent, confidence) VALUES (?, ?, ?)", (user_text, "greet", 1.0))
            # conn.commit()
            # conn.close()

            return "Hello 👋 How can I help you today?"

        # ---------- TRANSFER MONEY ----------
        if intent == "transfer_money":
            self.in_flow = True
            return self.handle_transfer_flow(entities, user_text)

        # ---------- CHECK BALANCE ----------
        if intent == "check_balance":
            self.in_flow = True
            return self.handle_check_balance(entities, user_text)

        # ---------- CARD BLOCK ----------
        if intent == "card_block":
            self.in_flow = True
            return self.handle_card_block(entities, user_text)

        
    # ================= GENERAL QA (GROQ) =================
        prompt = (
        "You are BankBot, a helpful banking assistant.\n"
        "Answer clearly in simple English. Do not perform real transactions.\n\n"
        f"User: {user_text}\n\nAnswer:"
    )
        answer=groq_answer(prompt)
        self.fallback_count=0
        conn = get_conn()
        real_intent = intent if intent else "unknown"
        conn.execute("INSERT INTO chat_history (user_query, predicted_intent, confidence,success) VALUES (?, ?, ?, ?)", (user_text,real_intent, 0.85, True))
        conn.commit()
        conn.close()

        return answer
    # unknown intent (should not normally reach here)

        # self.reset()
        # return "Sorry, I didn't understand. Please try again."

    # ================= TRANSFER FLOW =================
    def handle_transfer_flow(self, entities, user_text: str) -> str:
        # normalize entities: list -> dict
        if isinstance(entities, list):
            try:
                entities = dict(entities)
            except Exception:
                entities = {}
        elif entities is None:
            entities = {}

        # first turn
        if self.awaiting is None:
            self.in_flow = True
            self.awaiting = "from_account"
            self.slots = {
                "from_account": entities.get("account_number"),
                "amount": entities.get("amount"),
                "password": None,
                "to_account": None,
            }

            if not self.slots["from_account"]:
                return "Please enter your account number to start the transfer."

            if not self.slots["amount"]:
                self.awaiting = "amount"
                return "How much would you like to transfer?"

            self.awaiting = "password"
            return "Please enter your transaction password."

        # waiting for source account
        if self.awaiting == "from_account":
            acc = user_text.strip()
            if not acc:
                return "Please enter a valid account number."
            self.slots["from_account"] = acc

            if not self.slots.get("amount"):
                self.awaiting = "amount"
                return "How much would you like to transfer?"

            self.awaiting = "password"
            return "Please enter your transaction password."

        # waiting for amount
        if self.awaiting == "amount":
            ents = extract_entities(user_text)
            amt = ents.get("amount")
            if not amt:
                return "Please enter a valid amount."
            self.slots["amount"] = amt
            self.awaiting = "password"
            return "Please enter your transaction password."

        # waiting for password
        if self.awaiting == "password":
            pwd = user_text.strip()
            if not pwd:
                return "Please enter your transaction password."
            self.slots["password"] = pwd
            self.awaiting = "to_account"
            return "Please enter receiver account number."

        # waiting for receiver account
        if self.awaiting == "to_account":
            ents = extract_entities(user_text)
            to_acc = ents.get("account_number") or user_text.strip()
            if not to_acc:
                return "Please enter a valid receiver account number."
            self.slots["to_account"] = to_acc

            # perform transfer using DB
            src = self.slots["from_account"]
            amt_slot = self.slots.get("amount")
            if amt_slot is None:
                self.reset()
                return "Amount missing in transfer flow. Please start again."
            # amount can be list or str; normalise to int
            if isinstance(amt_slot, list):
                  amt_slot = amt_slot[0]
            amt = int(amt_slot)
            pwd = self.slots["password"]
            print("DEBUG transfer:", src, "->", to_acc, "amt", amt, "pwd", pwd)
            msg = transfer_money(src, to_acc, amt, pwd)
            log_interaction(user_text, "transfer_money", 0.95, entities, success=("✅" in msg))
            # conn = get_conn()
            # conn.execute("INSERT INTO chat_history (user_query, predicted_intent, confidence, success) VALUES (?, ?, ?, ?)", 
            #  (user_text, "transfer_money", 0.95, True))
            # conn.commit()
            # conn.close()

            self.reset()
            return msg

        # safety fallback
        self.reset()
        return "Something went wrong in the transfer flow. Please start again."

    # ================= CHECK BALANCE FLOW =================
    def handle_check_balance(self, entities, user_text: str) -> str:
        print("DEBUG awaiting =", self.awaiting, "user_text =", repr(user_text))

    # 1) Just entered the flow: ask for account, don't save anything yet
        if self.awaiting is None:
            self.in_flow = True
            self.awaiting = "account"
            return "Please enter your account number to check balance."

    # 2) User is now giving account number
        if self.awaiting == "account":
        # Save the account number from **this** turn
            self.slots["acc_no"] = user_text.strip()
            print("DEBUG acc_no from DM =", repr(self.slots["acc_no"]))
            self.awaiting = "account_password"
            return "Please enter your password."

    # 3) User is now giving password
        if self.awaiting == "account_password":
            self.slots["password"] = user_text.strip()
            print("DEBUG password from DM =", repr(self.slots["password"]))

            acc_no = self.slots.get("acc_no")
            password = self.slots.get("password")
            print("DEBUG acc_no =", repr(acc_no))
            print("DEBUG password =", repr(password))

            # NEW: read real balance from DB
            bal = get_balance(acc_no)
            self.reset()
            conn = get_conn()
            conn.execute("INSERT INTO chat_history (user_query, predicted_intent, confidence) VALUES (?, ?, ?)", (user_text, "check_balance", 0.95))
            conn.commit()
            conn.close()

            if bal is None:
              
              return f"Account {acc_no} not found."
            return f"Your balance for account {acc_no} is {bal} Rupees."



    # ================= CARD BLOCK FLOW (SIMPLE) =================
    def handle_card_block(self, entities, user_text: str) -> str:
        self.reset()
        return "Your card has been blocked. If this was not you, please contact customer care immediately."