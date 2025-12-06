from database import create_table, get_connection

def create_sample_data():
    create_table()
    conn = get_connection()
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        tables = ["schedule", "class", "lecturer_skill", "lecturer", "room", "subject"]
        for t in tables:
            conn.execute(f"DELETE FROM {t}")
        conn.execute("PRAGMA foreign_keys = ON")

        subject =[
            ("MI1111", "Giải tích 1", 4, 500),
            ("MI1141", "Đại số", 4, 500),
            
        ]

    except Exception:
        return -1
    finally:
        conn.close()