from database import get_connection, get_lecturer_current_load

def check_lecturer_skill(lecturer_id, subject_code, conn):
    cursor = conn.execute(
    """SELECT 1 FROM lecturer_skill WHERE lecturer_id = ? AND subject_code = ?""",
    (lecturer_id, subject_code)
    )
    result = cursor.fetchone()
    return result is not None

def check_time_conflict(lecturer_id, day, start_period, end_period, conn):
    query = """
        SELECT 1
        FROM schedule s 
        JOIN class c ON s.class_id = c.class_id
        WHERE s.lecturer_id = ?
        AND c.day = ?
        AND (c.start_period < ? and ? < c.end_period)
    """
    cursor = conn.execute(query, (lecturer_id, day, end_period, start_period))
    result = cursor.fetchone()
    return result is not None

def check_lecturer_max_credits(lecturer_id, new_credits, max_credits, conn):
    current_load = get_lecturer_current_load(conn, lecturer_id)
    if current_load + new_credits > max_credits:
        return False
    return True



    

