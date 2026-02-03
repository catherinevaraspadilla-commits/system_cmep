"""Quick DB health check script."""
import sqlite3
import pathlib
import sys

db_path = pathlib.Path(__file__).parent.parent / "backend" / "cmep_dev.db"
out_path = pathlib.Path(__file__).parent.parent / "db_check_result.txt"

lines = []

if not db_path.exists():
    lines.append(f"DB NOT FOUND at {db_path}")
else:
    lines.append(f"DB EXISTS at {db_path} ({db_path.stat().st_size} bytes)")

    conn = sqlite3.connect(str(db_path))

    # Tables
    tables = [t[0] for t in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    lines.append(f"TABLES: {tables}")

    # pago_solicitud columns
    if "pago_solicitud" in tables:
        cols = [col[1] for col in conn.execute(
            "PRAGMA table_info(pago_solicitud)"
        ).fetchall()]
        lines.append(f"pago_solicitud COLUMNS: {cols}")
        has_comentario = "comentario" in cols
        lines.append(f"Has 'comentario' column: {has_comentario}")
    else:
        lines.append("pago_solicitud table NOT FOUND")

    # Count records
    for t in ["pago_solicitud", "solicitud_cmep", "users", "servicios"]:
        if t in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            lines.append(f"  {t}: {count} rows")

    conn.close()

result = "\n".join(lines)
out_path.write_text(result, encoding="utf-8")
print(result)
