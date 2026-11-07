import subprocess
import threading
import time
import json
import os
import re
import requests

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def send_webhook(url, content, embed=None):
    payload = {"content": content}
    if embed:
        payload["embeds"] = [embed]
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

def notify_task(cfg, msg):
    send_webhook(cfg["task_webhook"], msg)

def notify_found(cfg, msg, embed=None):
    send_webhook(cfg["found_webhook"], msg, embed)

def monitor_output(proc, cfg):
    hashrate_pattern = re.compile(r"speed\s+[\d.]+\s+[\d.]+\s+([\d.]+)\s+H/s")
    accepted_pattern = re.compile(r"accepted\s+\((\d+)/")
    share_pattern = re.compile(r"(accepted|rejected)")
    last_report = time.time()
    total_accepted = 0
    current_hashrate = "0"

    for line in iter(proc.stdout.readline, ""):
        line = line.strip()
        if not line:
            continue

        hr = hashrate_pattern.search(line)
        if hr:
            current_hashrate = hr.group(1)

        acc = accepted_pattern.search(line)
        if acc:
            new_total = int(acc.group(1))
            if new_total > total_accepted:
                total_accepted = new_total
                notify_found(cfg, None, embed={
                    "title": "share accepted",
                    "description": f"total accepted: **{total_accepted}**\nhashrate: **{current_hashrate} H/s**",
                    "color": 0x00ff88
                })

        if time.time() - last_report > 300:
            notify_task(cfg, f"**status** | hashrate: {current_hashrate} H/s | accepted: {total_accepted} | uptime: {int((time.time() - start_time) / 60)}m")
            last_report = time.time()

def main():
    global start_time
    start_time = time.time()
    cfg = load_config()

    wallet = cfg["wallet"]
    pool = cfg["pool"]
    worker = cfg["worker_name"]
    threads = cfg.get("threads", 2)

    if "FILL" in wallet:
        notify_task(cfg, "**error** | wallet not set in config.json — fill it and redeploy")
        print("wallet not set. edit config.json")
        return

    notify_task(cfg, f"**miner starting** | pool: {pool} | worker: {worker} | threads: {threads}")

    cmd = [
        "./xmrig",
        "-o", pool,
        "-u", wallet,
        "-p", worker,
        "-t", str(threads),
        "--no-color",
        "--print-time=30"
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    monitor_thread = threading.Thread(target=monitor_output, args=(proc, cfg), daemon=True)
    monitor_thread.start()

    notify_task(cfg, "**miner live** | xmrig process launched, monitoring output")

    proc.wait()
    notify_task(cfg, f"**miner stopped** | exit code: {proc.returncode} | uptime was {int((time.time() - start_time) / 60)}m")

if __name__ == "__main__":
    main()
