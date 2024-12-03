from Backend.database import DatabaseManager
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
    db_manager = DatabaseManager()
    delete_test_order(db_manager,"7ffa4942-57e0-4d3f-9db3-a036b86ad26d")

if __name__ == '__main__':
    main()








