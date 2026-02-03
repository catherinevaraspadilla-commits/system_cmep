"""
Fix: add missing 'comentario' column to pago_solicitud in the correct DB,
and remove the extra DB that shouldn't exist.
Run from project root: python scripts/fix_db.py
"""
import sqlite3
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORRECT_DB = os.path.join(PROJECT_ROOT, "cmep_dev.db")
WRONG_DB = os.path.join(PROJECT_ROOT, "backend", "cmep_dev.db")

# 1. Fix the correct database
print(f"Correct DB: {CORRECT_DB}")
if os.path.exists(CORRECT_DB):
    conn = sqlite3.connect(CORRECT_DB)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(pago_solicitud)").fetchall()}
    print(f"  Current columns: {cols}")
    if "comentario" not in cols:
        conn.execute("ALTER TABLE pago_solicitud ADD COLUMN comentario TEXT")
        conn.commit()
        print("  FIXED: Added 'comentario' column")
    else:
        print("  OK: 'comentario' column already exists")
    conn.close()
else:
    print("  NOT FOUND!")

# 2. Delete the wrong database
print(f"\nWrong DB: {WRONG_DB}")
if os.path.exists(WRONG_DB):
    os.remove(WRONG_DB)
    print("  DELETED")
else:
    print("  Already gone")

print("\nDone.")

# Check users
conn = sqlite3.connect(CORRECT_DB)
rows = conn.execute("SELECT user_id, user_email, estado FROM users").fetchall()
print(f"\nUsers ({len(rows)}):")
for r in rows:
    print(f"  {r}")
conn.close()
