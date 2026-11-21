"""Lát 3 (DEV 3) — vòng đời khách quán: đến theo lịch, xếp bàn, chọn món nấu được, giữ chỗ
nguyên liệu, kiên nhẫn, rời quán. Theo PRD-0 mục D (fixture), E (event) và F (luật một bước).

Tách khỏi quan.py để lát 4/5 (kho, bếp, bưng, tiền) sửa quan.py mà ít đụng nhau. QuanSim gọi:
  init_customers()   lúc dựng fixture     (kiểm mâu thuẫn -> BadInput -> mã 2)
  tick_timers()      bước 1               (kiên nhẫn, timer ăn)
  settle_tables()    bước 4               (ăn xong trả tiền, hết kiên nhẫn, đóng ca)
  maybe_spawn()      bước 5               (lượt khách mới, no_dish)

Kho: sim.stock là tồn VẬT LÝ (gồm cả phần giữ chỗ). Khả dụng = tồn - tổng reserved của mọi khách.
"""

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from . import freshness as fr

TICK = 60

CUSTOMER_KEYS = ("id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                 "eat_ticks_left", "order_status", "reserved", "base_price", "tip")
STATES = ("waiting", "eating")
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")


def to_ticks(seconds) -> int:
    return int(round(seconds * TICK))


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _clamp_rep(sim, value):
    t = sim.t
    return max(t["reputation_min"], min(t["reputation_max"], round(value, 3)))


# ---------------------------------------------------------------- kho khả dụng / chọn món

def reserved_total(customers) -> dict:
    total = {}
    for c in customers:
        for kind, n in c["reserved"].items():
            total[kind] = total.get(kind, 0) + n
    return total


def available_stock(sim) -> dict:
    """Tồn vật lý trừ phần đang giữ chỗ. v1.2: đếm cá thể chưa ươn, chưa bị giữ."""
    if getattr(sim, "itemized", False):
        return fr.counts(fr.available_items(sim))
    held = reserved_total(sim.customers)
    return {k: sim.stock.get(k, 0) - held.get(k, 0) for k in set(sim.stock) | set(held)}


def menu_pool(sim) -> list:
    """Id món khách được gọi, theo mã Unicode. Trong day (v1.1) lọc theo kế hoạch Ngày TRƯỚC khi xét kho."""
    allowed = getattr(sim, "allowed_dishes", None)
    return [d for d in sorted(sim.menu) if allowed is None or d in allowed]


def cookable_dishes(sim) -> list:
    """Món trong pool đủ nguyên liệu khả dụng (tồn - giữ chỗ), theo thứ tự mã Unicode của id món."""
    avail = available_stock(sim)
    return [d for d in menu_pool(sim)
            if all(avail.get(k, 0) >= n for k, n in sim.menu[d]["recipe"].items())]


# ---------------------------------------------------------------- fixture (mục D)

def _bad(cid, msg):
    raise BadInput(f"customers.{cid}: {msg}")


def init_customers(sim, raw_customers, random_customers=True):
    """Chuẩn hóa khách fixture, cấp reserved còn thiếu, kiểm mâu thuẫn mức luật."""
    if not isinstance(random_customers, bool):
        raise BadInput("random_customers phải là boolean")
    t = sim.t
    patience_full, eat_full = to_ticks(t["patience_s"]), to_ticks(t["eat_s"])
    table_ids = {tb["id"] for tb in sim.tables}
    out = []
    for raw in raw_customers:
        cid = raw["id"]
        extra = set(raw) - set(CUSTOMER_KEYS)
        if extra:
            _bad(cid, f"trường lạ/chưa hỗ trợ {sorted(extra)}")
        if raw.get("table_id") not in table_ids:
            _bad(cid, "table_id phải là bàn có thật")
        if raw.get("dish_id") not in sim.menu:
            _bad(cid, "dish_id thiếu hoặc ngoài thực đơn")
        c = {
            "id": cid,
            "table_id": raw["table_id"],
            "dish_id": raw["dish_id"],
            "order_tick": raw.get("order_tick", 0),
            "state": raw.get("state", "waiting"),
            "patience_ticks_left": raw.get("patience_ticks_left", patience_full),
            "eat_ticks_left": raw.get("eat_ticks_left", 0),
            "order_status": raw.get("order_status", "reserved"),
            "reserved": raw.get("reserved"),
            "base_price": raw.get("base_price"),
            "tip": raw.get("tip"),
        }
        if c["state"] not in STATES:
            _bad(cid, f"state phải là một trong {STATES}")
        if c["order_status"] not in ORDER_STATUSES:
            _bad(cid, f"order_status phải là một trong {ORDER_STATUSES}")
        for key, hi in (("order_tick", None), ("patience_ticks_left", patience_full),
                        ("eat_ticks_left", eat_full)):
            v = c[key]
            if not _is_int(v) or v < 0 or (hi is not None and v > hi):
                _bad(cid, f"{key} phải là số nguyên trong [0, {hi if hi is not None else '∞'}]")
        if c["reserved"] is not None and sim.itemized:
            r = c["reserved"]
            if not isinstance(r, list) or any(not isinstance(i, str) or not i for i in r) or len(set(r)) != len(r):
                _bad(cid, "reserved phải là mảng id cá thể khác nhau (contract 1.2)")
            c["reserved"] = list(r)
        elif c["reserved"] is not None:
            r = c["reserved"]
            if not isinstance(r, dict) or any(k not in _kinds(sim) or not _is_int(n) or n < 0
                                              for k, n in r.items()):
                _bad(cid, "reserved phải là map nguyên liệu -> số nguyên không âm")
            c["reserved"] = {k: n for k, n in r.items() if n > 0}
        # Liên kết trạng thái khách / đơn
        if c["state"] == "eating":
            if c["order_status"] != "served":
                _bad(cid, "khách eating phải có đơn served")
            if c["eat_ticks_left"] <= 0:
                _bad(cid, "khách eating cần eat_ticks_left > 0")
            for key in ("base_price", "tip"):
                if not _is_int(c[key]) or c[key] < 0:
                    _bad(cid, f"khách eating phải khai {key} (số nguyên không âm)")
        else:
            if c["order_status"] == "served":
                _bad(cid, "đơn served chỉ có ở khách eating")
            if c["eat_ticks_left"] != 0:
                _bad(cid, "khách chưa ăn thì eat_ticks_left = 0")
        if c["order_status"] != "reserved" and c["reserved"]:
            _bad(cid, f"đơn {c['order_status']} không còn giữ chỗ")
        if c["order_status"] == "reserved" and c["reserved"] is not None:
            if sim.itemized:
                for iid in c["reserved"]:
                    if iid not in sim.items:
                        _bad(cid, f"reserved trỏ tới cá thể không có trong kho: {iid}")
                    if fr.is_spoiled(sim, sim.items[iid]):
                        _bad(cid, f"reserved trỏ tới cá thể đã ươn: {iid}")
                if fr.recipe_of_ids(sim, c["reserved"]) != sim.menu[c["dish_id"]]["recipe"]:
                    _bad(cid, "giữ chỗ khác công thức món")
            elif c["reserved"] != sim.menu[c["dish_id"]]["recipe"]:
                _bad(cid, "giữ chỗ khác công thức món")
        out.append(c)

    # Đơn reserved thiếu reserved: cấp theo công thức, theo order_tick rồi id bàn.
    pending = sorted((c for c in out if c["reserved"] is None),
                     key=lambda c: (c["order_tick"], id_key(c["table_id"])))
    for c in out:
        if c["reserved"] is None and c["order_status"] != "reserved":
            c["reserved"] = [] if sim.itemized else {}
    if sim.itemized:
        _allocate_itemized(sim, out, pending)
        _check_dish_links(sim, out)
        return sort_by_id(out)
    for c in pending:
        if c["order_status"] == "reserved":
            c["reserved"] = dict(sim.menu[c["dish_id"]]["recipe"])
    held = reserved_total(out)
    for kind, n in held.items():
        if n > sim.stock.get(kind, 0):
            raise BadInput(f"tổng giữ chỗ {kind}={n} vượt tồn kho {sim.stock.get(kind, 0)}")
    _check_dish_links(sim, out)
    return sort_by_id(out)


def _allocate_itemized(sim, out, pending):
    """v1.2: id giữ chỗ không dùng chung giữa các đơn; đơn reserved thiếu reserved được cấp theo
    order_tick rồi id bàn, mỗi loại lấy cá thể chưa ươn tươi nhất rồi id nhỏ. Thiếu -> mã 2."""
    held = [i for c in out for i in (c["reserved"] or [])]
    if len(held) != len(set(held)):
        raise BadInput("hai đơn giữ chung một cá thể")
    taken = set(held)
    for c in pending:
        if c["order_status"] != "reserved":
            continue
        pool = [it for it in sim.items.values() if it["id"] not in taken and not fr.is_spoiled(sim, it)]
        ids_ = fr.pick(sim, sim.menu[c["dish_id"]]["recipe"], pool=pool)
        if ids_ is None:
            _bad(c["id"], "kho không đủ cá thể chưa ươn để giữ chỗ")
        c["reserved"] = ids_
        taken |= set(ids_)


def _kinds(sim):
    kinds = set()
    for d in sim.menu.values():
        kinds |= set(d["recipe"])
    return kinds


def _check_dish_links(sim, customers):
    """Món ở bếp/tay phải trỏ tới đúng một đơn assigned cùng dish_id; đơn assigned có đúng một món."""
    by_id = {c["id"]: c for c in customers}
    holders = {}
    payloads = [(f"bếp {s['id']}", s.get("dish")) for s in sim.stoves] + [("tay", sim.hand)]
    for where, dish in payloads:
        if dish is None:
            continue
        if not isinstance(dish, dict) or "order_id" not in dish:
            raise BadInput(f"{where}: món phải là payload {{order_id, dish_id, base_price}}")
        c = by_id.get(dish["order_id"])
        if c is None or c["order_status"] != "assigned":
            raise BadInput(f"{where}: order_id {dish['order_id']} không phải đơn assigned")
        if dish.get("dish_id") != c["dish_id"]:
            raise BadInput(f"{where}: món không khớp đơn {c['id']}")
        holders.setdefault(c["id"], []).append(where)
    for c in customers:
        n = len(holders.get(c["id"], []))
        if c["order_status"] == "assigned" and n != 1:
            raise BadInput(f"customers.{c['id']}: đơn assigned cần đúng một món ở bếp hoặc tay (có {n})")


# ---------------------------------------------------------------- luật một bước (mục F)

def tick_timers(sim):
    """Bước 1: giảm kiên nhẫn khách đang chờ và timer ăn. Timer không âm."""
    for c in sim.customers:
        if c["state"] == "waiting":
            c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
        elif c["state"] == "eating":
            c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)


def _drop_order_dish(sim, order_id):
    """Khách rời: bỏ món của đơn đang nấu, ready hoặc trên tay (nguyên liệu đã dùng không hoàn)."""
    for s in sim.stoves:
        dish = s.get("dish")
        if isinstance(dish, dict) and dish.get("order_id") == order_id:
            s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
    if isinstance(sim.hand, dict) and sim.hand.get("order_id") == order_id:
        sim.hand = None


def remove_customer(sim, c, reason, events):
    """Khách chưa được phục vụ rời quán (patience/closing): nhả giữ chỗ, bỏ món, có thể trừ uy tín."""
    c["reserved"] = [] if getattr(sim, "itemized", False) else {}
    _drop_order_dish(sim, c["id"])
    if reason == "patience":
        sim.reputation = _clamp_rep(sim, sim.reputation + sim.t["left_reputation_delta"])
    sim.customers.remove(c)
    events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"],
                                     "reason": reason, "reputation": sim.reputation}))


def pay(sim, c, reason, events):
    """Khách đã được phục vụ trả tiền rồi rời bàn ngay.

    Bản tối thiểu theo PRD-0 F để vòng đời khách khép kín; lát 4/5 (DEV 5) sở hữu phần tiền và
    có thể thay hàm này (hoặc gán sim.pay_customer) mà không cần sửa settle_tables.
    """
    base, tip = c["base_price"] or 0, c["tip"] or 0
    amount = base + tip
    sim.money += amount
    sim.earned += amount
    sim.shift_earned += amount
    if tip > 0:
        sim.reputation = _clamp_rep(sim, sim.reputation + sim.t["tip_reputation"])
    sim.customers.remove(c)
    events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": base,
                            "tip": tip, "amount": amount, "reason": reason}))


def settle_tables(sim, events, closing: bool):
    """Bước 4, theo id bàn: ăn xong trả tiền; hết kiên nhẫn rời (còn giờ); đóng ca dọn hết."""
    pay_fn = getattr(sim, "pay_customer", None) or (lambda c, reason, ev: pay(sim, c, reason, ev))
    for tb in sort_by_id(sim.tables):
        c = next((x for x in sim.customers if x["table_id"] == tb["id"]), None)
        if c is None:
            continue
        if c["state"] == "eating":
            if c["eat_ticks_left"] <= 0:
                pay_fn(c, "finished_eating", events)
            elif closing:
                pay_fn(c, "closing", events)
        elif closing:
            remove_customer(sim, c, "closing", events)
        elif c["patience_ticks_left"] <= 0:
            remove_customer(sim, c, "patience", events)


def maybe_spawn(sim, events):
    """Bước 5 (chỉ khi ca còn giờ): lượt khách theo first_customer_tick rồi mỗi customer_interval_s."""
    if not sim.random_customers:
        return
    t = sim.t
    first, interval = t["first_customer_tick"], to_ticks(t["customer_interval_s"])
    pt = sim.phase_tick
    if pt < first or (pt - first) % interval != 0:
        return
    occupied = {c["table_id"] for c in sim.customers}
    free = [tb for tb in sort_by_id(sim.tables) if tb["id"] not in occupied]
    if not free:
        return  # không còn bàn: bỏ lượt, không phát event
    dishes = cookable_dishes(sim)
    if not dishes:
        events.append(("no_dish", {}))
        return
    dish_id = sim.rng.get("customer_dish").choice(dishes)
    table = free[0]
    cid = sim.ids.new("C")
    sim.customers.append({
        "id": cid,
        "table_id": table["id"],
        "dish_id": dish_id,
        "order_tick": pt,
        "state": "waiting",
        "patience_ticks_left": to_ticks(t["patience_s"]),
        "eat_ticks_left": 0,
        "order_status": "reserved",
        "reserved": (fr.pick(sim, sim.menu[dish_id]["recipe"]) if getattr(sim, "itemized", False)
                     else dict(sim.menu[dish_id]["recipe"])),
        "base_price": None,
        "tip": None,
    })
    sim.customers = sort_by_id(sim.customers)
    events.append(("customer_arrived", {"order_id": cid, "table_id": table["id"], "dish_id": dish_id}))
