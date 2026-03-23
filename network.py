import sqlite3
import time
import random
from datetime import datetime

DB_NAME = "energy_data.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS records 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         timestamp TEXT, 
                         energy REAL)''')
    print("Database Initialized.")

def run_simulation():
    init_db()
    print("Starting Live Data Stream... (Press Ctrl+C to stop)")
    
    while True:
        # Generate realistic energy data (between 40 and 95 kWh)
        energy_value = round(random.uniform(45.0, 92.0), 2)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("INSERT INTO records (timestamp, energy) VALUES (?, ?)", 
                             (now, energy_value))
            print(f"📡 [SENT] Time: {now.split()[1]} | Load: {energy_value} kWh")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(2) # Sends a new reading every 2 seconds

if __name__ == "__main__":
    run_simulation()