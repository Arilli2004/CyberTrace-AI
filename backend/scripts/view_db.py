import sqlite3
import os
import sys

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cybertrace.db"))
if not os.path.exists(db_path):
    db_path = os.path.abspath(os.path.join(os.getcwd(), "backend", "cybertrace.db"))

print("=" * 70)
print("  CYBERTRACE AI — DATABASE INSPECTOR & TABLE OVERVIEW")
print("=" * 70)
print(f"Database File: {db_path}\n")

if not os.path.exists(db_path):
    print(f"[ERROR] Database file not found at '{db_path}'.")
    print("Please run the project first to initialize the database.")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = [r[0] for r in cursor.fetchall()]

if not tables:
    print("No tables found in database.")
    sys.exit(0)

print(f"Found {len(tables)} Tables in Database:\n")

for table in sorted(tables):
    cursor.execute(f"SELECT COUNT(*) FROM `{table}`;")
    count = cursor.fetchone()[0]
    print(f"  * Table: {table:<30} | Total Records: {count}")

print("\n" + "-" * 70)
print("SAMPLE RECORDS PREVIEW:")
print("-" * 70)

# Preview Key Tables
preview_tables = ["users", "cases", "evidence", "events", "normalized_events", "graph_nodes", "graph_edges", "chain_of_custody_logs", "ai_reports"]

for tbl in preview_tables:
    if tbl in tables:
        cursor.execute(f"SELECT COUNT(*) FROM `{tbl}`;")
        cnt = cursor.fetchone()[0]
        print(f"\n[TABLE] `{tbl}` ({cnt} rows)")
        
        cursor.execute(f"PRAGMA table_info(`{tbl}`);")
        cols = [c[1] for c in cursor.fetchall()]
        print("  Columns: " + ", ".join(cols[:6]) + ("..." if len(cols) > 6 else ""))
        
        cursor.execute(f"SELECT * FROM `{tbl}` LIMIT 3;")
        rows = cursor.fetchall()
        if rows:
            for r in rows:
                print("  -", str(r)[:110] + ("..." if len(str(r)) > 110 else ""))
        else:
            print("  (Table is currently empty)")

conn.close()
print("\n" + "=" * 70)
