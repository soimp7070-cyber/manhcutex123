from __future__ import annotations
import json
import threading
import time
import random
import logging
import math
import re
import os
import sys
from collections import deque
from datetime import datetime
from typing import Any, Dict, Tuple, Optional, List, Union
from urllib.parse import urlparse, parse_qs

import pytz
import requests
import websocket

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("EscapeTool")

class GameConfig:
    def __init__(self):
        self.auto_bet_enabled = True
        self.base_bet = 1.0
        self.multiplier = 2.0
        self.run_mode = "AUTO"
        self.pause_after_losses = 0
        self.bet_rounds_before_skip = 0
        self.profit_target = None
        self.stop_loss_target = None
        self.user_id = None
        self.secret_key = None
        self.strategy = "MARTINGALE"
        self.mode = "NORMAL"
        self.max_bet_allowed = float("inf")
        self.max_players_allowed = 9999
        self.avoid_last_kill = True
        self.max_recent_kills = 3
        self.min_survive_rate = 0.5

class GameStateB5:
    def __init__(self, user_id: int, config: GameConfig):
        self.user_id = user_id
        self.config = config
        self.running = False
        self.stop_flag = False

        self.USER_ID = config.user_id
        self.SECRET_KEY = config.secret_key

        self.BET_API_URL = "https://api.escapemaster.net/escape_game/bet"
        self.WS_URL = "wss://api.escapemaster.net/escape_master/ws"
        self.WALLET_API_URL = "https://wallet.3games.io/api/wallet/user_asset"

        self.HTTP = requests.Session()
        try:
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            adapter = HTTPAdapter(pool_connections=20, pool_maxsize=50,
                                  max_retries=Retry(total=3, backoff_factor=0.2,
                                                    status_forcelist=(500, 502, 503, 504)))
            self.HTTP.mount("https://", adapter)
            self.HTTP.mount("http://", adapter)
        except Exception:
            pass

        self.ROOM_NAMES = {
            1: "📦 Nhà kho", 2: "🪑 Phòng họp", 3: "👔 Phòng giám đốc", 4: "💬 Phòng trò chuyện",
            5: "🎥 Phòng giám sát", 6: "🏢 Văn phòng", 7: "💰 Phòng tài vụ", 8: "👥 Phòng nhân sự"
        }
        self.ROOM_ORDER = [1, 2, 3, 4, 5, 6, 7, 8]

        self.issue_id = None
        self.issue_start_ts = None
        self.count_down = None
        self.killed_room = None
        self.round_index = 0

        self.room_state = {r: {"players": 0, "bet": 0} for r in self.ROOM_ORDER}
        self.room_stats = {r: {"kills": 0, "survives": 0, "last_kill_round": None, "last_players": 0, "last_bet": 0} for r in self.ROOM_ORDER}

        self.recent_issues = deque(maxlen=10)

        self.predicted_room = None
        self.last_killed_room = None
        self.prediction_locked = False

        self.current_build = None
        self.current_usdt = None
        self.current_world = None
        self.last_balance_ts = None
        self.last_balance_val = None
        self.starting_balance = None
        self.cumulative_profit = 0.0

        self.win_streak = 0
        self.lose_streak = 0
        self.max_win_streak = 0
        self.max_lose_streak = 0

        self.total_bets = 0
        self.total_wins = 0
        self.win_rate = 0.0

        self.current_bet = config.base_bet
        self.bet_history = deque(maxlen=500)
        self.bet_sent_for_issue = set()

        self._rounds_placed_since_skip = 0
        self.skip_next_round_flag = False
        self._skip_rounds_remaining = 0

        self.ui_state = "IDLE"
        self.analysis_start_ts = None

        self._ws = {"ws": None}
        self.last_msg_ts = time.time()
        self.last_balance_fetch_ts = 0.0
        self.BALANCE_POLL_INTERVAL = 4.0

        self._num_re = re.compile(r"-?\d+[\d,]*\.?\d*")
        self.tz = pytz.timezone("Asia/Ho_Chi_Minh")

        self.SELECTION_CONFIG = {
            "max_bet_allowed": float("inf"),
            "max_players_allowed": 9999,
            "avoid_last_kill": True,
            "max_recent_kills": 3,
            "min_survive_rate": 0.5,
            "bet_management_strategy": self.config.strategy,
        }

        self.ws_connected = False
        self.ws_reconnect_attempts = 0
        self.max_reconnect_attempts = 10

    # ---------- Helper methods ----------
    def _parse_number(self, x: Any) -> Optional[float]:
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x)
        m = self._num_re.search(s)
        if not m:
            return None
        token = m.group(0).replace(",", "")
        try:
            return float(token)
        except Exception:
            return None

    def _parse_balance_from_json(self, j: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        if not isinstance(j, dict):
            return None, None, None
        build = None
        world = None
        usdt = None
        data = j.get("data") if isinstance(j.get("data"), dict) else j
        if isinstance(data, dict):
            cwallet = data.get("cwallet") if isinstance(data.get("cwallet"), dict) else None
            if cwallet:
                for key in ("ctoken_contribute", "ctoken", "build", "balance", "amount"):
                    if key in cwallet and build is None:
                        build = self._parse_number(cwallet.get(key))
            for k in ("build", "ctoken", "ctoken_contribute"):
                if build is None and k in data:
                    build = self._parse_number(data.get(k))
            for k in ("usdt", "kusdt", "usdt_balance"):
                if usdt is None and k in data:
                    usdt = self._parse_number(data.get(k))
            for k in ("world", "xworld"):
                if world is None and k in data:
                    world = self._parse_number(data.get(k))
        found = []
        def walk(o: Any, path=""):
            if isinstance(o, dict):
                for kk, vv in o.items():
                    nk = (path + "." + str(kk)).strip(".")
                    if isinstance(vv, (dict, list)):
                        walk(vv, nk)
                    else:
                        n = self._parse_number(vv)
                        if n is not None:
                            found.append((nk.lower(), n))
            elif isinstance(o, list):
                for idx, it in enumerate(o):
                    walk(it, f"{path}[{idx}]")
        walk(j)
        for k, n in found:
            if build is None and any(x in k for x in ("ctoken", "build", "contribute", "balance")):
                build = n
            if usdt is None and "usdt" in k:
                usdt = n
            if world is None and any(x in k for x in ("world", "xworld")):
                world = n
        return build, world, usdt

    def balance_headers_for(self, uid: Optional[int] = None, secret: Optional[str] = None) -> Dict[str, str]:
        h = {
            "accept": "*/*",
            "accept-language": "vi,en;q=0.9",
            "cache-control": "no-cache",
            "country-code": "vn",
            "origin": "https://xworld.info",
            "pragma": "no-cache",
            "referer": "https://xworld.info/",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
            "user-login": "login_v2",
            "xb-language": "vi-VN",
        }
        if uid is not None:
            h["user-id"] = str(uid)
        if secret:
            h["user-secret-key"] = str(secret)
        return h

    def fetch_balances_3games(self, retries: int = 2, timeout: int = 10) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        payload = {"user_id": int(self.USER_ID) if self.USER_ID is not None else None, "source": "home"}
        attempt = 0
        while attempt <= retries:
            attempt += 1
            try:
                r = self.HTTP.post(
                    self.WALLET_API_URL,
                    json=payload,
                    headers=self.balance_headers_for(self.USER_ID, self.SECRET_KEY),
                    timeout=timeout,
                )
                if r.status_code != 200:
                    logger.warning(f"Wallet API trả về mã lỗi: {r.status_code}")
                    if attempt <= retries:
                        time.sleep(min(0.8 * attempt, 2))
                        continue
                    return self.current_build, self.current_world, self.current_usdt
                j = r.json()
                build, world, usdt = self._parse_balance_from_json(j)
                if build is not None:
                    if self.last_balance_val is None:
                        self.starting_balance = build
                        self.last_balance_val = build
                    else:
                        delta = float(build) - float(self.last_balance_val)
                        if abs(delta) > 0.000001:
                            self.cumulative_profit += delta
                            self.last_balance_val = build
                    self.current_build = build
                if usdt is not None:
                    self.current_usdt = usdt
                if world is not None:
                    self.current_world = world
                self.last_balance_ts = time.time()
                return self.current_build, self.current_world, self.current_usdt
            except Exception:
                if attempt <= retries:
                    time.sleep(min(0.8 * attempt, 2))
                    continue
        return self.current_build, self.current_world, self.current_usdt

    def api_headers(self) -> Dict[str, str]:
        return {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0",
            "user-id": str(self.USER_ID) if self.USER_ID else "",
            "user-secret-key": self.SECRET_KEY if self.SECRET_KEY else ""
        }

    def place_bet_http(self, issue: int, room_id: int, amount: float) -> dict:
        payload = {"asset_type": "BUILD", "user_id": self.USER_ID, "room_id": int(room_id), "bet_amount": float(amount)}
        try:
            r = self.HTTP.post(
                self.BET_API_URL,
                headers=self.api_headers(),
                json=payload,
                timeout=6,
            )
            try:
                return r.json()
            except Exception:
                return {"raw": r.text, "http_status": r.status_code}
        except Exception as e:
            return {"error": str(e)}

    def record_bet(self, issue: int, room_id: int, amount: float, resp: dict, algo_used: Optional[str] = None) -> dict:
        now = datetime.now(self.tz).strftime("%H:%M:%S")
        rec = {
            "issue": issue, "room": room_id, "amount": float(amount),
            "time": now, "resp": resp, "result": "Đang",
            "algo": algo_used, "delta": 0.0, "win_streak": self.win_streak,
            "lose_streak": self.lose_streak
        }
        self.bet_history.append(rec)
        return rec

    def place_bet_async(self, issue: int, room_id: int, amount: float, algo_used: Optional[str] = None) -> None:
        def worker():
            logger.info(f"Đang đặt {amount:,.4f} BUILD -> PHÒNG_{room_id} (v{issue}) — {algo_used}")
            time.sleep(random.uniform(0.02, 0.25))
            res = self.place_bet_http(self.issue_id, room_id, amount)
            rec = self.record_bet(self.issue_id, room_id, amount, res, algo_used=algo_used)
            if isinstance(res, dict) and (res.get("msg") == "ok" or res.get("code") == 0 or res.get("status") in ("ok", 1) or "success" in str(res).lower()):
                self.bet_sent_for_issue.add(self.issue_id)
                logger.info(f"✅ Đặt thành công {amount:,.4f} BUILD vào PHÒNG_{room_id} (v{self.issue_id}).")
            else:
                logger.error(f"❌ Đặt lỗi v{self.issue_id}: {res}")
        threading.Thread(target=worker, daemon=True).start()

    def safe_send_enter_game(self, ws: Optional[websocket.WebSocketApp]) -> None:
        if not ws:
            return
        try:
            payload = {"msg_type": "handle_enter_game", "asset_type": "BUILD", "user_id": self.USER_ID, "user_secret_key": self.SECRET_KEY}
            ws.send(json.dumps(payload))
            logger.info(f"✅ Đã gửi handle_enter_game cho user {self.USER_ID}")
        except Exception as e:
            logger.error(f"safe_send_enter_game err: {e}")

    def _extract_issue_id(self, d: Dict[str, Any]) -> Optional[int]:
        if not isinstance(d, dict):
            return None
        possible = []
        for key in ("issue_id", "issueId", "issue", "id"):
            v = d.get(key)
            if v is not None:
                possible.append(v)
        if isinstance(d.get("data"), dict):
            for key in ("issue_id", "issueId", "issue", "id"):
                v = d["data"].get(key)
                if v is not None:
                    possible.append(v)
        for p in possible:
            try:
                return int(p)
            except Exception:
                try:
                    return int(str(p))
                except Exception:
                    continue
        return None

    def on_open(self, ws: websocket.WebSocketApp) -> None:
        self._ws["ws"] = ws
        self.ws_connected = True
        self.ws_reconnect_attempts = 0
        logger.info("✅ WebSocket kết nối thành công!")
        self.safe_send_enter_game(ws)

    def _background_fetch_balance_after_result(self) -> None:
        try:
            self.fetch_balances_3games()
        except Exception:
            pass

    def _update_win_rate(self, is_win: bool):
        self.total_bets += 1
        if is_win:
            self.total_wins += 1
        self.win_rate = (self.total_wins / self.total_bets * 100) if self.total_bets > 0 else 0.0

    def _mark_bet_result_from_issue(self, res_issue: Optional[int], krid: int) -> None:
        if res_issue is None:
            return
        rec = None
        for b in reversed(list(self.bet_history)):
            if b.get("issue") == res_issue:
                rec = b
                break
        if rec is None:
            return
        try:
            placed_room = int(rec.get("room"))
            placed_amount = float(rec.get("amount"))
            is_win = (placed_room != int(krid))
            delta = 0.0
            if is_win:
                rec["result"] = "Thắng"
                delta = placed_amount
                self._update_win_rate(True)
                if self.SELECTION_CONFIG.get("bet_management_strategy") == "MARTINGALE":
                    self.current_bet = self.config.base_bet
                self.win_streak += 1
                self.lose_streak = 0
                if self.win_streak > self.max_win_streak:
                    self.max_win_streak = self.win_streak
            else:
                rec["result"] = "Thua"
                delta = -placed_amount
                self._update_win_rate(False)
                if self.SELECTION_CONFIG.get("bet_management_strategy") == "MARTINGALE":
                    try:
                        self.current_bet = placed_amount * float(self.config.multiplier)
                    except Exception:
                        self.current_bet = self.config.base_bet
                else:
                    self.current_bet = self.config.base_bet
                self.lose_streak += 1
                self.win_streak = 0
                if self.lose_streak > self.max_lose_streak:
                    self.max_lose_streak = self.lose_streak
                if self.config.pause_after_losses > 0:
                    self._skip_rounds_remaining = self.config.pause_after_losses
            rec["delta"] = delta
        except Exception as e:
            logger.error(f"_mark_bet_result_from_issue err: {e}")

    def on_message(self, ws: websocket.WebSocketApp, message: Union[str, bytes]) -> None:
        self.last_msg_ts = time.time()
        try:
            if isinstance(message, bytes):
                try:
                    message = message.decode("utf-8", errors="replace")
                except Exception:
                    message = str(message)
            data = None
            try:
                data = json.loads(message)
            except Exception:
                try:
                    data = json.loads(message.replace("'", '"'))
                except Exception:
                    return
            if isinstance(data, dict) and isinstance(data.get("data"), str):
                try:
                    inner = json.loads(data.get("data"))
                    merged = dict(data)
                    merged.update(inner)
                    data = merged
                except Exception:
                    pass
            msg_type = data.get("msg_type") or data.get("type") or ""
            msg_type = str(msg_type)
            new_issue = self._extract_issue_id(data)

            if msg_type == "notify_issue_stat" or "issue_stat" in msg_type:
                rooms = data.get("rooms") or []
                if not rooms and isinstance(data.get("data"), dict):
                    rooms = data["data"].get("rooms", [])
                for rm in (rooms or []):
                    try:
                        rid = int(rm.get("room_id") or rm.get("roomId") or rm.get("id"))
                        bet = float(rm.get("total_bet_amount") or rm.get("totalBet") or rm.get("bet") or 0) or 0
                        players = int(rm.get("user_cnt") or rm.get("userCount") or 0) or 0
                        self.room_state[rid] = {"players": players, "bet": bet}
                        self.room_stats[rid]["last_players"] = players
                        self.room_stats[rid]["last_bet"] = bet
                    except Exception:
                        continue

                if new_issue is not None and new_issue != self.issue_id:
                    logger.info(f"New issue: {self.issue_id} -> {new_issue}")
                    if self.issue_id is not None and self.killed_room is not None:
                        self.recent_issues.append({
                            "issue_id": self.issue_id,
                            "room_bets": {r: self.room_state.get(r, {}).get("bet", 0) for r in self.ROOM_ORDER},
                            "killed_room": self.killed_room
                        })
                    self.issue_id = new_issue
                    self.issue_start_ts = time.time()
                    self.killed_room = None
                    self.prediction_locked = False
                    self.predicted_room = None
                    if self.ui_state == "RESULT":
                        self.round_index += 1
                    self.ui_state = "ANALYZING"
                    self.analysis_start_ts = time.time()

            elif msg_type == "notify_count_down" or "count_down" in msg_type:
                count_down_val = data.get("count_down") or data.get("countDown") or data.get("count") or self.count_down
                try:
                    count_val = int(count_down_val)
                    self.count_down = count_val
                except Exception:
                    count_val = None
                if count_val is not None:
                    try:
                        if count_val <= 10 and not self.prediction_locked:
                            self.lock_prediction_if_needed()
                        elif count_val <= 45:
                            self.ui_state = "ANALYZING"
                            self.analysis_start_ts = time.time()
                    except Exception as e:
                        logger.error(f"Countdown logic error: {e}")

            elif msg_type == "notify_result" or "result" in msg_type:
                kr = data.get("killed_room") if data.get("killed_room") is not None else data.get("killed_room_id")
                if kr is None and isinstance(data.get("data"), dict):
                    kr = data["data"].get("killed_room") or data["data"].get("killed_room_id")
                if kr is not None:
                    try:
                        krid = int(kr)
                    except Exception:
                        krid = kr
                    self.killed_room = krid
                    self.last_killed_room = krid
                    for rid in self.ROOM_ORDER:
                        if rid == krid:
                            self.room_stats[rid]["kills"] += 1
                            self.room_stats[rid]["last_kill_round"] = self.round_index
                        else:
                            self.room_stats[rid]["survives"] += 1
                    res_issue = new_issue if new_issue is not None else self.issue_id
                    self._mark_bet_result_from_issue(res_issue, krid)
                    threading.Thread(target=self._background_fetch_balance_after_result, daemon=True).start()
                self.ui_state = "RESULT"

                def send_enter_game_after_result():
                    time.sleep(1)
                    self.safe_send_enter_game(self._ws.get("ws"))
                threading.Thread(target=send_enter_game_after_result, daemon=True).start()

                # ================== SỬA LỖI ĐIỀU KIỆN DỪNG ==================
                def _check_stop_conditions():
                    try:
                        # Dừng khi đạt lợi nhuận mục tiêu (lãi dương)
                        if self.config.profit_target is not None and self.cumulative_profit >= self.config.profit_target:
                            logger.info(f"🎉 MỤC TIÊU LÃI ĐẠT: {self.cumulative_profit:+,.4f} >= {self.config.profit_target:+,.4f}. Dừng tool.")
                            self.stop_flag = True
                            try:
                                wsobj = self._ws.get("ws")
                                if wsobj:
                                    wsobj.close()
                            except Exception:
                                pass
                        # Dừng khi lỗ vượt quá mức cắt lỗ (lỗ âm)
                        if self.config.stop_loss_target is not None and self.cumulative_profit <= -self.config.stop_loss_target:
                            logger.info(f"⚠️ STOP-LOSS TRIGGER: lỗ {self.cumulative_profit:+,.4f} <= -{self.config.stop_loss_target:+,.4f}. Dừng tool.")
                            self.stop_flag = True
                            try:
                                wsobj = self._ws.get("ws")
                                if wsobj:
                                    wsobj.close()
                            except Exception:
                                pass
                    except Exception as e:
                        logger.error(f"Stop conditions check error: {e}")
                threading.Timer(1.2, _check_stop_conditions).start()
        except Exception as e:
            logger.error(f"on_message err: {e}")

    def on_close(self, ws: websocket.WebSocketApp, code: int, reason: str) -> None:
        self.ws_connected = False
        logger.info(f"WS closed: {code} {reason}")

    def on_error(self, ws: websocket.WebSocketApp, err: Union[Exception, str]) -> None:
        logger.error(f"WS error: {err}")

    def start_ws(self) -> None:
        backoff = 0.6
        self.ws_reconnect_attempts = 0
        while not self.stop_flag and self.ws_reconnect_attempts < self.max_reconnect_attempts:
            try:
                logger.info(f"Đang kết nối WebSocket... (lần thử {self.ws_reconnect_attempts + 1})")
                ws_app = websocket.WebSocketApp(
                    self.WS_URL,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_close=self.on_close,
                    on_error=self.on_error
                )
                self._ws["ws"] = ws_app
                ws_app.run_forever(ping_interval=10, ping_timeout=5)
            except Exception as e:
                logger.error(f"start_ws exception: {e}")
                self.ws_reconnect_attempts += 1
            if self.stop_flag:
                break
            if self.ws_reconnect_attempts >= self.max_reconnect_attempts:
                logger.error(f"Đã thử kết nối {self.max_reconnect_attempts} lần nhưng không thành công. Dừng thử.")
                self.stop_flag = True
                break
            t = min(backoff + random.random() * 0.5, 30)
            logger.info(f"Reconnect WS after {t}s")
            time.sleep(t)
            backoff = min(backoff * 1.5, 30)

    def monitor_loop(self) -> None:
        while not self.stop_flag:
            now = time.time()
            if now - self.last_balance_fetch_ts >= self.BALANCE_POLL_INTERVAL * 2:
                self.last_balance_fetch_ts = now
                try:
                    self.fetch_balances_3games()
                except Exception as e:
                    logger.error(f"monitor fetch err: {e}")
            if now - self.last_msg_ts > 15:
                logger.info("No ws msg >15s, send enter_game to keep alive")
                try:
                    self.safe_send_enter_game(self._ws.get("ws"))
                except Exception as e:
                    logger.error(f"monitor send err: {e}")
            if now - self.last_msg_ts > 30:
                logger.info("No ws msg >30s, force reconnect")
                try:
                    wsobj = self._ws.get("ws")
                    if wsobj:
                        try:
                            wsobj.close()
                        except Exception:
                            pass
                except Exception:
                    pass
            time.sleep(1)

    # ---------- Phân tích chế độ Vua ----------
    def analyze_king_mode(self) -> Tuple[Optional[int], float]:
        if len(self.recent_issues) < 5:
            logger.info("Chế độ Vua: chưa đủ 5 phiên để phân tích, tạm thời dùng chế độ thường.")
            return None, 0.0

        room_avg_bet = {r: 0.0 for r in self.ROOM_ORDER}
        room_bet_std = {r: 0.0 for r in self.ROOM_ORDER}
        bet_values = {r: [] for r in self.ROOM_ORDER}

        for issue in self.recent_issues:
            for r in self.ROOM_ORDER:
                bet = issue["room_bets"].get(r, 0)
                bet_values[r].append(bet)

        for r in self.ROOM_ORDER:
            if bet_values[r]:
                avg = sum(bet_values[r]) / len(bet_values[r])
                room_avg_bet[r] = avg
                variance = sum((x - avg) ** 2 for x in bet_values[r]) / len(bet_values[r])
                room_bet_std[r] = math.sqrt(variance)

        abnormal_rooms = set()
        for r in self.ROOM_ORDER:
            current_bet = self.room_state.get(r, {}).get("bet", 0)
            avg = room_avg_bet[r]
            std = room_bet_std[r]
            if std > 0 and current_bet > avg + 2 * std:
                abnormal_rooms.add(r)
                logger.debug(f"Phòng {r} bất thường: bet hiện tại={current_bet}, avg={avg:.0f}, std={std:.0f}")

        safe_candidates = []
        for r in self.ROOM_ORDER:
            if r in abnormal_rooms:
                continue
            current_bet = self.room_state.get(r, {}).get("bet", 0)
            if current_bet > 100_000:
                continue
            kills = self.room_stats[r]["kills"]
            survives = self.room_stats[r]["survives"]
            total = kills + survives
            survive_rate = survives / total if total > 0 else 0.5
            if survive_rate < 0.6:
                continue
            avg_bet = room_avg_bet[r]
            if avg_bet > 0:
                volatility = room_bet_std[r] / avg_bet
            else:
                volatility = 1.0
            score = current_bet + volatility * 1000
            safe_candidates.append((r, score))

        if not safe_candidates:
            logger.info("Chế độ Vua: không tìm thấy phòng an toàn, bỏ qua ván này.")
            return None, 0.0

        best_room = min(safe_candidates, key=lambda x: x[1])[0]
        kills = self.room_stats[best_room]["kills"]
        survives = self.room_stats[best_room]["survives"]
        total = kills + survives
        if total > 0:
            base_rate = survives / total
        else:
            base_rate = 0.5
        players = self.room_state.get(best_room, {}).get("players", 0)
        if players < 10:
            base_rate *= 0.9
        elif players > 50:
            base_rate *= 1.05
        win_prob = min(0.95, max(0.3, base_rate)) * 100
        logger.info(f"Chế độ Vua: chọn phòng {best_room} với tỉ lệ thắng ước tính {win_prob:.1f}%")
        return best_room, win_prob

    # ---------- Thuật toán thường ----------
    def _room_features(self, rid: int) -> Dict[str, float]:
        st = self.room_state.get(rid, {})
        stats = self.room_stats.get(rid, {})
        players = float(st.get("players", 0))
        bet = float(st.get("bet", 0))
        bet_per_player = (bet / players) if players > 0 else bet
        kill_count = float(stats.get("kills", 0))
        survive_count = float(stats.get("survives", 0))
        total_rounds = kill_count + survive_count
        kill_rate = (kill_count + 1.0) / (total_rounds + 2.0) if total_rounds > 0 else 0.5
        survive_score = 1.0 - kill_rate
        recent_history = list(self.bet_history)
        recent_pen = 0.0
        for i, rec in enumerate(reversed(recent_history)):
            if rec.get("room") == rid and rec.get("result") == "Thua":
                recent_pen += 0.15 * (1.0 / (i + 1))
        last_pen = 0.0
        if self.last_killed_room == rid and self.SELECTION_CONFIG.get("avoid_last_kill", True):
            last_pen = 0.45
        players_norm = min(1.0, players / 70.0)
        bet_norm = 1.0 / (1.0 + bet / 3000.0)
        bpp_norm = 1.0 / (1.0 + bet_per_player / 1500.0)
        total_rounds_stats = sum(r['kills'] + r['survives'] for r in self.room_stats.values())
        safety_score = 0.5
        if total_rounds_stats > 0:
            safety_score = 1.0 - (kill_count / total_rounds_stats)
        return {
            "players": players, "players_norm": players_norm,
            "bet": bet, "bet_norm": bet_norm,
            "bet_per_player": bet_per_player, "bpp_norm": bpp_norm,
            "kill_rate": kill_rate, "survive_score": survive_score,
            "recent_pen": recent_pen, "last_pen": last_pen,
            "safety_score": safety_score
        }

    def choose_room_normal(self) -> Tuple[int, str]:
        filtered_cand = []
        for r in self.ROOM_ORDER:
            f = self._room_features(r)
            if self.SELECTION_CONFIG.get("avoid_last_kill", True) and self.last_killed_room == r:
                continue
            if f["survive_score"] < self.SELECTION_CONFIG.get("min_survive_rate", 0.5):
                continue
            if f["players"] > 100 or f["bet"] > 50000:
                continue
            if f["players"] < 3 or f["bet"] < 500:
                continue
            if f["safety_score"] < 0.7:
                continue
            filtered_cand.append(r)
        if not filtered_cand:
            fallback_scores = {r: self._room_features(r)["kill_rate"] for r in self.ROOM_ORDER}
            best_room = min(fallback_scores.items(), key=lambda x: x[1])[0]
            return best_room, "GODMODE_FALLBACK"
        seed = 1234567
        rng = random.Random(seed)
        formulas = []
        for i in range(100):
            w_players = rng.uniform(0.15, 0.85)
            w_bet = rng.uniform(0.05, 0.7)
            w_bpp = rng.uniform(0.03, 0.65)
            w_survive = rng.uniform(0.03, 0.45)
            w_recent = rng.uniform(0.03, 0.35)
            w_last = rng.uniform(0.05, 0.7)
            noise_scale = rng.uniform(0.0, 0.08)
            formulas.append((w_players, w_bet, w_bpp, w_survive, w_recent, w_last, noise_scale))
        agg_scores = {r: 0.0 for r in filtered_cand}
        for idx, wset in enumerate(formulas):
            for r in filtered_cand:
                f = self._room_features(r)
                score = 0.0
                score += wset[0] * f["players_norm"]
                score += wset[1] * f["bet_norm"]
                score += wset[2] * f["bpp_norm"]
                score += wset[3] * f["survive_score"]
                score += wset[3] * f["safety_score"]
                score -= wset[4] * f["recent_pen"]
                score -= wset[5] * f["last_pen"]
                noise = (math.sin((idx + 1) * (r + 1) * 12.9898) * 43758.5453) % 1.0
                noise = (noise - 0.5) * (wset[6] * 2.0)
                score += noise
                agg_scores[r] += score
        for r in agg_scores:
            agg_scores[r] /= len(formulas)
        ranked = sorted(agg_scores.items(), key=lambda kv: (-kv[1], kv[0]))
        best_room = ranked[0][0]
        return best_room, "GODMODE"

    def choose_room(self) -> Tuple[int, str, float]:
        if self.config.mode == "KING":
            king_room, prob = self.analyze_king_mode()
            if king_room is not None and prob >= 80.0:
                return king_room, "CHẾ ĐỘ VUA", prob
            else:
                logger.info(f"Chế độ Vua: tỉ lệ thắng {prob:.1f}% < 80%, chuyển sang chế độ thường.")
                room, algo = self.choose_room_normal()
                return room, algo, self.win_rate
        else:
            room, algo = self.choose_room_normal()
            return room, algo, self.win_rate

    # ---------- Quyết định đặt cược ----------
    def lock_prediction_if_needed(self, force: bool = False) -> None:
        if self.stop_flag:
            return
        if self.prediction_locked and not force:
            return
        if self.issue_id is None:
            logger.warning("Chưa có issue_id, chưa thể đặt cược.")
            return

        total_bet_in_rooms = sum(self.room_state.get(r, {}).get("bet", 0) for r in self.ROOM_ORDER)
        if total_bet_in_rooms == 0:
            logger.warning("Chưa nhận được dữ liệu phòng (room_state trống), bỏ qua đặt cược ván này.")
            self.prediction_locked = True
            return

        self.prediction_locked = True
        self.ui_state = "PREDICTED"

        chosen, algo_used, win_prob = self.choose_room()
        self.predicted_room = chosen

        if self._skip_rounds_remaining > 0:
            self._skip_rounds_remaining -= 1
            logger.info(f"Tạm nghỉ {self._skip_rounds_remaining} ván còn lại.")
            return

        if self.config.run_mode == "AUTO" and not self.skip_next_round_flag:
            if not self.config.auto_bet_enabled:
                self.record_bet(self.issue_id, self.predicted_room, 0.0, {"msg": "simulation"}, algo_used=algo_used)
                return

            bld, _, _ = self.fetch_balances_3games()
            if bld is None:
                logger.error("Không lấy được số dư, bỏ qua đặt cược.")
                self.prediction_locked = False
                return

            if self.current_bet is None:
                self.current_bet = self.config.base_bet

            if self.SELECTION_CONFIG.get("bet_management_strategy") == "ANTI-MARTINGALE":
                if self.win_streak > 0:
                    self.current_bet = self.config.base_bet + (self.config.base_bet * 0.1 * self.win_streak)
                else:
                    self.current_bet = self.config.base_bet

            if self.current_bet < self.config.base_bet:
                self.current_bet = self.config.base_bet

            amt = float(self.current_bet)
            if amt <= 0:
                logger.warning(f"Số tiền cược không hợp lệ: {amt}")
                self.prediction_locked = False
                return
            if amt > bld:
                logger.warning(f"Số dư không đủ: cần {amt} nhưng chỉ có {bld}")
                self.prediction_locked = False
                return

            logger.info(f"🎯 Quyết định: đặt {amt:.2f} BUILD vào phòng {chosen} (thuật toán {algo_used}, tỉ lệ thắng ước tính {win_prob:.1f}%)")
            self.place_bet_async(self.issue_id, self.predicted_room, amt, algo_used=algo_used)

            self._rounds_placed_since_skip += 1
            if self.config.bet_rounds_before_skip > 0 and self._rounds_placed_since_skip >= self.config.bet_rounds_before_skip:
                self.skip_next_round_flag = True
                self._rounds_placed_since_skip = 0
        elif self.skip_next_round_flag:
            self.skip_next_round_flag = False
            logger.info("Bỏ qua ván này do chống soi.")
            return

    # ---------- Điều khiển game ----------
    def start_game(self) -> None:
        self.running = True
        self.stop_flag = False
        self.fetch_balances_3games()
        self.ws_thread = threading.Thread(target=self.start_ws, daemon=True)
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.ws_thread.start()
        self.monitor_thread.start()
        logger.info(f"Game started for user {self.user_id} (Mode: {self.config.mode})")

    def stop_game(self) -> None:
        self.stop_flag = True
        self.running = False
        try:
            wsobj = self._ws.get("ws")
            if wsobj:
                wsobj.close()
        except Exception:
            pass
        logger.info(f"Game stopped for user {self.user_id}")

    # ---------- Hiển thị console ----------
    def get_game_info(self) -> str:
        if not self.ws_connected:
            return "🔄 ĐANG KẾT NỐI WEBSOCKET...\nChờ trong giây lát..."
        lines = []
        crown = "👑 " if self.config.mode == "KING" else ""
        lines.append(f"{crown}ESCAPE VIP - GODMODE CHIẾN THẦN PROMAX - Chế độ {self.config.mode}")
        lines.append(f"🕐 {datetime.now(self.tz).strftime('%H:%M:%S')}")
        if self.issue_id:
            lines.append(f"🎯 Phiên #{self.issue_id}")
        if self.count_down:
            lines.append(f"⏳ Thời gian còn lại: {self.count_down}s")
        balance_display = f"{self.current_build:,.4f}" if self.current_build else "Đang tải..."
        lines.append(f"💰 Số dư BUILD: {balance_display}")
        profit_style = "🟢" if self.cumulative_profit >= 0 else "🔴"
        lines.append(f"{profit_style} Lãi/Lỗ: {self.cumulative_profit:+,.4f} BUILD")
        lines.append(f"📈 Chuỗi: 🟢{self.win_streak} | 🔴{self.lose_streak}")
        lines.append(f"🏆 Chuỗi MAX: 🟢{self.max_win_streak} | 🔴{self.max_lose_streak}")
        lines.append(f"📊 Tỉ lệ thắng: {self.win_rate:.1f}% ({self.total_wins}/{self.total_bets})")
        status_map = {"IDLE": "Chờ dữ liệu", "ANALYZING": "Đang phân tích", "PREDICTED": "Đã dự đoán", "RESULT": "Chờ kết quả"}
        lines.append(f"📊 Trạng thái: {status_map.get(self.ui_state, self.ui_state)}")
        if self.predicted_room:
            room_name = self.ROOM_NAMES.get(self.predicted_room, f"P{self.predicted_room}")
            lines.append(f"🎯 Dự đoán AI: {room_name}")
        if self.last_killed_room:
            room_name = self.ROOM_NAMES.get(self.last_killed_room, f"P{self.last_killed_room}")
            lines.append(f"☠️ Sát thủ vừa rồi: {room_name}")
        if self.current_bet:
            lines.append(f"💰 Cược tiếp theo: {self.current_bet:,.4f} BUILD")
        lines.append("\n📊 THÔNG TIN PHÒNG:")
        for rid in self.ROOM_ORDER:
            st = self.room_state.get(rid, {})
            players = st.get('players', 0)
            bet = st.get('bet', 0)
            bet_display = f"{bet:,.0f}" if bet >= 1000 else f"{bet:.2f}"
            bpp = bet / players if players > 0 else 0
            bpp_display = f"{bpp:,.0f}" if bpp >= 1000 else f"{bpp:.2f}"
            status = ""
            if self.killed_room == rid:
                status = " ☠️"
            elif self.predicted_room == rid:
                status = " ✅"
            room_name = self.ROOM_NAMES.get(rid, f"P{rid}")
            lines.append(f"{room_name}: {players}👥 | {bet_display}🪙 | {bpp_display}⌀{status}")
        if self.bet_history:
            lines.append("\n📜 LỊCH SỬ GẦN ĐÂY:")
            for bet in reversed(list(self.bet_history)[-3:]):
                result = "🟢" if bet.get('result') == 'Thắng' else ("🔴" if bet.get('result') == 'Thua' else "⚪")
                lines.append(f"V{bet.get('issue')}: {result} P{bet.get('room')} | {bet.get('amount'):,.2f}")
        if self.config.profit_target:
            lines.append(f"\n🏆 Chốt lời: {self.config.profit_target:,.2f} BUILD")
        if self.config.stop_loss_target:
            lines.append(f"🛡️ Cắt lỗ: {self.config.stop_loss_target:,.2f} BUILD")
        lines.append("\nNhấn Ctrl+C để dừng game.")
        return "\n".join(lines)

# ==================== CONSOLE DISPLAY ====================
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def console_display(game_state: GameStateB5):
    while game_state.running and not game_state.stop_flag:
        clear_screen()
        info = game_state.get_game_info()
        print(info)
        time.sleep(3)

# ==================== MAIN ====================
def main():
    print("=" * 60)
    print("ESCAPE VIP PROMAX - GODMODE CHIẾN THẦN (ĐÃ SỬA LỖI DỪNG MỤC TIÊU)")
    print("=" * 60)
    print("Tool chạy hoàn toàn trên console, không cần Telegram.")
    print()

    link_or_userid = input("User ID (hoặc link chứa userId&secretKey): ").strip()
    secret = input("Secret Key (nếu đã nhập link có thể bỏ qua): ").strip()

    user_id = None
    secret_key = None
    if "http" in link_or_userid:
        parsed = urlparse(link_or_userid)
        params = parse_qs(parsed.query)
        user_id_str = params.get('userId', [None])[0] or params.get('uid', [None])[0]
        if user_id_str:
            user_id = int(user_id_str)
        secret_key = params.get('secretKey', [None])[0] or params.get('secret', [None])[0] or secret
    else:
        try:
            user_id = int(link_or_userid)
        except:
            print("❌ User ID không hợp lệ.")
            return
        secret_key = secret

    if not user_id or not secret_key:
        print("❌ Thiếu userId hoặc secretKey.")
        return

    print("\n--- CẤU HÌNH CƯỢC ---")
    mode_choice = input("Chọn chế độ (1: NORMAL - Thường, 2: KING - Vua): ").strip()
    mode = "KING" if mode_choice == "2" else "NORMAL"

    base_bet = float(input("Số BUILD cược mỗi ván (vd: 1.0): ") or "1.0")
    multiplier = float(input("Hệ số nhân (vd: 2.0): ") or "2.0")

    strategy_choice = input("Chọn chiến lược (1: MARTINGALE, 2: ANTI-MARTINGALE): ").strip()
    strategy = "MARTINGALE" if strategy_choice == "1" else "ANTI-MARTINGALE"

    skip_rounds = int(input("Chống soi: sau mấy ván thì nghỉ 1 ván (0=tắt): ") or "0")
    pause_losses = int(input("Nghỉ sau thua liên tiếp mấy lần (0=tắt): ") or "0")
    profit_target = input("Mục tiêu lời (BUILD, bỏ trống nếu không): ").strip()
    profit_target = float(profit_target) if profit_target else None
    stop_loss = input("Mức cắt lỗ (BUILD, bỏ trống nếu không): ").strip()
    stop_loss = float(stop_loss) if stop_loss else None

    config = GameConfig()
    config.user_id = user_id
    config.secret_key = secret_key
    config.auto_bet_enabled = True
    config.base_bet = base_bet
    config.multiplier = multiplier
    config.strategy = strategy
    config.bet_rounds_before_skip = skip_rounds
    config.pause_after_losses = pause_losses
    config.profit_target = profit_target
    config.stop_loss_target = stop_loss
    config.mode = mode

    print("\n" + "="*60)
    print(f"ĐANG KHỞI ĐỘNG GAME (Chế độ {mode})...")
    print("="*60)

    game_state = GameStateB5(user_id, config)
    game_state.start_game()

    display_thread = threading.Thread(target=console_display, args=(game_state,), daemon=True)
    display_thread.start()

    try:
        while game_state.running and not game_state.stop_flag:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⚠️ Đang dừng game...")
        game_state.stop_game()
        print("✅ Game đã dừng.")
        sys.exit(0)

if __name__ == "__main__":
    main()
