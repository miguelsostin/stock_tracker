import sqlite3
from sqlite3 import Error
import threading
import os
from alpaca.trading.client import Position


class DatabaseManager:
    def __init__(self, db_file='stock_tracker.db'):
        self.db_file = db_file
        self.local = threading.local()
        self.connect_to_db()

    def connect_to_db(self):
        self.local.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.create_tables()

    @property
    def conn(self):
        if not hasattr(self.local, 'conn'):
            self.connect_to_db()
        return self.local.conn


    def create_tables(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                    id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    quantity FLOAT NOT NULL,
                    side TEXT NOT NULL,
                    status TEXT NOT NULL,
                    strategy_id TEXT,
                    opened_at DATETIME NOT NULL,
                    avg_price FLOAT)
                     """)

            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS active_positions(
                    symbol TEXT PRIMARY KEY,
                    quantity FLOAT NOT NULL,
                    avg_price FLOAT NOT NULL,
                    market_value FLOAT NOT NULL,
                    p_l FLOAT NOT NULL,
                    current_price FLOAT NOT NULL,
                    strategy_id TEXT,
                    side TEXT NOT NULL)
                    """)

            cursor.execute("""
                        CREATE TABLE IF NOT EXISTS strategies (
                            strategy_id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            description TEXT,
                            parameters TEXT)
                        """)
        ###PARAMETERS will be a JSON object containing the parameters for the strategy.
        # Create performance table
            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id TEXT,
                    date DATE NOT NULL,
                    net_profit FLOAT,
                    total_trades INTEGER,
                    open_positions INTEGER,
                    FOREIGN KEY(strategy_id) REFERENCES strategies(strategy_id))
                    """)

            self.conn.commit()
            print("Tables created successfully.")
        except Error as e:
            print(f"Error creating tables: {e}")

    def create_indices(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_symbol ON trades (symbol);""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_status ON trades (status);""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_strategy_id ON trades (strategy_id);""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS idx_symbol ON active_positions (symbol);""")
            self.conn.commit()
            print("Indices created successfully.")
        except Error as e:
            print(f"Error creating indices: {e}")

    def close_connection(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    def insert_order(self, order_id, symbol, quantity, side, status, strategy_id, opened_at, avg_price=None):
        """Insert a new order into the trades table."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO trades (id, symbol, quantity, side, status, strategy_id, opened_at, avg_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_id, symbol, quantity, side, status, strategy_id, opened_at, avg_price))
            self.conn.commit()
            print(f"Order {order_id} inserted successfully.")
        except sqlite3.IntegrityError as e:
            print(f"Error inserting order {order_id}: {e}")
        except Error as e:
            print(f"Error inserting order {order_id}: {e}")

    def update_order(self, order_id, status = None, avg_price = None):
        try:
            cursor = self.conn.cursor()
            # Build the update query dynamically based on provided fields
            fields = []
            params = []
            if status is not None:
                fields.append("status = ?")
                params.append(status)
            if avg_price is not None:
                fields.append("avg_price = ?")
                params.append(avg_price)
            if not fields:
                print(f"No fields to update for order {order_id}.")
                return
            params.append(order_id)
            query = f"""
                        UPDATE trades
                        SET {', '.join(fields)}
                        WHERE id = ?
                    """
            cursor.execute(query, params)
            self.conn.commit()
            print(f"Order {id} updated successfully.")
        except Error as e:
            print(f"Error updating order {id}: {e}")

    def update_active_position(self,symbol, position: Position):
        """Update the active position for a symbol, uses alpaca-py Position dict as input"""
        if not position:
            self.delete_position(symbol)
        if position.qty == 0:
            self.delete_position(symbol)
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE active_positions
                SET quantity = ?, avg_price = ?, market_value = ?, p_l = ?, current_price = ?
                WHERE symbol = ?
            """, (position.qty, position.avg_entry_price, position.market_value, position.unrealized_pl, position.current_price, symbol))
            self.conn.commit()
            print(f"Position {symbol} updated successfully.")
        except Error as e:
            print(f"Error updating position {symbol}: {e}")

    def insert_strategy(self, strategy_id, name, description=None, parameters=None):
        """Insert a new trading strategy."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO strategies (strategy_id, name, description, parameters)
                VALUES (?, ?, ?, ?)
            """, (strategy_id, name, description, parameters))
            self.conn.commit()
            print(f"Strategy {strategy_id} inserted successfully.")
        except sqlite3.IntegrityError as e:
            print(f"Error inserting strategy {strategy_id}: {e}")
        except Error as e:
            print(f"Error inserting strategy {strategy_id}: {e}")

    def update_performance(self, strategy_id, date, net_profit, total_trades):
        """Update or insert performance metrics for a strategy on a given date."""
        try:
            cursor = self.conn.cursor()
            # Check if an entry already exists
            cursor.execute("""
                SELECT id FROM performance WHERE strategy_id = ? AND date = ?
            """, (strategy_id, date))
            result = cursor.fetchone()
            if result:
                # Update existing entry
                cursor.execute("""
                    UPDATE performance
                    SET net_profit = ?, total_trades = ?
                    WHERE id = ?
                """, (net_profit, total_trades, result[0]))
            else:
                # Insert new entry
                cursor.execute("""
                    INSERT INTO performance (strategy_id, date, net_profit, total_trades)
                    VALUES (?, ?, ?, ?)
                """, (strategy_id, date, net_profit, total_trades))
            self.conn.commit()
            print(f"Performance for strategy {strategy_id} on {date} updated successfully.")
        except Error as e:
            print(f"Error updating performance for strategy {strategy_id}: {e}")

    def get_active_positions(self):
        """Retrieve all active positions."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM active_positions
            """)
            positions = cursor.fetchall()
            return positions
        except Error as e:
            print(f"Error retrieving active positions: {e}")
            return []

    def get_order_by_id(self, order_id):
        """Retrieve an order by its ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM trades WHERE id = ?
            """, (order_id,))
            order = cursor.fetchone()
            return order
        except Error as e:
            print(f"Error retrieving order {order_id}: {e}")
            return None

    def get_orders_by_status(self, status):
        """Retrieve orders by their status."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM trades WHERE status = ?
            """, (status,))
            orders = cursor.fetchall()
            return orders
        except Error as e:
            print(f"Error retrieving orders with status {status}: {e}")
            return []

    def delete_order(self, order_id):
        """Delete an order by its ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM trades WHERE id = ?
            """, (order_id,))
            self.conn.commit()
            print(f"Order {order_id} deleted successfully.")
        except Error as e:
            print(f"Error deleting order {order_id}: {e}")

    def delete_position(self, symbol):
        """Delete an active position by its symbol."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM active_positions WHERE symbol = ?
            """, (symbol,))
            self.conn.commit()
            print(f"Position {symbol} deleted successfully.")
        except Error as e:
            print(f"Error deleting position {symbol}: {e}")

    def delete_all_test_orders(self):
        """Delete all orders."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM trades WHERE strategy_id = 'TEST'
            """)
            self.conn.commit()
            print("All test orders deleted successfully.")
        except Error as e:
            print(f"Error deleting all orders: {e}")


