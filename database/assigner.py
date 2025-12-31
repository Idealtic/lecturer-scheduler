import networkx as nx
from collections import defaultdict
from database import(
    get_all_classes, get_subject_credits, 
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

def compute_score_for_assignment(conn, lecturer):
    """
    Tính điểm phù hợp (score) cho việc gán lecturer cho class cls.
    Đơn giản hóa:
    - Deduct penalty theo tải hiện tại (current credits / max_credits)
    """
    base = 100
    cur_load = get_lecturer_current_load(conn, lecturer["lecturer_id"])
    max_credits = lecturer["max_credits"]
    if max_credits <= 0:
        return -1
    load_ratio = cur_load / max_credits
    score = base - int(load_ratio * 50)
    return score

def add_source_to_class_edges(G, SRC, classes):  # Tạo đỉnh cho mỗi lớp học và nối từ SOURCE
    for cls in classes:
        cls_node = f"class_{cls['class_id']}"
        G.add_edge(SRC, cls_node, capacity=1, weight=0)

def add_class_to_lecturer_edges(G, conn, classes, class_credits, remaining_credits): #Tạo cạnh nối lớp -> giảng viên
    for cls in classes:
        cls_node = f"class_{cls['class_id']}"
        subject_code = cls['subject_code']
        possible_lecs = get_lecturer_by_subject(conn, subject_code) 
        for lec in possible_lecs:
            lec_id = lec['lecturer_id']
            cls_credit = class_credits.get(cls['class_id'], 1)
            if remaining_credits.get(lec_id, 0) < cls_credit:
                continue

            existing = get_lecturer_schedule(conn, lec_id)
            conflict = False
            for ex in existing:
                if time_conflict(cls, ex):
                    conflict = True
                    break
            if conflict:
                continue

            score = compute_score_for_assignment(conn, lec)
            cost = -score
            lec_node = f"lec_{lec_id}"
            G.add_edge(cls_node, lec_node, capacity=1, weight=cost)

def add_lecturer_to_sink_edges(G, remaining_credits, min_credit,SNK): #Tạo cạnh nối giảng viên -> SINK
    for lec_id, remaining in remaining_credits.items():
        slot_capacity = int(remaining / min_credit)  # số lượng lớp tối đa có thể nhận
        if slot_capacity <= 0:
            continue
        lec_node = f"lec_{lec_id}"
        G.add_edge(lec_node, SNK, capacity=slot_capacity, weight=0)

def prepare_graph_data(conn):
    classes = get_all_classes(conn) 
    class_credits = {}
    min_credit = None
    subject_class_count = defaultdict(int)

    for cls in classes:
        subject_class_count[cls['subject_code']] += 1
        total_credits = get_subject_credits(conn, cls['subject_code'])
        num_sessions = subject_class_count[cls['subject_code']]

        if num_sessions > 0:
            class_credits[cls['class_id']] = total_credits / num_sessions
        else:
            class_credits[cls['class_id']] = total_credits

        class_value = class_credits[cls['class_id']]
        if min_credit is None or class_value < min_credit:
            min_credit = class_value
    if min_credit is None or min_credit <= 0:
        min_credit = 1

    lecturers_info = {}  # id -> dict (lecturer row)
    cur = conn.execute("SELECT * FROM lecturer")
    for r in cur.fetchall():
        lecturers_info[r['lecturer_id']] = dict(r)

    remaining_credits = {}
    for lec_id, info in lecturers_info.items():
        cur_load = get_lecturer_current_load(conn, lec_id)
        remaining = info['max_credits'] - cur_load
        if remaining < 0:
            remaining = 0
        remaining_credits[lec_id] = remaining

    return classes, class_credits, remaining_credits, min_credit

def build_flow_graph(conn):
    """
    DiGraph
    - SOURCE -> class_node (cap=1)
    - class_node -> lec_node (cap=1, weight = -score)
    - lec_node -> SINK (cap = remaining_slots, weight=0)

    Note: remaining_slots được tính bằng floor((max_credits - current_load) / min_class_credit)
    """
    G = nx.DiGraph()
    SRC = "SRC"
    SNK = "SNK"
    G.add_node(SRC)
    G.add_node(SNK)

    classes, class_credits, remaining_credits, min_credit = prepare_graph_data(conn)
    add_source_to_class_edges(G, SRC, classes)
    add_class_to_lecturer_edges(G, conn, classes, class_credits, remaining_credits)
    add_lecturer_to_sink_edges(G, remaining_credits, min_credit,SNK)

    return G, classes, class_credits

def assignment_result(G, flow_dict): # Nếu luồng = 1 -> Lớp được gán cho giảng viên
    assignments = []

    for node in list(G.nodes()):
        if node.startswith("class_"):
            class_id = int(node.split("_",1)[1])
            for neigh, f in flow_dict[node].items():
                if f and neigh.startswith("lec_"):
                    lec_id = int(neigh.split("_",1)[1])
                    if f >= 1:
                        assignments.append((class_id, lec_id))
    
    return assignments

def check_over_assigned(assignments, class_credits, conn): 
    lec_credit_sum = defaultdict(int)
    for class_id, lec_id in assignments:
        credits = class_credits.get(class_id, 1)
        lec_credit_sum[lec_id] += credits

    over_assigned = []
    for lec_id, credit_sum in lec_credit_sum.items():
        cur_load = get_lecturer_current_load(conn, lec_id)
        max_credits = conn.execute("SELECT max_credits FROM lecturer WHERE lecturer_id = ?", (lec_id,)).fetchone()['max_credits']
        if cur_load + credit_sum > max_credits:
            over_assigned.append(lec_id)
    
    return over_assigned

def remove_overloaded_assignment(over_assigned, classes, assignments, conn, class_credits):
    score_map = {}
    for cls in classes:
        cls_id = cls['class_id']
        for lec in get_lecturer_by_subject(conn, cls['subject_code']):
            score_map[(cls_id, lec['lecturer_id'])] = compute_score_for_assignment(conn, lec)

    lec_assign_map = defaultdict(list)
    for class_id, lec_id in assignments:
        s = score_map.get((class_id, lec_id), 0)
        lec_assign_map[lec_id].append((class_id, s))

    removed = [] 
    for lec_id in over_assigned:
        lst = sorted(lec_assign_map[lec_id], key=lambda x: x[1]) 
        cur_load = get_lecturer_current_load(conn, lec_id)
        max_credits = conn.execute("SELECT max_credits FROM lecturer WHERE lecturer_id = ?", (lec_id,)).fetchone()['max_credits']
        current_assigned_credits = sum(class_credits[cid] for cid, _ in lec_assign_map[lec_id])
        while cur_load + current_assigned_credits > max_credits and lst:
            drop_class_id, _ = lst.pop(0)
            try:
                assignments.remove((drop_class_id, lec_id))
            except ValueError:
                pass
            removed.append(drop_class_id)
            current_assigned_credits -= class_credits.get(drop_class_id, 1)

    return removed

def greedy_reassign(removed, class_map, conn, class_credits, assignments):
    if removed:
        for cid in removed:
            cls = class_map[cid]
            possible = get_lecturer_by_subject(conn, cls['subject_code'])
            best = None
            best_score = -10**9
            for lec in possible:
                lec_id = lec['lecturer_id']
                cur_load = get_lecturer_current_load(conn, lec_id)
                assigned_credits = sum(class_credits[c] for c,l in assignments if l==lec_id)
                max_credits = conn.execute("SELECT max_credits FROM lecturer WHERE lecturer_id = ?", (lec_id,)).fetchone()['max_credits']
                if cur_load + assigned_credits + class_credits[cid] > max_credits:
                    continue
                conflict = False
                for ex in get_lecturer_schedule(conn, lec_id):
                    if time_conflict(cls, ex):
                        conflict = True
                        break
                if conflict:
                    continue
                for (ac, al) in assignments:
                    if al == lec_id:
                        other_cls = class_map[ac]
                        if time_conflict(cls, other_cls):
                            conflict = True
                            break
                if conflict:
                    continue
                score = compute_score_for_assignment(conn, lec)
                if score > best_score:
                    best = lec_id; best_score = score
            if best is not None:
                assignments.append((cid, best))
            else:
                pass

def solve_and_record(conn, commit_result=True):
    """
    Giải bài toán phân công bằng Min-Cost Max-Flow.

    Kết quả trả về:
    - Danh sách (class_id, lecturer_id)

    Nếu commit_result = True:
    - Ghi kết quả phân công vào cơ sở dữ liệu
    """
    G, classes, class_credits = build_flow_graph(conn)
    SRC = "SRC"
    SNK = "SNK"

    flow_dict = nx.max_flow_min_cost(G, SRC, SNK) 

    assignments = assignment_result(G, flow_dict)
    class_map = {cls['class_id']: cls for cls in classes}
    over_assigned = check_over_assigned(assignments, class_credits, conn)

    if over_assigned:
        removed = remove_overloaded_assignment(over_assigned, classes, assignments, conn, class_credits)
        greedy_reassign(removed, class_map, conn, class_credits, assignments)
        resolve_time_conflicts(assignments, class_map, conn, class_credits)

    if commit_result:
        clear_schedule(conn)
        for class_id, lec_id in assignments:
            assign_lecturer(conn, class_id, lec_id)

    return assignments

def find_time_conflicts(assignments, class_map):
    conflicts = []
    lec_classes = defaultdict(list)

    for cid, lid in assignments:
        lec_classes[lid].append(cid)

    for lec_id, cls_ids in lec_classes.items():
        for i in range(len(cls_ids)):
            for j in range(i + 1, len(cls_ids)):
                c1 = class_map[cls_ids[i]]
                c2 = class_map[cls_ids[j]]
                if time_conflict(c1, c2):
                    conflicts.append((lec_id, cls_ids[i], cls_ids[j]))

    return conflicts

def resolve_time_conflicts(assignments, class_map, conn, class_credits):
    while True:
        conflicts = find_time_conflicts(assignments, class_map)
        if not conflicts:
            break

        lec_id, c1, c2 = conflicts[0]

        cls1 = class_map[c1]
        cls2 = class_map[c2]

        lec = conn.execute(
            "SELECT * FROM lecturer WHERE lecturer_id = ?",
            (lec_id,)
        ).fetchone()
        lec = dict(lec)

        s1 = compute_score_for_assignment(conn, lec)
        s2 = compute_score_for_assignment(conn, lec)

        drop = c1 if class_credits[c1] >= class_credits[c2] else c2

        try:
            assignments.remove((drop, lec_id))
        except ValueError:
            pass

        greedy_reassign([drop], class_map, conn, class_credits, assignments)
