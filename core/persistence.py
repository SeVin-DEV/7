import oracledb
import os
import json

# --- DB CONNECTION CONFIG ---
DB_CONFIG = {
    "user": "ADMIN",
    "password": "1903313.Cb237527",
    "dsn": "svnbrain_high",
    "wallet_path": "/root/wallet",
    "wallet_pass": "1903313.Cb"
}

def get_brain_connection():
    """Establishes a secure mTLS connection to the 26ai instance."""
    return oracledb.connect(
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dsn=DB_CONFIG["dsn"],
        config_dir=DB_CONFIG["wallet_path"],
        wallet_location=DB_CONFIG["wallet_path"],
        wallet_password=DB_CONFIG["wallet_pass"]
    )

def get_identity_content(filename="soul.md"):
    """Fetches core identity from the identity_matrix table."""
    conn = get_brain_connection()
    try:
        with conn.cursor() as cur:
            key = filename.split(".")[0]
            cur.execute("SELECT content FROM identity_matrix WHERE identity_key = :1", [key])
            row = cur.fetchone()
            return row[0] if row else "# Identity not found in DB"
    except Exception as e:
        return f"# DB_ERROR: {str(e)}"
    finally:
        conn.close()

def load_json(table_name, default_value=[]):
    """Queries a DB table instead of a local JSON file."""
    conn = get_brain_connection()
    try:
        table = table_name.split(".")[0]
        with conn.cursor() as cur:
            cur.execute(f"SELECT json_data FROM {table} ORDER BY id ASC")
            rows = cur.fetchall()
            return [json.loads(row[0]) for row in rows] if rows else default_value
    except Exception:
        return default_value
    finally:
        conn.close()

def save_json(table_name, data):
    """Inserts/Appends data into the 26ai brain tables."""
    conn = get_brain_connection()
    try:
        table = table_name.split(".")[0]
        with conn.cursor() as cur:
            if isinstance(data, list) and len(data) > 0:
                payload = data[-1]
            else:
                payload = data
            cur.execute(f"INSERT INTO {table} (json_data) VALUES (:1)", [json.dumps(payload)])
            conn.commit()
    except Exception as e:
        print(f"CRITICAL PERSISTENCE ERROR: {e}")
    finally:
        conn.close()
