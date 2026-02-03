"""
Lambda para limpieza de sesiones expiradas.
Ejecutada via EventBridge cada 6 horas.

Variables de entorno requeridas:
  DB_HOST  — RDS endpoint
  DB_USER  — usuario MySQL (cmep_user)
  DB_PASS  — password MySQL
  DB_NAME  — nombre de la BD (cmep_prod)
"""

import os
import pymysql


def handler(event, context):
    conn = pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        database=os.environ["DB_NAME"],
    )
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE expires_at < NOW()")
            deleted = cur.rowcount
        conn.commit()
        print(f"Sesiones expiradas eliminadas: {deleted}")
        return {"ok": True, "deleted_sessions": deleted}
    finally:
        conn.close()
