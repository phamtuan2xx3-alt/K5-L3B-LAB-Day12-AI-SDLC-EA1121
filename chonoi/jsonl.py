"""Ghi JSONL tất định: làm tròn 3 chữ số khi XUẤT (tính toán dùng giá trị chính xác)."""

import json


# Contract v1.2: độ tươi xuất đủ chính xác (snapshot quán phải khớp CHÍNH XÁC file kho sau lần hao ở gather,
# và giữ nhánh ở ngưỡng 30); tọa độ và số khác vẫn làm tròn 3 chữ số.
_FULL_PRECISION_KEYS = {"fresh"}


def _clean(v):
    if isinstance(v, float):
        r = round(v, 3)
        return 0.0 if r == 0 else r  # tránh -0.0
    if isinstance(v, dict):
        return {k: (x if k in _FULL_PRECISION_KEYS and isinstance(x, float) else _clean(x)) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    return v


def dumps(obj) -> str:
    return json.dumps(_clean(obj), ensure_ascii=False, separators=(",", ":"))


class JsonlWriter:
    def __init__(self, path: str):
        self._f = open(path, "w", encoding="utf-8", newline="\n")

    def write(self, obj):
        self._f.write(dumps(obj) + "\n")

    def close(self):
        self._f.close()
