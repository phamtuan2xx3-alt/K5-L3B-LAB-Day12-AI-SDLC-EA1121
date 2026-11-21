"""File kho v1.0 (Contract G): {"items": {id: số nguyên >= 0}}.

Đọc: từ chối sai schema / id lạ / số âm (BadInput -> mã 2).
Ghi: bỏ mục bằng 0, qua file tạm cùng thư mục rồi thay thế, byte-ổn-định.
"""

import json
import os
import tempfile

from .errors import BadInput

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_P2 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
ALL_KINDS = KINDS_P2


def kinds_for(tuning) -> tuple:
    """Nguyên liệu hợp lệ = mọi kind trong công thức menu đang chạy (P1: 4 loại, v1.1: thêm ca_keo, keo_neo)."""
    kinds = {k for d in (tuning or {}).get("menu", {}).values() for k in d.get("recipe", {})}
    return tuple(sorted(kinds)) if kinds else KINDS_P1


def validate_items(items, kinds=ALL_KINDS):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def is_itemized(tuning, *, version=None) -> bool:
    """CLI chọn schema theo manifest; lớp mô phỏng có thể dùng tuning v1.2 riêng."""
    if version is None:
        return bool((tuning or {}).get("freshness"))
    if version == "1.2" and not (tuning or {}).get("freshness"):
        raise BadInput("contract v1.2 cần tuning.freshness")
    return version == "1.2"


def read_inventory(path: str, kinds=ALL_KINDS, itemized=False):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if itemized:  # v1.2: mảng cá thể; file kho đếm -> mã 2
        from .sim.freshness import validate_item_list
        return validate_item_list(data["items"], kinds)
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items):
    """dict đếm (v1.0/1.1) hoặc mảng cá thể (v1.2, sắp theo id, fresh đủ chính xác để đọc lại)."""
    if isinstance(items, list):
        from .ids import sort_by_id
        items = [{"id": it["id"], "kind": it["kind"], "fresh": float(it["fresh"])} for it in sort_by_id(items)]
    else:
        items = {k: items[k] for k in sorted(items) if items[k] > 0}
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
