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
        create_table(conn)

        clear_schedule(conn)
        create_sample_data(conn)

        assignments = solve_and_record(conn, commit_result=True)
        print("=== FULL SCHEDULE VIEW ===")
        full_schedule = get_full_schedule_view(conn)
        for row in full_schedule:
            print(
                f"Lớp {row['class_id']}: {row['subject_name']}, "
                f"Phòng {row['room_code']}, Thứ {row['day']}, "
                f"Tiết {row['start_period']}-{row['end_period']}  |  "
                f"Giảng viên: {row.get('lecturer_name', 'None')} "
            )

    finally:
        conn.close()
