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

        subjects =[
            ("SSH1111", "Triết học Mác - Lênin", 3, 0),
            ("SSH1121", "Kinh tế chính trị Mác - Lênin", 2, 0),
            ("SSH1131", "Chủ nghĩa xã hội khoa học", 2, 0),
            ("SSH1141", "Lịch sử Đảng cộng sản Việt Nam", 2, 0),
            ("SSH1151", "Tư tưởng Hồ Chí Minh", 2, 0),

            ("MI1111", "Giải tích I", 4, 0),
            ("MI1121", "Giải tích II", 3, 0),
            ("MI1131", "Giải tích III", 3, 0),
            ("MI1141", "Đại số", 4, 0),
            ("MI2020", "Xác suất thống kê", 3, 0),
            ("MI3010", "Toán rời rạc", 3, 0),
            ("MI3041", "Giải tích số", 2, 0),
            ("MI2001", "Nhập môn HTTTQL", 3, 0),
            ("MI3031", "Suy luận thống kê", 3, 0),
            ("MI3060", "Cấu trúc dữ liệu và giải thuật", 3, 0),
            ("MI3090", "Cơ sở dữ liệu", 3, 0),
            ("MI3120", "Phân tích và thiết kế hệ thống", 3, 0),
            ("MI3130", "Toán kinh tế", 3, 0),
            ("MI3310", "Kỹ thuật lập trình", 2, 0),
            ("MI3370", "Hệ điều hành", 2, 0),

            ("IT1110", "Tin học đại cương", 4, 0),
            ("PH1110", "Vật lý đại cương I", 3, 0),
            ("PH1120", "Vật lý đại cương II", 3, 0),

            ("EM1010", "Quản trị học đại cương", 2, 0),
            ("EM1170", "Pháp luật đại cương", 2, 0),
            ("EM1180", "Văn hóa kinh doanh và tinh thần khởi nghiệp", 2, 0),
            ("EM3102", "Kinh tế đại cương", 3, 0),
            ("EM3190", "Hành vi của tổ chức", 2, 0),
            ("EM3211", "Nguyên lý marketing", 3, 0),
        ]
        if subjects:
            conn.executemany("INSERT OR IGNORE INTO subject VALUES (?,?,?,?)", subjects)
            print(f"Đã thêm {len(subjects)} môn học.")

        rooms = [
            ("D3-101", 200), ("D3-102", 200), ("D3-103", 150), ("D3-104", 150), ("D3-105", 150),
            ("D3-201", 120), ("D3-202", 120), ("D3-203", 100), ("D3-204", 100), ("D3-205", 100),
            ("D3-301", 80), ("D3-302", 80), ("D3-303", 60), ("D3-304", 60), ("D3-305", 60),
            ("D3-401", 50), ("D3-402", 50), ("D3-403", 45), ("D3-404", 45), ("D3-405", 45),
            ("D3-501", 40), ("D3-502", 40), ("D3-503", 40), ("D3-504", 40), ("D3-505", 40),

            ("D5-101", 200), ("D5-102", 200), ("D5-103", 150), ("D5-104", 150), ("D5-105", 150),
            ("D5-201", 120), ("D5-202", 120), ("D5-203", 100), ("D5-204", 100), ("D5-205", 100),
            ("D5-301", 80), ("D5-302", 80), ("D5-303", 60), ("D5-304", 60), ("D5-305", 60),
            ("D5-401", 50), ("D5-402", 50), ("D5-403", 45), ("D5-404", 45), ("D5-405", 45),
            ("D5-501", 40), ("D5-502", 40), ("D5-503", 40), ("D5-504", 40), ("D5-505", 40),

            ("D7-101", 200), ("D7-102", 200), ("D7-103", 150), ("D7-104", 150), ("D7-105", 150),
            ("D7-201", 120), ("D7-202", 120), ("D7-203", 100), ("D7-204", 100), ("D7-205", 100),
            ("D7-301", 80), ("D7-302", 80), ("D7-303", 60), ("D7-304", 60), ("D7-305", 60),
            ("D7-401", 50), ("D7-402", 50), ("D7-403", 45), ("D7-404", 45), ("D7-405", 45),
            ("D7-501", 40), ("D7-502", 40), ("D7-503", 40), ("D7-504", 40), ("D7-505", 40),

            ("D9-101", 200), ("D9-102", 200), ("D9-103", 150), ("D9-104", 150), ("D9-105", 150),
            ("D9-201", 120), ("D9-202", 120), ("D9-203", 100), ("D9-204", 100), ("D9-205", 100),
            ("D9-301", 80), ("D9-302", 80), ("D9-303", 60), ("D9-304", 60), ("D9-305", 60),
            ("D9-401", 50), ("D9-402", 50), ("D9-403", 45), ("D9-404", 45), ("D9-405", 45),
            ("D9-501", 40), ("D9-502", 40), ("D9-503", 40), ("D9-504", 40), ("D9-505", 40)
        ]
        if rooms:
            conn.executemany("INSERT OR IGNORE INTO subject VALUES (?,?)", rooms)
            print(f"Đã thêm {len(rooms)} môn học.")

        lecturers = [
            
        ]
    except Exception:
        return -1
    finally:
        conn.close()