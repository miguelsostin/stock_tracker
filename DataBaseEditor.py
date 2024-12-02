from Backend.database import DatabaseManager
import os

db_manager = DatabaseManager()

cursor = db_manager.conn.cursor()

strategy_id = "TEST"

def insert_test_order(order_id,symbol,quantity,side,status,opened_at,avg_price):
    db_manager.insert_order(order_id,symbol,quantity,side,status,strategy_id,opened_at,avg_price)
    db_manager.conn.commit()

def delete_test_order(order_id):
    db_manager.delete_order(order_id)
    db_manager.conn.commit()

def delete_all_test_orders():
    db_manager.delete_all_test_orders()
    db_manager.conn.commit()

def main():
    db_manager.conn.commit()


if __name__ == '__main__':
    main()








