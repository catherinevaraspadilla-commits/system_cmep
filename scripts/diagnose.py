"""
Diagnostic script for CMEP backend loading issues.
Run from project root: python scripts/diagnose.py
"""
import sqlite3
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_ROOT = os.path.join(PROJECT_ROOT, "cmep_dev.db")
DB_BACKEND = os.path.join(PROJECT_ROOT, "backend", "cmep_dev.db")

results = []


def check_db(path, label):
    results.append(f"\n=== {label}: {path} ===")
    if not os.path.exists(path):
        results.append("  NOT FOUND")
        return
    size = os.path.getsize(path)
    results.append(f"  Size: {size} bytes")

    try:
        conn = sqlite3.connect(path)

        # Tables
        tables = [t[0] for t in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        results.append(f"  Tables: {tables}")

        # Check pago_solicitud columns
        if "pago_solicitud" in tables:
            cols = [col[1] for col in conn.execute(
                "PRAGMA table_info(pago_solicitud)"
            ).fetchall()]
            results.append(f"  pago_solicitud columns: {cols}")
            has_comentario = "comentario" in cols
            results.append(f"  Has 'comentario' column: {has_comentario}")
            if not has_comentario:
                results.append("  >>> MISSING 'comentario' column! This causes ALL solicitud queries to fail.")
                results.append("  >>> FIXING: Adding column now...")
                conn.execute("ALTER TABLE pago_solicitud ADD COLUMN comentario TEXT")
                conn.commit()
                results.append("  >>> FIXED: 'comentario' column added.")
        else:
            results.append("  pago_solicitud table NOT FOUND")

        # Row counts
        for t in ["users", "servicios", "solicitud_cmep", "pago_solicitud", "sessions"]:
            if t in tables:
                count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                results.append(f"  {t}: {count} rows")

        # Check sessions table for expired sessions
        if "sessions" in tables:
            try:
                expired = conn.execute(
                    "SELECT COUNT(*) FROM sessions WHERE expires_at < datetime('now')"
                ).fetchone()[0]
                results.append(f"  Expired sessions: {expired}")
            except Exception:
                pass

        conn.close()
    except Exception as e:
        results.append(f"  ERROR: {e}")


def check_backend_import():
    results.append("\n=== Backend Import Check ===")
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))
    try:
        start = time.time()
        from app.main import app  # noqa: F401
        elapsed = time.time() - start
        results.append(f"  Import OK ({elapsed:.2f}s)")
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        results.append(f"  Routes: {routes}")
    except Exception as e:
        results.append(f"  IMPORT FAILED: {e}")


def check_bcrypt_speed():
    results.append("\n=== Bcrypt Speed Check ===")
    try:
        import bcrypt
        start = time.time()
        hashed = bcrypt.hashpw(b"test123", bcrypt.gensalt())
        hash_time = time.time() - start
        start = time.time()
        bcrypt.checkpw(b"test123", hashed)
        check_time = time.time() - start
        results.append(f"  Hash time: {hash_time:.3f}s")
        results.append(f"  Check time: {check_time:.3f}s")
        if check_time > 1.0:
            results.append("  >>> SLOW: bcrypt is taking >1s, this slows every login")
    except ImportError:
        results.append("  bcrypt not installed")


# Run checks
print("CMEP Diagnostic Tool")
print("=" * 50)

check_db(DB_ROOT, "Project Root DB (USED BY APP)")
check_db(DB_BACKEND, "Backend Dir DB (NOT used by app)")
check_backend_import()
check_bcrypt_speed()

# Output
output = "\n".join(results)
print(output)

# Also write to file
out_path = os.path.join(PROJECT_ROOT, "diagnostic_result.txt")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(output)
print(f"\nResults saved to: {out_path}")
