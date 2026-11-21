"""Cửa sổ chơi trực tiếp bằng TRÌNH DUYỆT, chỉ dùng thư viện chuẩn Python.

    python3 -m chonoi.live --mode gather|quan [--seed N] [--port 8000]

Máy chủ HTTP nhỏ (ThreadingHTTPServer) phục vụ `chonoi/web/index.html` và hai API:
    GET  /state  -> snapshot JSON hiện tại (cùng trường như dòng snapshot của headless) + `meta` + `events`
    POST /input  -> {"move": [a, b], "interact": bool, "catch": bool}   (trạng thái phím đang giữ)
    POST /restart -> chơi lại từ đầu (cùng seed, cùng scenario)

Mô phỏng chạy 60 tick/s trong một luồng nền, dùng CÙNG lớp sim như headless (qua `runner.Session`).
Client chỉ ĐỌC snapshot và tự bỏ qua trường chưa có, nên luật do nhóm viết thêm trường nào cũng không vỡ.
Ngẫu nhiên vẫn đi qua `Streams` (seed); chỉ nhịp chạy theo đồng hồ thật, không đi vào luật.
"""

import argparse
import json
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .contract import load_contract
from .errors import BadInput
from .inputs import BUTTONS_V11, LiveInputs
from .inventory import is_itemized, kinds_for, read_inventory
from .runner import Session
from .scenario import load_scenario

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
TICK_S = 1.0 / 60.0
MAX_BODY = 4096
RECENT_EVENTS = 40


class LiveGame:
    """Một lượt chơi + luồng nền bước 60 tick/s. Mọi truy cập trạng thái đi qua khóa."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None):
        self._args = (mode, tuning, scenario, seed, inventory)
        self.mode = mode
        self.tuning = tuning
        self.scenario = scenario
        self.seed = seed
        self.inventory = inventory
        self.inventory_out = inventory_out

        # Trạng thái tổng thể xuyên suốt chu trình 24h & các phase
        self.master_day = 1
        self.master_phase = mode if mode in ("gather", "quan", "day") else "gather"
        self.master_phase_tick = 0
        if isinstance(inventory, dict):
            self.master_stock = dict(inventory)
        elif isinstance(inventory, list):
            self.master_stock = list(inventory)
        else:
            self.master_stock = {}
        self.master_money = int(scenario.get("day", {}).get("money", scenario.get("quan", {}).get("money", 0)))
        self.master_earned = 0
        self.master_reputation = float(scenario.get("day", {}).get("reputation", scenario.get("quan", {}).get("reputation", tuning.get("quan", {}).get("reputation_initial", 3.0))))
        self.master_upgrades = dict(scenario.get("day", {}).get("upgrades", {}))

        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread = None
        self._reset()

    def _reset(self):
        effective_tuning = dict(self.tuning)
        if self.mode == "gather" or (self.mode == "day" and getattr(self, "master_phase", "gather") == "gather"):
            gather_t = dict(self.tuning.get("gather", {}))
            if "oxygen" in self.master_upgrades:
                lvl = self.master_upgrades["oxygen"]
                gather_t["oxygen_max_s"] = 45 if lvl == 1 else 60
            if "hp" in self.master_upgrades:
                lvl = self.master_upgrades["hp"]
                gather_t["hp_max"] = 4 if lvl == 1 else 5
            effective_tuning["gather"] = gather_t

        eff_scen = dict(self.scenario)
        eff_inv = self.inventory
        if self.mode == "quan":
            q_scen = dict(eff_scen.get("quan", {}))
            if self.master_stock:
                q_scen["stock"] = self.master_stock
                eff_inv = self.master_stock
            q_scen["money"] = self.master_money
            q_scen["reputation"] = self.master_reputation
            eff_scen["quan"] = q_scen

        self.session = Session(self.mode, effective_tuning, eff_scen, self.seed, eff_inv)
        self.inputs = LiveInputs(buttons=BUTTONS_V11)
        self.events = []
        self._saved = False
        self.error = None

    # --- luồng nền ----------------------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._loop, name="chonoi-sim", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        nxt = time.perf_counter()
        while not self._stop.is_set():
            nxt += TICK_S
            with self._lock:
                try:
                    self._tick_once()
                except Exception:  # luật của nhóm lỗi: báo ra terminal + client, dừng bước (restart để chơi lại)
                    self.error = traceback.format_exc()
                    sys.stderr.write(self.error)
                    self.session.sim.done = True
                    self.session.sim.reason = "error"
            delay = nxt - time.perf_counter()
            if delay > 0:
                self._stop.wait(delay)
            elif delay < -0.25:  # chạy chậm quá thì bỏ bù, tránh chạy dồn
                nxt = time.perf_counter()

    def _tick_once(self):
        s = self.session
        if self.mode == "day":
            if s.done:
                return
            for row in s.step(self.inputs.advance()):
                self.events.append(row)
            del self.events[:-RECENT_EVENTS]
            return

        # Khi đang ở phase Chuẩn Bị (prep) hoặc Nghỉ ngơi (sleep)
        if self.master_phase in ("prep", "shop"):
            self.master_phase_tick += 1
            if self.master_phase_tick >= 3600:  # 60s @ 60Hz = 3h in-game -> auto chuyển sang quan
                self.goto_phase("quan")
            return

        if self.master_phase == "sleep":
            self.master_phase_tick += 1
            if self.master_phase_tick >= 3600:  # 60s @ 60Hz = 7h in-game -> auto chuyển sang ngày mới
                self.goto_phase("gather")
            return

        if not s.done:
            for row in s.step(self.inputs.advance()):
                self.events.append(row)
            del self.events[:-RECENT_EVENTS]

            if s.done:
                if self.master_phase == "gather":
                    # Xuất giỏ đồ vào kho
                    if hasattr(s.sim, "inventory_items"):
                        collected = s.sim.inventory_items()
                    else:
                        collected = [it["kind"] if isinstance(it, dict) else it for it in getattr(s.sim, "hold", [])]
                    if isinstance(self.master_stock, dict) and isinstance(collected, dict):
                        for k, v in collected.items():
                            self.master_stock[k] = self.master_stock.get(k, 0) + v
                    elif isinstance(self.master_stock, dict) and isinstance(collected, list):
                        for it in collected:
                            k = it["kind"] if isinstance(it, dict) else it
                            self.master_stock[k] = self.master_stock.get(k, 0) + 1
                    elif isinstance(self.master_stock, list):
                        if isinstance(collected, list):
                            self.master_stock.extend(collected)
                        elif isinstance(collected, dict):
                            for k, v in collected.items():
                                for _ in range(v):
                                    self.master_stock.append(k)

                    if self.inventory_out and not self._saved:
                        self._saved = True
                        try:
                            s.write_inventory_if_done(self.inventory_out)
                        except OSError as e:
                            sys.stderr.write(f"lỗi ghi kho: {e}\n")

                    # Tự động cập bến và sang phase prep (15:00 - 18:00)
                    self.master_phase = "prep"
                    self.master_phase_tick = 0
                    self.events.append(("phase_start", {"phase": "prep"}))

                elif self.master_phase == "quan":
                    self.master_money = getattr(s.sim, "money", self.master_money)
                    self.master_earned = getattr(s.sim, "earned", self.master_earned)
                    self.master_reputation = getattr(s.sim, "reputation", self.master_reputation)
                    if hasattr(s.sim, "stock"):
                        self.master_stock = dict(s.sim.stock)

                    # Tự động đóng quán và sang phase sleep (23:00 - 06:00)
                    self.master_phase = "sleep"
                    self.master_phase_tick = 0
                    self.events.append(("phase_start", {"phase": "sleep"}))

    def goto_phase(self, new_phase):
        with self._lock:
            # Thu gom an toàn nếu đang chuyển từ gather sang phase khác
            if self.master_phase == "gather" and new_phase != "gather":
                if hasattr(self.session.sim, "inventory_items"):
                    collected = self.session.sim.inventory_items()
                else:
                    collected = [it["kind"] if isinstance(it, dict) else it for it in getattr(self.session.sim, "hold", [])]
                if isinstance(self.master_stock, dict) and isinstance(collected, dict):
                    for k, v in collected.items():
                        self.master_stock[k] = self.master_stock.get(k, 0) + v
                elif isinstance(self.master_stock, dict) and isinstance(collected, list):
                    for it in collected:
                        k = it["kind"] if isinstance(it, dict) else it
                        self.master_stock[k] = self.master_stock.get(k, 0) + 1

            if new_phase in ("prep", "shop"):
                self.master_phase = "prep"
                self.master_phase_tick = 0
                self.events.append(("phase_start", {"phase": "prep"}))
            elif new_phase == "quan":
                self.master_phase = "quan"
                self.mode = "quan"
                self.master_phase_tick = 0
                # Nếu kho hoàn toàn rỗng, cấp sẵn một số nguyên liệu cơ bản để quán nấu nướng
                if not self.master_stock:
                    self.master_stock = {"ca_loc": 3, "bong_sung": 6, "ca_linh": 4, "bong_dien_dien": 4}
                self.scenario = dict(self.scenario)
                q_scen = dict(self.scenario.get("quan", {}))
                q_scen["stock"] = self.master_stock
                q_scen["money"] = self.master_money
                q_scen["earned"] = self.master_earned
                q_scen["reputation"] = self.master_reputation
                self.scenario["quan"] = q_scen
                self._args = ("quan", self.tuning, self.scenario, self.seed, self.master_stock)
                self._reset()
                self.events.append(("phase_start", {"phase": "quan"}))
            elif new_phase == "sleep":
                self.master_phase = "sleep"
                self.master_phase_tick = 0
                self.events.append(("phase_start", {"phase": "sleep"}))
            elif new_phase == "gather":
                if self.master_phase == "sleep":
                    self.master_day = (self.master_day % 5) + 1
                self.master_phase = "gather"
                self.mode = "gather"
                self.master_phase_tick = 0
                self._args = ("gather", self.tuning, self.scenario, self.seed, None)
                self._reset()
                self.events.append(("day_start", {"day": self.master_day}))
                self.events.append(("phase_start", {"phase": "gather"}))

    def get_clock(self) -> dict:
        if self.mode == "day" and hasattr(self.session.sim, "get_clock"):
            return self.session.sim.get_clock()

        phase = self.master_phase
        if phase == "gather":
            sub_ticks = getattr(self.session.sim, "ticks_run", getattr(self.session.sim, "phase_tick", self.master_phase_tick))
            tick_lim = getattr(self.session.sim, "tick_limit", getattr(self.session.sim, "duration_ticks", 10800))
            prog = min(1.0, max(0.0, sub_ticks / max(1, tick_lim)))
            mins = 6 * 60 + int(prog * 540)  # 06:00 -> 15:00
            period = "morning" if mins < 12 * 60 else "afternoon"
        elif phase in ("prep", "shop"):
            prog = min(1.0, max(0.0, self.master_phase_tick / 3600.0))
            mins = 15 * 60 + int(prog * 180)  # 15:00 -> 18:00
            period = "afternoon"
        elif phase == "quan":
            sub_ticks = getattr(self.session.sim, "ticks_run", getattr(self.session.sim, "phase_tick", self.master_phase_tick))
            tick_lim = getattr(self.session.sim, "tick_limit", getattr(self.session.sim, "duration_ticks", 10800))
            prog = min(1.0, max(0.0, sub_ticks / max(1, tick_lim)))
            mins = 18 * 60 + int(prog * 300)  # 18:00 -> 23:00
            period = "evening"
        elif phase == "sleep":
            prog = min(1.0, max(0.0, self.master_phase_tick / 3600.0))
            mins = (23 * 60 + int(prog * 420)) % 1440  # 23:00 -> 06:00
            period = "night"
        else:
            mins = 6 * 60
            period = "morning"

        hour = (mins // 60) % 24
        minute = mins % 60
        return {
            "hour": hour,
            "minute": minute,
            "time_str": f"{hour:02d}:{minute:02d}",
            "period": period,
            "day": self.master_day,
            "real_minutes_per_24h": 8.0,
            "ratio_desc": "24h game = 8 phut doi thuc (1s thuc = 3 phut game)"
        }

    def get_areas(self, hour: int) -> dict:
        return {
            "ben_lan": {
                "id": "ben_lan",
                "name": "Bến Lặn Sông Tiền",
                "open": 6 <= hour < 15,
                "hours": "06:00 - 15:00",
                "desc": "Lặn bắt cá Linh, Cá Lóc, Cá Kèo và hái hoa"
            },
            "cho_chu_sau": {
                "id": "cho_chu_sau",
                "name": "Chợ Nổi Chú Sáu",
                "open": 15 <= hour < 22,
                "hours": "15:00 - 22:00",
                "desc": "Mua bán nguyên liệu, nâng cấp ghe và trang bị"
            },
            "quan_an": {
                "id": "quan_an",
                "name": "Quán Ăn Má Tư",
                "open": 18 <= hour < 23,
                "hours": "18:00 - 23:00",
                "desc": "Tiếp khách ghe, nấu nướng và phục vụ"
            },
            "ghe_nghi": {
                "id": "ghe_nghi",
                "name": "Ghe Nghỉ Út Sen",
                "open": (hour >= 22 or hour < 6),
                "hours": "22:00 - 06:00",
                "desc": "Nghỉ ngơi, hồi phục thể lực và sang ngày mới"
            }
        }

    # --- API cho handler -----------------------------------------------------------
    def state_json(self) -> bytes:
        with self._lock:
            snap = self.session.snapshot()
            clk = self.get_clock()
            snap["clock"] = clk
            snap["areas"] = self.get_areas(clk["hour"])
            snap["day"] = self.master_day if self.mode != "day" else getattr(self.session.sim, "current_day", getattr(self.session.sim, "day", self.master_day))
            snap["mode"] = self.mode
            snap["phase"] = self.master_phase if self.mode != "day" else getattr(self.session.sim, "phase", self.mode)
            snap["master_stock"] = self.master_stock
            snap["master_money"] = self.master_money
            snap["master_reputation"] = self.master_reputation
            if "stock" not in snap and self.master_stock:
                snap["stock"] = self.master_stock
            phase = snap["phase"]
            snap["meta"] = self.tuning.get(phase, self.tuning.get(self.mode, self.tuning.get("gather", {})))
            snap["events"] = list(self.events)
            snap["finished"] = self.session.done if self.master_phase in ("gather", "quan") else False
            snap["reason"] = self.session.sim.reason if self.session.done else None
            snap["error"] = self.error
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def set_input(self, body: dict):
        move = body.get("move")
        if move is not None:
            ok = (isinstance(move, list) and len(move) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and abs(c) <= 1 for c in move))
            if not ok:
                raise ValueError("move phải là [a, b] trong [-1, 1]")
        buttons = {}
        for b in ("interact", "catch", "pause", "shop_done", "attack", "photo"):
            if b in body:
                if not isinstance(body[b], bool):
                    raise ValueError(f"{b} phải là boolean")
                buttons[b] = body[b]
        buy = body.get("buy")
        if buy is not None:
            if not isinstance(buy, str) or not buy.strip():
                raise ValueError("buy phải là chuỗi khác rỗng")
            buy = buy.strip()
        with self._lock:
            self.inputs.set(move, buy=buy, **buttons)

    def restart(self):
        with self._lock:
            self._reset()

    def switch_mode(self, new_mode):
        if new_mode not in ("gather", "quan", "day"):
            raise ValueError(f"Chế độ không hợp lệ: {new_mode}")
        if new_mode == "gather":
            self.goto_phase("gather")
        elif new_mode == "quan":
            self.goto_phase("quan")
        elif new_mode == "day":
            with self._lock:
                self.mode = "day"
                self.master_phase = "gather"
                self._args = ("day", self.tuning, self.scenario, self.seed, None)
                self._reset()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    game: LiveGame = None  # gán trên lớp con trong make_server

    def log_message(self, fmt, *args):  # yên lặng
        pass

    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/state":
            self._send(200, self.game.state_json())
        elif path in ("/", "/index.html"):
            try:
                with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(404, b'{"error":"thieu index.html"}')
        elif path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
        else:
            rel_path = path.lstrip("/")
            full_path = os.path.join(WEB_DIR, rel_path)
            if os.path.isfile(full_path):
                ctype = "application/octet-stream"
                if rel_path.endswith(".js"): ctype = "application/javascript"
                elif rel_path.endswith(".css"): ctype = "text/css"
                elif rel_path.endswith(".png"): ctype = "image/png"
                elif rel_path.endswith(".svg"): ctype = "image/svg+xml"
                elif rel_path.endswith(".ico"): ctype = "image/x-icon"
                try:
                    with open(full_path, "rb") as f:
                        self._send(200, f.read(), ctype)
                    return
                except OSError:
                    pass
            self._send(404, b'{"error":"khong co"}')

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > MAX_BODY:
            self._send(400, b'{"error":"body sai"}')
            return
        raw = self.rfile.read(n) if n else b""
        try:
            if path == "/input":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                self.game.set_input(body)
            elif path == "/restart":
                self.game.restart()
            elif path in ("/mode", "/switch_mode"):
                body = json.loads(raw.decode("utf-8") or "{}")
                new_mode = body.get("mode")
                if not new_mode:
                    raise ValueError("Thiếu trường 'mode'")
                self.game.switch_mode(new_mode)
            elif path == "/next_phase":
                body = json.loads(raw.decode("utf-8") or "{}")
                phase = body.get("phase")
                if not phase or phase not in ("gather", "prep", "shop", "quan", "sleep"):
                    raise ValueError(f"Phase không hợp lệ: {phase}")
                self.game.goto_phase(phase)
            else:
                self._send(404, b'{"error":"khong co"}')
                return
        except (ValueError, UnicodeDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self._send(200, b'{"ok":true}')


class LiveServer:
    """Máy chủ + mô phỏng. port=0 -> cổng ngẫu nhiên (đọc `.port`)."""

    def __init__(self, game: LiveGame, host="127.0.0.1", port=8000):
        handler = type("Handler", (_Handler,), {"game": game})
        self.game = game
        self.httpd = ThreadingHTTPServer((host, port), handler)
        self.httpd.daemon_threads = True
        self.host = host
        self.port = self.httpd.server_address[1]
        self._thread = None

    @property
    def url(self):
        return f"http://{self.host}:{self.port}/"

    def start(self):
        self.game.start()
        self._thread = threading.Thread(target=self.httpd.serve_forever, name="chonoi-http", daemon=True)
        self._thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)
        self.game.stop()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.live", description="Chơi trực tiếp trên trình duyệt (starter).")
    p.add_argument("--mode", required=True, choices=["gather", "quan", "day"])
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--port", type=int, default=8000, help="0 = cổng ngẫu nhiên")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--scenario")
    p.add_argument("--inventory", help="chỉ với quan: nạp kho từ file")
    p.add_argument("--inventory-out", dest="inventory_out", help="chỉ với gather: ghi kho khi kết thúc buổi")
    a = p.parse_args(argv)
    try:
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        contract = load_contract()
        tuning = contract["tuning"]
        itemized = is_itemized(tuning, version=contract.get("contract_version", "1.0"))
        scenario = load_scenario(a.scenario, a.mode, tuning)
        inventory = read_inventory(a.inventory, kinds_for(tuning), itemized) if a.inventory else None
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
        game = LiveGame(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out)
        server = LiveServer(game, a.host, a.port)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không mở được cổng {a.port}: {e}\n")
        return 1
    server.start()
    print(f"Mở trình duyệt tại {server.url}  (chế độ {a.mode}, seed {a.seed}). Ctrl+C để dừng.", flush=True)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
