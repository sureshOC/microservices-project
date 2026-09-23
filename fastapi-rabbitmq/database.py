import sqlite3

DB_PATH = "orders.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS processed_events (event_id TEXT PRIMARY KEY, processed_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("CREATE TABLE IF NOT EXISTS orders (order_id TEXT PRIMARY KEY, customer_id INTEGER NOT NULL, item TEXT NOT NULL, quantity INTEGER NOT NULL, status TEXT NOT NULL)")

def process_order(event):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("INSERT OR IGNORE INTO processed_events (event_id) VALUES (?)", (event["event_id"],))
        if cursor.rowcount == 0:
            print(f"Duplicate event skipped: {event['event_id']}")
            return False
        conn.execute("INSERT INTO orders (order_id, customer_id, item, quantity, status) VALUES (?, ?, ?, ?, ?)", (event["order_id"], event["customer_id"], event["item"], event["quantity"], "PROCESSED"))
        print(f"Order saved to database: {event['order_id']}")
        return True
