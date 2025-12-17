import networkx as nx
from collections import defaultdict
from database import (
    get_connection, get_all_classes, get_subject_credits, 
    get_lecturer_by_subject, get_lecturer_schedule, get_lecturer_current_load,
    assign_lecturer, clear_schedule
)


def parse_weeks(weeks_str):
    """
    Nhận chuỗi weeks như "2-19" hoặc "1,3,5" hoặc "2-5,7,9-11"
    Trả về set các số tuần (ints)
    """
    s = set()
    parts = weeks_str.split(",")
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if "-" in p:
            a, b = p.split("-")
            try:
                a = int(a) 
                b = int(b)
                s.update(range(a, b+1))
            except:
                pass
        else:
            try:
                s.add(int(p))
            except:
                pass
    return s

def time_conflict(class_1, class_2):
    """
    Kiểm tra hai lớp có xung đột lịch không:
    - cùng day
    - tiết trùng hoặc chồng (start/end overlap)
    - tuần có giao nhau
    class: dict: day,start_period,end_period,weeks (string)
    """
    if class_1["day"] != class_2["day"]:
        return False
    if class_1["end_period"] < class_2["start_period"] or class_2["end_period"] < class_1["start_period"]:
        return False
    week_1 = parse_weeks(class_1.get("weeks", ""))
    week_2 = parse_weeks(class_2.get("weeks", ""))
    if not week_1 or not week_2:
        return True
    return len(week_1 & week_2) > 0

def compute_score_for_assignment(conn, cls, lecturer):
    """
    Tính điểm phù hợp (score) cho việc gán lecturer cho class cls.
    Đơn giản hóa:
    - base_score = 100 nếu lecturer có kỹ năng dạy môn (từ lecturer_skill),
      else -1000 (không thêm cạnh nếu không có skill)
    - Deduct penalty theo tải hiện tại (current credits / max_credits)
    - Deduct penalty nếu có ít tương thích (không dùng ở đây)
    """
    subject_code = cls['subject_code']
    # lấy danh sách giảng viên theo subject (hàm get_lecturer_by_subject)
    # nhưng hàm ngoài trả list of dict giảng viên, chúng ta so sánh id
    # kiểm tra nếu lecturer được trả (đã được filtered), nếu không thì return None
    base = 100
    # lấy current load và max credits
    cur_load = get_lecturer_current_load(conn, lecturer["lecturer_id"])
    max_credits = lecturer["max_credits"]
    if max_credits <= 0:
        return -1
    load_ratio = cur_load / max_credits
    score = base - int(load_ratio * 50)
    return score

# ---------- Build graph and run min-cost flow ----------
def build_flow_graph(conn):
    """
    DiGraph
    - SOURCE -> class_node (cap=1)
    - class_node -> lec_node (cap=1, weight = -score)
    - lec_node -> SINK (cap = remaining_slots, weight=0)

    Note: remaining_slots được tính bằng floor((max_credits - current_load) / min_class_credit)
    """
    classes = get_all_classes(conn) 
    # tính tín chỉ nhỏ nhất của các lớp để xác định kích thước slot
    class_credits = {}
    min_credit = None
    for cls in classes:
        c = get_subject_credits(conn, cls['subject_code'])
        class_credits[cls['class_id']] = c
        if min_credit is None or c < min_credit:
            min_credit = c
    if min_credit is None or min_credit <= 0:
        min_credit = 1

    G = nx.DiGraph()
    SRC = "SRC"
    SNK = "SNK"
    G.add_node(SRC); G.add_node(SNK)

    # tính trước danh sách giảng viên có thể dạy mỗi lớp và cả lịch hiện tại để kiểm tra xung đột.
    # Map lec_id -> current schedule classes (list of dict)
    # map lecturer id -> dict (lecturer info: max_credits)
    # Chỉ lấy danh sách giảng viên cho từng môn dựa trên những giảng viên đủ điều kiện
    lecturers_info = {}  # id -> dict (lecturer row)
    # Lấy tất cả giảng viên cho capacity edges sau 
    cur = conn.execute("SELECT * FROM lecturer")
    for r in cur.fetchall():
        lecturers_info[r['lecturer_id']] = dict(r)

    # tính số tín chỉ còn lại của mỗi giảng viên
    remaining_credits = {}
    for lec_id, info in lecturers_info.items():
        cur_load = get_lecturer_current_load(conn, lec_id)
        remaining = info['max_credits'] - cur_load
        if remaining < 0:
            remaining = 0
        remaining_credits[lec_id] = remaining

    # Tạo node cho mỗi lớp học và nối từ SOURCE
    for cls in classes:
        cls_node = f"class_{cls['class_id']}"
        G.add_edge(SRC, cls_node, capacity=1, weight=0)

    # Đối với mỗi lớp, nối các cạnh đến những giảng viên có kỹ năng phù hợp và không có xung đột lịch trực tiếp.”
    for cls in classes:
        cls_node = f"class_{cls['class_id']}"
        subject_code = cls['subject_code']
        possible_lecs = get_lecturer_by_subject(conn, subject_code)  # list of dicts
        for lec in possible_lecs:
            lec_id = lec['lecturer_id']
            # Nếu giảng viên không còn đủ tín chỉ để dạy môn này., skip
            cls_credit = class_credits.get(cls['class_id'], 1)
            if remaining_credits.get(lec_id, 0) < cls_credit:
                continue

            # Kiểm tra xung đột với lịch hiện tại của giảng viên
            # lấy tất cả các lớp trong lịch hiện tại của giảng viên
            existing = get_lecturer_schedule(conn, lec_id)
            conflict = False
            for ex in existing:
                # ex chứa class_id, day, start_period, end_period, weeks
                if time_conflict(cls, ex):
                    conflict = True
                    break
            if conflict:
                # bỏ qua giảng viên này (xung đột về thời gian dạy)
                continue

            # tính điểm, ưu tiên giảng viên với current load thấp
            score = compute_score_for_assignment(conn, cls, lec)
            cost = -score
            lec_node = f"lec_{lec_id}"
            G.add_edge(cls_node, lec_node, capacity=1, weight=cost)

    # Thêm cạnh từ giảng viên đến SINK
    # capacity biểu diễn số lượng lớp tối đa có thể nhận
    for lec_id, remaining in remaining_credits.items():
        slot_capacity = remaining // min_credit  # số lượng tín chỉ tối thiểu có thể nhận
        if slot_capacity <= 0:
            continue
        lec_node = f"lec_{lec_id}"
        G.add_edge(lec_node, SNK, capacity=slot_capacity, weight=0)

    return G, classes, class_credits

def solve_and_record(conn, commit_result=True):
    """
    Giải bài toán phân công bằng Min-Cost Max-Flow.

    Kết quả trả về:
    - Danh sách (class_id, lecturer_id)

    Nếu commit_result = True:
    - Ghi kết quả phân công vào cơ sở dữ liệu
    """
    G, classes, class_credits = build_flow_graph(conn)
    SRC = "SRC"; SNK = "SNK"

    # run min cost max flow
    flow_dict = nx.max_flow_min_cost(G, SRC, SNK)

    # Trích xuất kết quả phân công:
    # Nếu luồng từ node lớp sang node giảng viên bằng 1 thì lớp đó được gán cho giảng viên tương ứng
    assignments = []
    class_map = {cls['class_id']: cls for cls in classes}

    for node in list(G.nodes()):
        if node.startswith("class_"):
            class_id = int(node.split("_",1)[1])
            for neigh, f in flow_dict[node].items():
                if f and neigh.startswith("lec_"):
                    lec_id = int(neigh.split("_",1)[1])
                    # Đảm bảo lớp được gán đầy đủ:
                    # f == 1 vì capacity của cạnh từ lớp sang giảng viên là 1
                    if f >= 1:
                        assignments.append((class_id, lec_id))

    # Kiểm tra lại sức chứa theo tín chỉ và cũng kiểm tra các xung đột có thể phát sinh (không nên có).
    # tính số tín chỉ cho mỗi giảng viên theo cách phân công
    lec_credit_sum = defaultdict(int)
    for class_id, lec_id in assignments:
        credits = class_credits.get(class_id, 1)
        lec_credit_sum[lec_id] += credits

    # Đối chiếu kết quả phân công với ràng buộc tín chỉ còn lại của giảng viên
    over_assigned = []
    for lec_id, credit_sum in lec_credit_sum.items():
        cur_load = get_lecturer_current_load(conn, lec_id)
        max_credits = conn.execute("SELECT max_credits FROM lecturer WHERE lecturer_id = ?", (lec_id,)).fetchone()['max_credits']
        if cur_load + credit_sum > max_credits:
            over_assigned.append(lec_id)

    # Nếu giảng viên vượt quá capacity, bỏ qua các lớp được phân công có số tín chỉ thấp nhất của giảng viên đó
    if over_assigned:
        # Tạo bảng score cho các cặp phân công
        score_map = {}
        for cls in classes:
            cls_id = cls['class_id']
            for lec in get_lecturer_by_subject(conn, cls['subject_code']):
                score_map[(cls_id, lec['lecturer_id'])] = compute_score_for_assignment(conn, cls, lec)

        # Tạo mapping lec->list of (class_id, score)
        lec_assign_map = defaultdict(list)
        for class_id, lec_id in assignments:
            s = score_map.get((class_id, lec_id), 0)
            lec_assign_map[lec_id].append((class_id, s))

        removed = []  # Danh sách lớp cần xếp lại
        for lec_id in over_assigned:
            # Sắp xếp theo score tăng dần và dừng lại cho đến khi đủ sức chứa
            lst = sorted(lec_assign_map[lec_id], key=lambda x: x[1])  # lowest score first
            # Xác định số tín chỉ cần loại bỏ để không vượt mức giới hạn
            cur_load = get_lecturer_current_load(conn, lec_id)
            max_credits = conn.execute("SELECT max_credits FROM lecturer WHERE lecturer_id = ?", (lec_id,)).fetchone()['max_credits']
            current_assigned_credits = sum(class_credits[cid] for cid, _ in lec_assign_map[lec_id])
            while cur_load + current_assigned_credits > max_credits and lst:
                drop_class_id, drop_score = lst.pop(0)
                # Xóa khỏi danh sách phân công
                try:
                    assignments.remove((drop_class_id, lec_id))
                except ValueError:
                    pass
                removed.append(drop_class_id)
                current_assigned_credits -= class_credits.get(drop_class_id, 1)

        # thử đăng ký lại các lớp bị huỷ bằng tham lam (greedily)
        if removed:
            for cid in removed:
                cls = class_map[cid]
                # “Tìm giảng viên thay thế tốt nhất trong số những người có thể dạy, không bị tràn lịch và không có xung đột.”
                possible = get_lecturer_by_subject(conn, cls['subject_code'])
                best = None; best_score = -10**9
                for lec in possible:
                    lec_id = lec['lecturer_id']
                    # Tính sức chứa còn lại theo tín chỉ ngay bây giờ
                    cur_load = get_lecturer_current_load(conn, lec_id)
                    assigned_credits = sum(class_credits[c] for c,l in assignments if l==lec_id)
                    max_credits = conn.execute("SELECT max_credits FROM lecturer WHERE lecturer_id = ?", (lec_id,)).fetchone()['max_credits']
                    if cur_load + assigned_credits + class_credits[cid] > max_credits:
                        continue
                    # Kiểm tra tính xung đột với lịch dạy và các lớp đã đăng ký trước đó
                    conflict = False
                    for ex in get_lecturer_schedule(conn, lec_id):
                        if time_conflict(cls, ex):
                            conflict = True; break
                    if conflict:
                        continue
                    # Kiểm tra xung đột với các lớp đã được phân công cho giảng viên này trong lần chạy này.
                    for (ac, al) in assignments:
                        if al == lec_id:
                            other_cls = class_map[ac]
                            if time_conflict(cls, other_cls):
                                conflict = True; break
                    if conflict:
                        continue
                    # compute score
                    score = compute_score_for_assignment(conn, cls, lec)
                    if score > best_score:
                        best = lec_id; best_score = score
                if best is not None:
                    assignments.append((cid, best))
                else:
                    # không thể đăng ký -> leave
                    pass

    if commit_result:
        clear_schedule(conn)
        for class_id, lec_id in assignments:
            assign_lecturer(conn, class_id, lec_id)

    return assignments
