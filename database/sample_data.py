from database import create_table, get_connection
import random
import math

def insert_subjects(conn): #thêm dữ liệu vào bảng subject
    subjects = [
        ("SSH1111", "Triết học Mác - Lênin", 3, 3500),
        ("SSH1121", "Kinh tế chính trị Mác - Lênin", 2, 3200),
        ("SSH1131", "Chủ nghĩa xã hội khoa học", 2, 3000),
        ("SSH1141", "Lịch sử Đảng cộng sản Việt Nam", 2, 2800),
        ("SSH1151", "Tư tưởng Hồ Chí Minh", 2, 2800),

        ("MI1111", "Giải tích I", 4, 4000),
        ("MI1121", "Giải tích II", 3, 3500),
        ("MI1131", "Giải tích III", 3, 1500),
        ("MI1141", "Đại số", 4, 4000),
        ("MI2020", "Xác suất thống kê", 3, 3000),
        ("MI3010", "Toán rời rạc", 3, 900),
        ("MI3041", "Giải tích số", 2, 350),
        ("MI2001", "Nhập môn HTTTQL", 3, 300),
        ("MI3031", "Suy luận thống kê", 3, 250),
        ("MI3060", "Cấu trúc dữ liệu và giải thuật", 3, 1200),
        ("MI3090", "Cơ sở dữ liệu", 3, 1100),
        ("MI3120", "Phân tích và thiết kế hệ thống", 3, 500),
        ("MI3130", "Toán kinh tế", 3, 150),
        ("MI3310", "Kỹ thuật lập trình", 2, 800),
        ("MI3370", "Hệ điều hành", 2, 750),

        ("EM1010", "Quản trị học đại cương", 2, 1800),
        ("EM1170", "Pháp luật đại cương", 2, 2500),
        ("EM1180", "Văn hóa kinh doanh và tinh thần khởi nghiệp", 2, 200),
        ("EM3102", "Kinh tế đại cương", 3, 300),
        ("EM3190", "Hành vi của tổ chức", 2, 200),
        ("EM3211", "Nguyên lý marketing", 3, 300)
    ]
    if subjects:
        conn.executemany("INSERT OR IGNORE INTO subject VALUES (?,?,?,?)", subjects)
        print(f"Đã thêm {len(subjects)} môn học.")
    return subjects

def insert_rooms(conn): #thêm dữ liệu vào bảng room
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
        conn.executemany("INSERT OR IGNORE INTO room VALUES (?,?)", rooms)
        print(f"Đã thêm {len(rooms)} phòng học.")
    return rooms

def insert_lecturers(conn): #thêm dữ liệu vào bảng lecturer
    lecturers = [
        (20250001, "Phạm Minh Hoàng", 20),
        (20250002, "Dương Tùng Lâm", 20),
        (20250003, "Nguyễn Văn An", 18),
        (20250004, "Trần Thị Bích", 22),
        (20250005, "Lê Hoàng Nam", 24),
        (20250006, "Vũ Ngọc Ánh", 16),
        (20250007, "Đặng Minh Tuấn", 21),
        (20250008, "Bùi Thị Mai", 19),
        (20250009, "Ngô Thành Đạt", 23),
        (20250010, "Hoàng Văn Hùng", 15),
        (20250011, "Phan Thị Lan", 20),
        (20250012, "Vương Quốc Bảo", 24),
        (20250013, "Trịnh Văn Quyết", 17),
        (20250014, "Đinh Thị Hương", 22),
        (20250015, "Lý Văn Khải", 18),
        (20250016, "Nguyễn Thị Thu", 8),
        (20250017, "Trần Văn Hậu", 6),
        (20250018, "Lê Thị Thanh", 9),
        (20250019, "Hoàng Đức Dũng", 21),
        (20250020, "Đỗ Văn Mạnh", 23),
        (20250021, "Tạ Thị Tuyết", 16),
        (20250022, "Cao Văn Thắng", 20),
        (20250023, "Nguyễn Hữu Nghĩa", 24),
        (20250024, "Trần Quang Huy", 19),
        (20250025, "Lê Văn Long", 15),
        (20250026, "Phạm Thị Yến", 22),
        (20250027, "Nguyễn Đức Tâm", 17),
        (20250028, "Vũ Văn Kiên", 5),
        (20250029, "Đặng Thị Hoa", 20),
        (20250030, "Bùi Văn Phúc", 18)
    ]
    if lecturers:
        conn.executemany("INSERT OR IGNORE INTO lecturer VALUES (?,?,?)", lecturers)
        print(f"Đã thêm {len(lecturers)} giảng viên.")
    return lecturers

def insert_lecturer_skills(conn): #thêm dữ liệu vào bảng lecturer_skill
    skills = [
        (20250001, "MI1111"), (20250001, "MI1141"), (20250001, "MI2020"), (20250001, "MI3010"),
        (20250002, "MI1121"), (20250002, "MI1131"), (20250002, "MI3041"),
        (20250003, "MI1111"), (20250003, "MI1121"), (20250003, "MI1131"),
        (20250004, "MI1141"), (20250004, "MI2020"), (20250004, "MI3031"),
        (20250005, "MI3060"), (20250005, "MI3090"), (20250005, "MI3310"),
        (20250006, "MI2001"), (20250006, "MI3120"), (20250006, "MI3130"),
        (20250007, "MI3370"), (20250007, "MI3060"), (20250007, "MI3310"),
        (20250008, "MI1111"), (20250008, "MI2020"),
        (20250009, "MI3010"), (20250009, "MI3041"), (20250009, "MI3031"),
        (20250010, "MI1121"), (20250010, "MI1131"), (20250010, "MI1141"),
        (20250011, "MI3090"), (20250011, "MI3120"), (20250011, "MI2001"),
        (20250012, "MI1141"), (20250012, "MI2001"), (20250012, "MI3060"),
        (20250013, "MI3031"), (20250013, "MI3130"), (20250013, "MI2020"),
        (20250014, "MI1111"), (20250014, "MI1121"), (20250014, "MI1131"), (20250014, "MI1141"),
        (20250015, "MI3370"), (20250015, "MI3310"),
        (20250016, "MI3060"), (20250016, "MI3090"),

        (20250017, "SSH1111"), (20250017, "SSH1121"), (20250017, "SSH1151"),
        (20250018, "SSH1131"), (20250018, "SSH1141"), (20250018, "SSH1151"),
        (20250019, "SSH1111"), (20250019, "SSH1121"),
        (20250020, "SSH1131"), (20250020, "SSH1141"),
        (20250021, "SSH1111"), (20250021, "SSH1131"),
        (20250022, "SSH1121"), (20250022, "SSH1141"),
        (20250023, "SSH1151"), (20250023, "SSH1111"),

        (20250024, "EM1010"), (20250024, "EM1170"),
        (20250025, "EM1180"), (20250025, "EM3102"),
        (20250026, "EM3190"), (20250026, "EM3211"),
        (20250027, "EM1010"), (20250027, "EM3102"),
        (20250028, "EM1170"), (20250028, "EM1180"),
        (20250029, "EM1010"), (20250029, "EM3211"), (20250029, "EM1180"),
        (20250030, "EM1170"), (20250030, "EM3190"), (20250030, "EM3102")
    ]
    if skills:
        conn.executemany("INSERT OR IGNORE INTO lecturer_skill VALUES (?,?)", skills)
        print(f"Đã phân công giảng viên.")
    return skills

def insert_classes(subjects, conn, rooms): #thêm dữ liệu vào bảng class
    ssh_subs = [s for s in subjects if s[0].startswith("SSH")]
    mi_subs  = [s for s in subjects if s[0].startswith("MI")]
    em_subs  = [s for s in subjects if s[0].startswith("EM")]

    sorted_subjects = ssh_subs + mi_subs + em_subs
    classes = []
    current_class_id = 163001
    room_codes = [r[0] for r in rooms]

    for sub in sorted_subjects:
        sub_code = sub[0]
        credits = sub[2]
        total_students = sub[3]

        if total_students <= 0:
            continue

        avg_size = 60
        num_classes = math.ceil(total_students / avg_size)
        base_student_count = int(total_students / num_classes)

        for _ in range(num_classes):
            variance = int(base_student_count * 0.15)
            student_count = random.randint(base_student_count - variance, base_student_count + variance)
            if student_count > 200:
                student_count = 200
            
            room = random.choice(room_codes)
            weeks = "2-19"

            if credits == 2:
                day = random.randint(2, 7)
                start_period = random.choice([1, 4, 7, 10])
                end_period = start_period + 2

                classes.append((current_class_id, sub_code, room, day, start_period, end_period, weeks, student_count))
                current_class_id +=1

            elif credits == 3:
                mode = random.choice(["1 buổi", "2 buổi"])
                if mode == "1 buổi":
                    day = random.randint(2, 7)
                    start_period = random.choice([1, 6])
                    end_period = start_period + 3

                    classes.append((current_class_id, sub_code, room, day, start_period, end_period, weeks, student_count))
                    current_class_id += 1

                else:
                    day_1 = random.randint(2, 5)
                    day_2 = day_1 + 2

                    start_period = random.choice([1, 3, 5, 7, 9, 11])
                    end_period = start_period + 1

                    classes.append((current_class_id, sub_code, room, day_1, start_period, end_period, weeks, student_count))
                    current_class_id += 1
                    classes.append((current_class_id, sub_code, room, day_2, start_period, end_period, weeks, student_count))
                    current_class_id += 1

            elif credits == 4:
                day_1 = random.randint(2, 5)
                day_2 = day_1 + 2

                start_1 = random.choice([1, 4, 7, 10])
                end_1 = start_1 + 2

                start_2 = random.choice([1, 3, 5, 7, 9, 11])
                end_2 = start_2 + 1
                
                classes.append((current_class_id, sub_code, room, day_1, start_1, end_1, weeks, student_count))
                current_class_id += 1
                classes.append((current_class_id, sub_code, room, day_2, start_2, end_2, weeks, student_count))
                current_class_id += 1

    if classes:
        conn.executemany("INSERT OR IGNORE INTO class VALUES (?,?,?,?,?,?,?,?)", classes)
        print(f"Đã thêm {len(classes)} lớp học.")
    return classes

def create_sample_data(): #xoá dữ liệu cũ và thêm tất cả dữ liệu mới vào các bảng
    create_table()
    conn = get_connection()
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        tables = ["schedule", "class", "lecturer_skill", "lecturer", "room", "subject"]
        for t in tables:
            conn.execute(f"DELETE FROM {t}")
        conn.execute("PRAGMA foreign_keys = ON")

        subjects = insert_subjects(conn)
        rooms = insert_rooms(conn)
        insert_lecturers(conn)
        insert_lecturer_skills(conn)
        insert_classes(subjects, conn, rooms)

        conn.commit()
        print("Nạp dữ liệu hoàn tất")
    except Exception as error:
        print(f"Lỗi: {error}")
        return -1
    finally:
        conn.close()

if __name__ == "__main__":
    create_sample_data()