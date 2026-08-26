import sqlite3
import os

# find .db files automatically so you don't have to guess the name
db_files = [f for f in os.listdir('.') if f.endswith('.db')]
print("Found database files:", db_files)
print()

if not db_files:
    print("No .db file found in this folder. Run this script from your project folder.")
else:
    db_name = db_files[0]  # uses the first .db file found
    print(f"Reading schema from: {db_name}\n")
    
    conn = sqlite3.connect(db_name)
    cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    
    for row in cursor:
        print(row[0])
        print()
    
    conn.close()