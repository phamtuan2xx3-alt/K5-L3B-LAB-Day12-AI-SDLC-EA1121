"""Phase 3 (TICKET-03, Contract v1.2) — độ tươi phía Quán (DEV 3): kho cá thể, hao tươi, ươn,
giữ chỗ theo id, giữ lại khi hàng vừa ươn, giá theo độ tươi.

Bật khi tuning có khóa `freshness` (contract 1.2). Không có khóa đó thì quán chạy kho đếm v1.0/v1.1
như cũ, để main vẫn chạy được trong lúc các lát khác chuyển schema.

Độ tươi lưu bằng Fraction (chính xác tuyệt đối): hao 0.25/s = 1/240 mỗi tick ở quán, so ngưỡng 30 và
floor giá không bao giờ lệch vì sai số dấu phẩy động. Xuất JSON bằng float(Fraction).
"""

import math
import numbers
from fractions import Fraction

from ..errors import BadInput
from ..ids import id_key, sort_by_id

TICK = 60
ITEM_KEYS = {"id", "kind", "fresh"}


UNITS = 240  # 1 điểm tươi = 240 đơn vị: quán hao 1 đơn vị/tick, giỏ 2 đơn vị/tick (mọi giá trị chạy là bội 1/240)


def frac(x) -> Fraction:
    """Số -> Fraction chính xác. Float sát một bội 1/240 (vd 30.004166666666666 đọc lại từ file kho) được đưa về
    đúng bội đó, để giá trị và nhánh ở ngưỡng 30 giữ nguyên sau khi ghi/đọc; số thập phân khác giữ nguyên."""
    if isinstance(x, Fraction):
        return x
    f = Fraction(str(x))
    u = round(f * UNITS)
    return Fraction(u, UNITS) if abs(f * UNITS - u) < Fraction(1, 10 ** 6) else f


def config(tuning):
    """Cấu hình độ tươi v1.2, hoặc None nếu contract chưa bật."""
    f = (tuning or {}).get("freshness")
    if f is None:
        return None
    return {
        "initial": frac(f["initial"]),
        "gather_decay": frac(f["gather_decay_per_s"]) / TICK,
        "quan_decay": frac(f["quan_decay_per_s"]) / TICK,
        "spoiled_below": frac(f["spoiled_below"]),
    }


# ---------------------------------------------------------------- schema cá thể (mục 1, Contract v1.2)

def validate_item_list(items, kinds, where="items") -> list:
    """Mảng {id, kind, fresh}: id chuỗi khác rỗng duy nhất, kind trong danh mục, fresh hữu hạn [0, 100]."""
    if not isinstance(items, list):
        raise BadInput(f"{where} phải là mảng cá thể {{id, kind, fresh}} (contract 1.2)")
    out, seen = [], set()
    for i, it in enumerate(items):
        if not isinstance(it, dict) or set(it) != ITEM_KEYS:
            raise BadInput(f"{where}[{i}] phải có đúng các khóa id, kind, fresh")
        iid, kind, fresh = it["id"], it["kind"], it["fresh"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"{where}[{i}].id phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"{where}: id trùng {iid}")
        seen.add(iid)
        if kind not in kinds:
            raise BadInput(f"{where}.{iid}: nguyên liệu lạ {kind!r}")
        if isinstance(fresh, bool) or not isinstance(fresh, numbers.Real) or not math.isfinite(fresh) \
                or not (0 <= fresh <= 100):
            raise BadInput(f"{where}.{iid}: fresh phải là số hữu hạn trong [0, 100]")
        out.append({"id": iid, "kind": kind, "fresh": frac(fresh)})
    return out


def out_item(it) -> dict:
    return {"id": it["id"], "kind": it["kind"], "fresh": float(it["fresh"])}


def items_from_handoff(raw, kinds, ids, initial) -> list:
    """Kho vào quán: mảng cá thể (v1.2) hoặc, trong lúc chuyển, object đếm từ day (cấp id mới, fresh = initial)."""
    if isinstance(raw, list):
        return [dict(it, fresh=frac(it["fresh"])) for it in validate_item_list(raw, kinds, "stock")]
    out = []
    for kind in sorted(raw or {}):
        for _ in range(raw[kind]):
            out.append({"id": ids.new("I"), "kind": kind, "fresh": initial})
    return out


# ---------------------------------------------------------------- kho khả dụng / giữ chỗ theo id

def is_spoiled(sim, it) -> bool:
    return it["fresh"] < sim.fresh["spoiled_below"]


def held_ids(sim) -> set:
    return {iid for c in sim.customers for iid in (c["reserved"] or [])}


def available_items(sim) -> list:
    """Cá thể chưa ươn, chưa bị đơn nào giữ."""
    held = held_ids(sim)
    return [it for it in sim.items.values() if it["id"] not in held and not is_spoiled(sim, it)]


def counts(items) -> dict:
    out = {}
    for it in items:
        out[it["kind"]] = out.get(it["kind"], 0) + 1
    return out


def freshest_first(items) -> list:
    return sorted(items, key=lambda it: (-it["fresh"], id_key(it["id"])))


def pick(sim, recipe, pool=None):
    """Mỗi loại trong công thức lấy các cá thể khả dụng tươi nhất, hòa theo id. Thiếu -> None."""
    pool = available_items(sim) if pool is None else pool
    chosen = []
    for kind in sorted(recipe):
        cands = freshest_first([it for it in pool if it["kind"] == kind])
        if len(cands) < recipe[kind]:
            return None
        chosen += [it["id"] for it in cands[:recipe[kind]]]
    return sorted(chosen, key=id_key)


def recipe_of_ids(sim, ids_) -> dict:
    return counts(sim.items[i] for i in ids_)


# ---------------------------------------------------------------- một bước Quán (mục 1, "Thứ tự trong tick")

def decay(sim, events) -> set:
    """Hao tươi kho thô (kể cả hàng đang giữ), kẹp 0; phát spoiled theo id khi đi từ >= 30 xuống < 30."""
    thr, step = sim.fresh["spoiled_below"], sim.fresh["quan_decay"]
    spoiled = set()
    for it in sort_by_id(list(sim.items.values())):
        before = it["fresh"]
        it["fresh"] = max(Fraction(0), before - step)
        if before >= thr > it["fresh"]:
            spoiled.add(it["id"])
            events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "stock"}))
    return spoiled


def rehold(sim, spoiled_ids):
    """Đơn reserved có cá thể vừa ươn: nhả toàn bộ phần giữ, thử giữ lại ĐÚNG MỘT lần, theo order_tick rồi id bàn.
    Không đủ thì đơn chuyển unfulfillable, khách vẫn chờ tới hạn kiên nhẫn."""
    affected = [c for c in sim.customers
                if c["order_status"] == "reserved" and spoiled_ids & set(c["reserved"] or [])]
    for c in sorted(affected, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
        c["reserved"] = []
        ids_ = pick(sim, sim.menu[c["dish_id"]]["recipe"])
        if ids_ is None:
            c["order_status"] = "unfulfillable"
        else:
            c["reserved"] = ids_


def take(sim, ids_) -> list:
    """Bếp tiêu đúng các id đang giữ; trả cá thể đã dùng (sắp theo kind rồi id cho cook_started.items)."""
    used = [sim.items.pop(i) for i in ids_]
    return sorted(used, key=lambda it: (it["kind"], id_key(it["id"])))


def fresh_price(list_price, used) -> int:
    """base_price = floor(giá niêm yết × trung bình fresh của các cá thể dùng / 100)."""
    mean = sum((it["fresh"] for it in used), Fraction(0)) / len(used)
    return math.floor(Fraction(list_price) * mean / 100)
