#!/usr/bin/env python3
"""
ABCK Token Server v2 — NO STORAGE MODE
Token masuk → langsung dipakai → langsung hilang. Tidak ada penyimpanan.

Endpoints:
  POST /api/save-token         — Kirim token baru  {"token": "..."}
  GET  /api/get-token          — Ambil 1 token dari queue (FIFO), langsung hapus
  GET  /api/token/bulk?n=5     — Ambil beberapa token sekaligus
  GET  /api/status             — Info queue & statistik
  DELETE /api/tokens           — Flush queue
  GET  /                       — Dashboard real-time (browser)

Jalankan:
  python server.py
  python server.py --port 5050
  python server.py --host 0.0.0.0 --port 8080
  python server.py --ttl 60         (token kadaluarsa 60 detik)
"""

import argparse
import os
import threading
import time
from collections import deque
from datetime import datetime

from flask import Flask, jsonify, request, Response, send_from_directory

app = Flask(__name__, static_folder='dist', static_url_path='')

# ── Config (diset dari argparse) ─────────────────────────────────────────────
TOKEN_TTL = 180  # detik, default 3 menit (cepat expire, no storage)

# ── State (NO STORAGE — hanya queue sementara) ──────────────────────────────
_lock = threading.Lock()
_token_queue = deque()          # deque of {"token": str, "ts": float}
_stats = {
    "received": 0,
    "served": 0,
    "expired": 0,
    "duplicates": 0,
    "flushed": 0,
    "start_time": time.time(),
    "peak_queue": 0,
    "last_received": None,
    "last_served": None,
}


# ── Helpers ──────────────────────────────────────────────────────────────────
def _purge_expired():
    """Buang token expired dari depan queue (caller harus sudah hold _lock)."""
    now = time.time()
    removed = 0
    while _token_queue and (now - _token_queue[0]["ts"]) > TOKEN_TTL:
        _token_queue.popleft()
        removed += 1
    _stats["expired"] += removed
    return removed


def _cleanup_loop():
    """Background thread: bersihkan token expired setiap 10 detik."""
    while True:
        time.sleep(10)
        with _lock:
            _purge_expired()


# ── Start cleanup thread ─────────────────────────────────────────────────────
_cleaner = threading.Thread(target=_cleanup_loop, daemon=True)
_cleaner.start()


# ── Endpoints ────────────────────────────────────────────────────────────────
@app.route("/api/save-token", methods=["POST"])
def receive_token():
    """Terima token baru dari ab.py generator."""
    data = request.get_json(silent=True)
    if not data or "token" not in data:
        return jsonify({"error": "missing 'token' field"}), 400

    token = str(data["token"]).strip()
    if not token:
        return jsonify({"error": "empty token"}), 400

    with _lock:
        _purge_expired()  # Bersihkan expired dulu
        now = time.time()
        _token_queue.append({"token": token, "ts": now})
        _stats["received"] += 1
        _stats["last_received"] = datetime.now().isoformat()
        queue_size = len(_token_queue)
        if queue_size > _stats["peak_queue"]:
            _stats["peak_queue"] = queue_size
        # Tidak ada penyimpanan ke disk / history

    return jsonify({
        "status": "ok",
        "queue_size": queue_size,
        "total_received": _stats["received"],
    }), 200


@app.route("/api/get-token", methods=["GET"])
@app.route("/api/token", methods=["GET"])
def get_token():
    """Ambil 1 token valid dari queue (FIFO), skip yang expired."""
    with _lock:
        _purge_expired()
        if _token_queue:
            entry = _token_queue.popleft()  # Ambil & langsung hapus
            _stats["served"] += 1
            _stats["last_served"] = datetime.now().isoformat()
            return jsonify({
                "token": entry["token"],
                "remaining": len(_token_queue),
                "age_seconds": round(time.time() - entry["ts"], 1),
            }), 200
        else:
            return jsonify({"error": "no tokens available", "remaining": 0}), 404


@app.route("/api/token/bulk", methods=["GET"])
def get_tokens_bulk():
    """Ambil beberapa token sekaligus. Query param: ?n=5"""
    n = request.args.get("n", 1, type=int)
    n = max(1, min(n, 100))

    tokens = []
    with _lock:
        _purge_expired()
        for _ in range(n):
            if _token_queue:
                entry = _token_queue.popleft()  # Ambil & langsung hapus
                tokens.append(entry["token"])
                _stats["served"] += 1
            else:
                break
        if tokens:
            _stats["last_served"] = datetime.now().isoformat()

    return jsonify({
        "tokens": tokens,
        "count": len(tokens),
        "remaining": len(_token_queue),
    }), 200


@app.route("/api/status", methods=["GET"])
def status():
    """Info queue & statistik."""
    with _lock:
        _purge_expired()
        elapsed = time.time() - _stats["start_time"]
        rate = _stats["received"] / (elapsed / 60) if elapsed > 0 else 0
        return jsonify({
            "queue_size": len(_token_queue),
            "total_received": _stats["received"],
            "total_served": _stats["served"],
            "total_expired": _stats["expired"],
            "total_duplicates": _stats["duplicates"],
            "total_flushed": _stats["flushed"],
            "peak_queue": _stats["peak_queue"],
            "uptime_seconds": round(elapsed, 1),
            "tokens_per_minute": round(rate, 2),
            "token_ttl_seconds": TOKEN_TTL,
            "last_received": _stats["last_received"],
            "last_served": _stats["last_served"],
        }), 200


@app.route("/api/tokens", methods=["DELETE"])
def flush_tokens():
    """Hapus semua token dari queue."""
    with _lock:
        count = len(_token_queue)
        _token_queue.clear()
        _stats["flushed"] += count
    return jsonify({"status": "flushed", "removed": count}), 200


# ── Dashboard HTML ───────────────────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="3">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ABCK Token Server</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:#0a0a0a;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:20px;font-size:clamp(12px,2vw,16px)}}
  h1{{color:#00e5ff;font-size:clamp(1.2rem,4vw,1.6rem);margin-bottom:6px}}
  .sub{{color:#666;font-size:.85rem;margin-bottom:24px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:14px;margin-bottom:28px}}
  .card{{background:#151515;border:1px solid #222;border-radius:10px;padding:14px 16px;text-align:center}}
  .card .val{{font-size:clamp(1.5rem,3vw,2rem);font-weight:700;color:#00e5ff}}
  .card .lbl{{font-size:.75rem;color:#888;margin-top:4px;text-transform:uppercase;letter-spacing:.5px}}
  .card.green .val{{color:#76ff03}}
  .card.orange .val{{color:#ff9100}}
  .card.red .val{{color:#ff1744}}
  .card.purple .val{{color:#d500f9}}
  .queue-bar{{background:#151515;border:1px solid #222;border-radius:10px;padding:16px 18px;margin-bottom:28px}}
  .queue-bar h3{{color:#888;font-size:.8rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}}
  .bar-outer{{background:#1a1a1a;border-radius:6px;height:26px;overflow:hidden}}
  .bar-inner{{background:linear-gradient(90deg,#00e5ff,#76ff03);height:100%;border-radius:6px;transition:width .5s ease;min-width:2px}}
  .bar-label{{font-size:.75rem;color:#666;margin-top:4px}}
  .ts{{color:#444;font-size:.75rem;text-align:center;margin-top:20px}}
  @media(max-width:640px){{
    body{{padding:16px}}
    .grid{{grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:10px}}
    .card{{padding:12px 14px}}
  }}
</style>
</head>
<body>
<h1>⚡ ABCK Token Server v2 — NO STORAGE</h1>
<p class="sub">Auto-refresh 3s &mdash; Token TTL: {ttl}s &mdash; Pakai langsung, hapus otomatis</p>
<div class="grid">
  <div class="card green"><div class="val">{queue}</div><div class="lbl">Queue</div></div>
  <div class="card"><div class="val">{received}</div><div class="lbl">Received</div></div>
  <div class="card orange"><div class="val">{served}</div><div class="lbl">Served</div></div>
  <div class="card red"><div class="val">{expired}</div><div class="lbl">Expired</div></div>
  <div class="card purple"><div class="val">{duplicates}</div><div class="lbl">Duplicates</div></div>
  <div class="card"><div class="val">{rate}</div><div class="lbl">Tok/min</div></div>
  <div class="card"><div class="val">{peak}</div><div class="lbl">Peak Queue</div></div>
  <div class="card"><div class="val">{uptime}</div><div class="lbl">Uptime (m)</div></div>
</div>
<div class="queue-bar">
  <h3>Queue Capacity</h3>
  <div class="bar-outer"><div class="bar-inner" style="width:{bar_pct}%"></div></div>
  <div class="bar-label">{queue} token(s) ready &mdash; peak {peak}</div>
</div>
<div class="ts">Last received: {last_recv} &nbsp;|&nbsp; Last served: {last_serv}</div>
</body>
</html>"""


@app.route("/")
def dashboard():
    """Dashboard real-time di browser."""
    with _lock:
        _purge_expired()
        elapsed = time.time() - _stats["start_time"]
        rate = _stats["received"] / (elapsed / 60) if elapsed > 0 else 0
        q = len(_token_queue)
        peak = _stats["peak_queue"] or 1
        bar_pct = min(int(q / peak * 100), 100) if peak else 0

    html = DASHBOARD_HTML.format(
        ttl=TOKEN_TTL,
        queue=q,
        received=_stats["received"],
        served=_stats["served"],
        expired=_stats["expired"],
        duplicates=_stats["duplicates"],
        rate=f"{rate:.1f}",
        peak=_stats["peak_queue"],
        uptime=f"{elapsed / 60:.1f}",
        bar_pct=bar_pct,
        last_recv=_stats["last_received"] or "-",
        last_serv=_stats["last_served"] or "-",
    )
    return Response(html, mimetype="text/html")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ABCK Token Server v2")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5050, help="Port (default 5050)")
    parser.add_argument("--ttl", type=int, default=180, help="Token TTL in seconds (default 180)")
    args = parser.parse_args()

    TOKEN_TTL = args.ttl

    print(f"\n  ⚡ ABCK Token Server v2 — NO STORAGE")
    print(f"  ─────────────────────────────────────────")
    print(f"  Mode       : Pakai langsung, hapus otomatis")
    print(f"  Bind       : http://{args.host}:{args.port}")
    print(f"  Token TTL  : {TOKEN_TTL}s")
    print(f"  Dashboard  : http://{args.host}:{args.port}/")
    print(f"  ─────────────────────────────────────────")
    print(f"  POST /api/save-token     — kirim token")
    print(f"  GET  /api/get-token      — ambil 1 token (langsung hapus)")
    print(f"  GET  /api/token/bulk?n=5 — ambil banyak (langsung hapus)")
    print(f"  GET  /api/status         — statistik")
    print(f"  DELETE /api/tokens       — flush queue")
    print()

    app.run(host=args.host, port=args.port, debug=False, threaded=True)
