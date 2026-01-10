# database/bank_crud.py
import sqlite3  

from database.db import get_conn
from database.security import hash_password, verify_password
from datetime import datetime

def create_account(name, acc_no, acc_type, balance, password):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("INSERT OR IGNORE INTO users(name) VALUES (?)", (name,))
    pwd_hash = hash_password(password)

    cur.execute("""
    INSERT INTO accounts(account_number, user_name, account_type, balance, password_hash)
    VALUES (?, ?, ?, ?, ?)
    """, (acc_no, name, acc_type, balance, pwd_hash))

    conn.commit() 
    conn.close()

def get_account(acc_no):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT account_number, user_name, account_type, balance, password_hash
    FROM accounts WHERE account_number=?
    """, (acc_no,))
    row = cur.fetchone()
    conn.close()
    return row

def list_accounts():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT account_number, user_name FROM accounts")
    rows = cur.fetchall()
    conn.close()
    return rows

def transfer_money(from_acc, to_acc, amount, password):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT balance, password_hash FROM accounts WHERE account_number=?", (from_acc,))
    row = cur.fetchone()
    if not row:
        return "❌ Invalid sender account"

    balance, pwd_hash = row
    if not verify_password(password, pwd_hash):
        return "❌ Incorrect password"

    if balance < amount:
        return "❌ Insufficient balance"

    # Transaction (ACID)
    cur.execute("UPDATE accounts SET balance = balance - ? WHERE account_number=?", (amount, from_acc))
    cur.execute("UPDATE accounts SET balance = balance + ? WHERE account_number=?", (amount, to_acc))

    cur.execute("""
    INSERT INTO transactions(from_account, to_account, amount, timestamp)
    VALUES (?, ?, ?, ?)
    """, (from_acc, to_acc, amount, datetime.now().isoformat()))

    conn.commit()
    conn.close()
    return "✅ Transfer Successful"

def check_balance(acc_no, password):
    conn = get_conn()
    cur = conn.cursor()
    print("DEBUG acc_no =", repr(acc_no))
    print("DEBUG password =", repr(password))  # add this line

    # get balance and hashed password for this account
    cur.execute(
        "SELECT balance, password_hash FROM accounts WHERE account_number = ?",
        (acc_no,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return "X Account not found."

    balance, pwd_hash = row

    # verify plain password with stored hash
    if not verify_password(password, pwd_hash):
        return "X Incorrect password."

    return f"Your current balance is {balance} rupees."
def get_balance(acc_no: str) -> int | None:
    conn = sqlite3.connect("bankbot.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM accounts WHERE account_number= ?", (acc_no,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

