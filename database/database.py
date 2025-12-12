import sqlite3
import os

DB_PATH = "university.db"

def get_connection(): #hàm khởi tạo
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_table(conn): #hàm tạo bảng
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subject(
        subject_code TEXT PRIMARY KEY,
        subject_name TEXT,
        credits INTEGER,
        num_students INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS room(
        room_code TEXT PRIMARY KEY,
        capacity INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lecturer(
        lecturer_id INTEGER PRIMARY KEY,
        lecturer_name TEXT,
        max_credits INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lecturer_skill(
        lecturer_id INTEGER,
        subject_code TEXT,
        PRIMARY KEY(lecturer_id, subject_code),
        FOREIGN KEY(lecturer_id) REFERENCES lecturer(lecturer_id),
        FOREIGN KEY(subject_code) REFERENCES subject(subject_code)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS classes(
        class_id INTEGER PRIMARY KEY,
        subject_code TEXT,
        room_code TEXT,
        day INTEGER,
        start_period INTEGER,
        end_period INTEGER,
        weeks TEXT,
        num_students INTEGER,
        FOREIGN KEY(subject_code) REFERENCES subject(subject_code),
        FOREIGN KEY(room_code) REFERENCES room(room_code)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedule(
        class_id INTEGER PRIMARY KEY,
        lecturer_id INTEGER,
        status TEXT DEFAULT "AUTO",
        is_locked INTEGER DEFAULT 0,
        FOREIGN KEY(class_id) REFERENCES classes(class_id),
        FOREIGN KEY(lecturer_id) REFERENCES lecturer(lecturer_id)
    )
    """)

    conn.commit()

def get_all_classes(conn): #hàm lấy tất cả các lớp
    cursor = conn.execute("SELECT * FROM classes")
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_lecturer_by_subject(conn, subject_code): #hàm lấy thông tin giảng viên theo môn
    query = """
        SELECT l.* FROM lecturer l
        JOIN lecturer_skill s ON l.lecturer_id = s.lecturer_id
        WHERE s.subject_code = ?
    """
    cursor = conn.execute(query, (subject_code,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_lecturer_schedule(conn, lecturer_id): #hàm lấy lịch của 1 giảng viên
    query = """
        SELECT s.class_id, c.day, c.start_period, c.end_period, c.weeks
        FROM schedule s
        JOIN classes c ON s.class_id = c.class_id
        WHERE s.lecturer_id = ?
    """
    cursor = conn.execute(query, (lecturer_id,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_room_info(conn, room_code): #hàm lấy thông tin của phòng
    cursor = conn.execute("SELECT * FROM room WHERE room_code = ?", (room_code,))
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None

def get_lecturer_current_load(conn, lecturer_id): #hàm lấy tổng số tín chỉ của giảng viên
    query = """
        SELECT SUM(sub.credits) as total_credits
        FROM schedule s
        JOIN classes c ON s.class_id = c.class_id
        JOIN subject sub ON c.subject_code = sub.subject_code
        WHERE s.lecturer_id = ?
    """
    cursor = conn.execute(query, (lecturer_id,))
    row = cursor.fetchone()
    return row['total_credits'] if row['total_credits'] else 0

def get_full_schedule_view(conn): #hàm in ra lịch đầy đủ
    query = """
        SELECT 
            c.class_id, 
            sub.subject_name, 
            c.room_code, 
            c.day, 
            c.start_period, 
            c.end_period,
            l.lecturer_name,
            s.status
        FROM schedule s
        JOIN classes c ON s.class_id = c.class_id
        JOIN subject sub ON c.subject_code = sub.subject_code
        LEFT JOIN lecturer l ON s.lecturer_id = l.lecturer_id
    """
    cursor = conn.execute(query)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def assign_lecturer(conn, class_id, lecturer_id): #hàm lưu kết quả
    try:
        query = """
            INSERT OR REPLACE INTO schedule (class_id, lecturer_id, status)
            VALUES (?, ?, 'AUTO')
        """
        conn.execute(query, (class_id, lecturer_id))
        conn.commit()
        return True
    except Exception:
        return False

def clear_schedule(conn): #hàm reset kết quả phân công khi muốn chạy lần sau
    conn.execute("DELETE FROM schedule WHERE is_locked = 0")
    conn.commit()

if __name__ == "__main__":
    conn = get_connection()
    try:
        create_table(conn)
        print("Đã tạo database.")
    finally:
        conn.close()