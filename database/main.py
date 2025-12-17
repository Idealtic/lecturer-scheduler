from database import (
    get_connection,
    create_table,
    get_full_schedule_view,
    clear_schedule
)
from assigner import solve_and_record
from sample_data import create_sample_data

if __name__ == "__main__":

    conn = get_connection()
    try:
        # 1. Khởi tạo bảng (nếu chưa tạo)
        create_table(conn)

        # 2. Xóa lịch AUTO cũ để chạy mới
        clear_schedule(conn)
        create_sample_data(conn)

        # 3. Chạy thuật toán phân công
        assignments = solve_and_record(conn, commit_result=True)
        #print("debugg", assignments)
        # 4. In lịch đầy đủ sau khi phân công
        print("=== FULL SCHEDULE VIEW ===")
        full_schedule = get_full_schedule_view(conn)
        for row in full_schedule:
            print(
                f"Class {row['class_id']}: {row['subject_name']}, "
                f"Room {row['room_code']}, Day {row['day']}, "
                f"{row['start_period']}-{row['end_period']}  |  "
                f"Lecturer: {row.get('lecturer_name', 'None')} "
                f"({row['status']})"
            )

    finally:
        conn.close()
