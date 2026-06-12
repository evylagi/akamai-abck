#!/usr/bin/env python3
"""
ABCK Token Server v2 — NO STORAGE MODE
Token masuk → langsung dipakai → langsung hilang. Tidak ada penyimpanan.
"""

import argparse
import os
import threading
import time
from collections import deque
from datetime import datetime

from flask import Flask, jsonify, request, Response, send_from_directory

# Fix: Serve React from dist, but API routes take priority
app = Flask(__name__, static_folder='dist', static_url_path='')

# ── Config ─────────────────────────────────────────────────────────────
TOKEN_TTL = 180

# ── State ──────────────────────────────────────────────────────────────
_lock = threading.Lock()
_token_queue = deque()
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
    now = time.time()
    removed = 0
    while _token_queue and (now - _token_queue[0]["ts"]) > TOKEN_TTL:
        _token_queue.popleft()
        removed += 1
    _stats["expired"] += removed
    return removed


def _cleanup_loop():
    while True:
        time.sleep(10)
        with _lock:
            _purge_expired()


_cleaner = threading.Thread(target=_cleanup_loop, daemon=True)
_cleaner.start()


# ── API ENDPOINTS (These MUST come BEFORE the React catch-all) ────────────────
@app.route("/api/save-token", methods=["POST"])
def receive_token():
    data = request.get_json(silent=True)
    if not data or "token" not in data:
        return jsonify({"error": "missing 'token' field"}), 400

    token = str(data["token"]).strip()
    if not token:
        return jsonify({"error": "empty token"}), 400

    with _lock:
        _purge_expired()
        now = time.time()
        _token_queue.append({"token": token, "ts": now})
        _stats["received"] += 1
        _stats["last_received"] = datetime.now().isoformat()
        queue_size = len(_token_queue)
        if queue_size > _stats["peak_queue"]:
            _stats["peak_queue"] = queue_size

    return jsonify({
        "status": "ok",
        "queue_size": queue_size,
        "total_received": _stats["received"],
    }), 200


@app.route("/api/get-token", methods=["GET"])
@app.route("/api/token", methods=["GET"])
def get_token():
    with _lock:
        _purge_expired()
        if _token_queue:
            entry = _token_queue.popleft()
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
    n = request.args.get("n", 1, type=int)
    n = max(1, min(n, 100))

    tokens = []
    with _lock:
        _purge_expired()
        for _ in range(n):
            if _token_queue:
                entry = _token_queue.popleft()
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
    with _lock:
        count = len(_token_queue)
        _token_queue.clear()
        _stats["flushed"] += count
    return jsonify({"status": "flushed", "removed": count}), 200


# ── REACT CATCH-ALL ROUTE (Must be LAST) ─────────────────────────────────────
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    """Serve React app for all non-API routes"""
    # Don't handle API routes here
    if path.startswith('api/'):
        return jsonify({"error": "API endpoint not found"}), 404
    
    # Check if it's a static file in dist
    if path and os.path.exists(os.path.join('dist', path)):
        return send_from_directory('dist', path)
    
    # For all other paths, serve index.html (React Router)
    return send_from_directory('dist', 'index.html')


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ABCK Token Server v2")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 5050)), help="Port")
    parser.add_argument("--ttl", type=int, default=180, help="Token TTL in seconds")
    args = parser.parse_args()

    TOKEN_TTL = args.ttl
    PORT = int(os.environ.get("PORT", args.port))

    print(f"\n  ⚡ ABCK Token Server v2 — WITH REACT SUPPORT")
    print(f"  ─────────────────────────────────────────")
    print(f"  Bind       : http://{args.host}:{PORT}")
    print(f"  Token TTL  : {TOKEN_TTL}s")
    print(f"  API        : http://{args.host}:{PORT}/api/status")
    print(f"  React App  : http://{args.host}:{PORT}/")
    print(f"  ─────────────────────────────────────────")
    print(f"  POST /api/save-token     — kirim token")
    print(f"  GET  /api/get-token      — ambil 1 token")
    print(f"  GET  /api/token/bulk?n=5 — ambil banyak")
    print(f"  GET  /api/status         — statistik")
    print(f"  DELETE /api/tokens       — flush queue")
    print()

    app.run(host=args.host, port=PORT, debug=False, threaded=True)