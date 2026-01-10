# test_create_account.py
from database.bank_curd import create_account

if __name__ == "__main__":
    msg = create_account(
        name="Sai",
        acc_no="123456789",
        acc_type="savings",
        balance=50000,
        password="123456"
    )
    print(msg)
