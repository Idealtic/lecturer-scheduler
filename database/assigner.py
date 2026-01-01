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

def compute_score_for_assignment(cur_load, max_credits):
    if max_credits <= 0: 
        return -1
    load_ratio = cur_load / max_credits
    score = 100 - int(load_ratio * 50)
    return score

def add_source_to_class_edges(G, SRC, classes):  # Tạo đỉnh cho mỗi lớp học và nối từ SOURCE
    for cls in classes:
        cls_node = f"class_{cls['class_id']}"
        G.add_edge(SRC, cls_node, capacity=1, weight=0)

def add_class_to_lecturer_edges(G, conn, classes):  # Tạo cạnh nối lớp -> giảng viên
    for cls in classes:
        cls_node = f"class_{cls['class_id']}"
        subject_code = cls['subject_code']

        possible_lecs = get_lecturer_by_subject(conn, subject_code)

        for lec in possible_lecs:
            lec_id = lec['lecturer_id']
            lec_node = f"lec_{lec_id}"
            existing_schedule = get_lecturer_schedule(conn, lec_id)
            has_conflict = False

            for existing_cls in existing_schedule:
                if time_conflict(cls, existing_cls):
                    has_conflict = True 
                    break
            if has_conflict:
                continue

            cur_load = get_lecturer_current_load(conn, lec_id)
            max_credits = lec['max_credits']
            remaining = max_credits - cur_load

            subject_credits = get_subject_credits(conn, subject_code)

            if remaining < subject_credits * 0.5:
                continue

            score = compute_score_for_assignment(cur_load, max_credits)
            if score < 0:
                continue
            
            cost = -score
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

    for cls in classes:
        total_credits = get_subject_credits(conn, cls['subject_code'])
        
        if total_credits >= 4:
            val = total_credits / 2
        else:
            val = total_credits

        class_credits[cls['class_id']] = val
        
        if min_credit is None or val < min_credit:
            min_credit = val

    if min_credit is None or min_credit <= 0:
        min_credit = 1

    lecturer_max_credits = {}
    cur = conn.execute("SELECT lecturer_id, max_credits FROM lecturer")
    for r in cur:
        lecturer_max_credits[r['lecturer_id']] = r['max_credits']

    remaining_credits = lecturer_max_credits.copy()

    return classes, class_credits, remaining_credits, min_credit, lecturer_max_credits

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

    classes, class_credits, remaining_credits, min_credit, lecturer_max_credits = prepare_graph_data(conn)
    add_source_to_class_edges(G, SRC, classes)
    add_class_to_lecturer_edges(G, conn, classes)
    add_lecturer_to_sink_edges(G, remaining_credits, min_credit,SNK)

    return G, classes, class_credits, lecturer_max_credits 

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
            score_map[(cls_id, lec['lecturer_id'])] = compute_score_for_assignment(cur_load, max_credits)

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

def greedy_reassign(removed_class_ids, class_map, conn, class_credits, assignments, current_load_map, lecturer_max_credits, lec_schedule_map, black_list = None):
    if black_list is None:
        black_list = {}

    for cid in removed_class_ids:
        cls = class_map[cid]
        sub_code = cls['subject_code']
        possible_lecs = get_lecturer_by_subject(conn, sub_code)

        best_lec_id = None
        best_score = -10**9

        for lec in possible_lecs:
            lec_id = lec['lecturer_id']

            if cid in black_list and lec_id in black_list[cid]:
                continue

            max_credits = lecturer_max_credits.get(lec_id, 0)
            cur_load = current_load_map.get(lec_id, 0)
            cred = class_credits.get(cid, 2)

            if cur_load + cred > max_credits:
                continue
            
            conflict = False
            if lec_id in lec_schedule_map:
                for assigned_cls in lec_schedule_map[lec_id]:
                    if time_conflict(cls, assigned_cls):
                        conflict = True
                        break
            if conflict: 
                continue

            score = compute_score_for_assignment(cur_load, max_credits)
            if score > best_score:
                best_lec_id = lec_id
                best_score = score

        if best_lec_id is not None:
            assignments.append((cid, best_lec_id))
            current_load_map[best_lec_id] += class_credits.get(cid, 2)
            lec_schedule_map[best_lec_id].append(cls)
        else:
            pass

def resolve_split_subjects(assignments, class_map, class_credits, current_load_map, lecturer_max_credits, lec_schedule_map):
    """
    Đảm bảo các lớp (buổi) cùng subject_code được gán cho cùng 1 giảng viên
    """
    # subject_code -> list of (class_id, lecturer_id)
    subject_assignments = defaultdict(list)

    for cid, lid in assignments:
        subject = class_map[cid]['subject_code']
        subject_assignments[subject].append((cid, lid))

    for subject, lst in subject_assignments.items():
        if len(lst) < 2:
            continue
        
        lecturers = [lid for _, lid in lst]
        if len(set(lecturers)) <= 1:
            continue

        lec_count = defaultdict(int)
        for lid in lecturers:
            lec_count[lid] += 1
        target_lec = max(lec_count, key=lec_count.get)

        for cid, current_lid in lst:
            if current_lid == target_lec: continue

            cls = class_map[cid]
            cred = class_credits.get(cid, 2)

            target_load = current_load_map.get(target_lec, 0)
            target_max = lecturer_max_credits.get(target_lec, 0)

            if target_load + cred > target_max:
                continue
            conflict = False
            if target_lec in lec_schedule_map:
                for assigned_cls in lec_schedule_map[target_lec]:
                    if time_conflict(cls, assigned_cls):
                        conflict = True
                        break
            if conflict: 
                continue # Target bị trùng lịch

            # --- CHUYỂN GIAO (UPDATE STATE) ---
            try:
                # 1. Gỡ khỏi người cũ
                assignments.remove((cid, current_lid))
                current_load_map[current_lid] -= cred
                if cls in lec_schedule_map[current_lid]:
                    lec_schedule_map[current_lid].remove(cls)
                
                # 2. Gán cho người mới
                assignments.append((cid, target_lec))
                current_load_map[target_lec] += cred
                lec_schedule_map[target_lec].append(cls)
                
            except ValueError:
                pass

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

def resolve_time_conflicts(assignments, class_map, conn, class_credits, current_load_map, lecturer_max_credits, lec_schedule_map):
    loop_count = 0

    while loop_count < 100:
        conflicts = find_time_conflicts(assignments, class_map)
        if not conflicts:
            break

        lec_id, c1, c2 = conflicts[0]

        lec = conn.execute(
            "SELECT * FROM lecturer WHERE lecturer_id = ?",
            (lec_id,)
        ).fetchone()
        lec = dict(lec)

        drop = c1 if class_credits[c1] >= class_credits[c2] else c2

        try:
            assignments.remove((drop, lec_id))
            current_load_map[lec_id] -= class_credits.get(drop, 2)
            lec_schedule_map[lec_id].remove(class_map[drop])
        except ValueError:
            pass
        
        black_list = {drop: [lec_id]}

        greedy_reassign([drop], class_map, conn, class_credits, assignments, current_load_map, lecturer_max_credits, lec_schedule_map, black_list = black_list)

        loop_count += 1

def check_and_remove_conflicts(assignments, class_map, current_load_map, class_credits, lecturer_max_credits):
    clean_assignments = []
    removed = []
    lec_schedule = defaultdict(list)

    for cid, lid in assignments:
        cls = class_map[cid]
        cred = class_credits.get(cid, 2)
        max_c = lecturer_max_credits.get(lid, 0)

        conflict = False
        for assigned_cls in lec_schedule[lid]:
            if time_conflict(cls, assigned_cls):
                conflict = True
                break
        
        if conflict:
            removed.append(cid)
            continue 

        if current_load_map[lid] + cred > max_c:
            removed.append(cid)
            continue

        lec_schedule[lid].append(cls)
        current_load_map[lid] += class_credits.get(cid, 2)
        clean_assignments.append((cid, lid))
        
    return clean_assignments, removed, lec_schedule

def solve_and_record(conn, commit_result=True):
    """
    Giải bài toán phân công bằng Min-Cost Max-Flow.

    Kết quả trả về:
    - Danh sách (class_id, lecturer_id)

    Nếu commit_result = True:
    - Ghi kết quả phân công vào cơ sở dữ liệu
    """
    G, classes, class_credits, lecturer_max_credits = build_flow_graph(conn)
    SRC = "SRC"
    SNK = "SNK"

    flow_dict = nx.max_flow_min_cost(G, SRC, SNK) 

    raw_assignments = assignment_result(G, flow_dict)
    class_map = {cls['class_id']: cls for cls in classes}
    current_load_map = defaultdict(int)
    assignments, removed, lec_schedule_map = check_and_remove_conflicts(raw_assignments, class_map, current_load_map, class_credits, lecturer_max_credits)
    assigned_ids = set(cid for cid, lid in assignments)

    all_unassigned = [cls['class_id'] for cls in classes if cls['class_id'] not in assigned_ids]
    greedy_reassign(all_unassigned, class_map, conn, class_credits, assignments, current_load_map, lecturer_max_credits, lec_schedule_map)
    resolve_time_conflicts(assignments, class_map, conn, class_credits, current_load_map, lecturer_max_credits, lec_schedule_map)
    resolve_split_subjects(assignments, class_map, class_credits, current_load_map, lecturer_max_credits, lec_schedule_map)

    if commit_result:
        clear_schedule(conn)
        for class_id, lec_id in assignments:
            assign_lecturer(conn, class_id, lec_id)

    return assignments
