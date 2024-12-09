from Backend.database import DatabaseManager
import sqlite3
import os



strategy_id = "TEST"

def insert_test_order(db_manager, order_id,symbol,quantity,side,status,opened_at,avg_price):
    db_manager.insert_order(order_id,symbol,quantity,side,status,strategy_id,opened_at,avg_price)
    db_manager.conn.commit()

def delete_test_order(db_manager, order_id):
    db_manager.delete_order(order_id)
    db_manager.conn.commit()

def delete_all_test_orders(db_manager):
    db_manager.delete_all_test_orders()
    db_manager.conn.commit()

def main():
    conn = sqlite3.connect('stock_tracker.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM strategies""")
    row = cursor.fetchone()
    print(row)

if __name__ == '__main__':
    main()








