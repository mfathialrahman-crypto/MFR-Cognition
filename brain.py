import os
import json
import platform
import socket
import hashlib
from datetime import datetime, timezone
from statistics import mean, stdev

STATE = "state.json"
REPORT = "report.txt"

def load_state():
    try:
        with open(STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "history": [],
            "anomalies": [],
            "evolution": 0,
            "alerts": []
        }

def save_state(data):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_system_snapshot():
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        net = psutil.net_io_counters()
        net_sent = round(net.bytes_sent / 1024 / 1024, 2)
        net_recv = round(net.bytes_recv / 1024 / 1024, 2)
        load_avg = os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.0
    except Exception:
        cpu = mem = disk = net_sent = net_recv = load_avg = 0.0

    return {
        "cpu": round(cpu, 1),
        "memory": round(mem, 1),
        "disk": round(disk, 1),
        "net_sent_mb": net_sent,
        "net_recv_mb": net_recv,
        "load_avg": round(load_avg, 2)
    }

def generate_signature(data):
    raw = json.dumps(data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def analyze(state, current):
    evolution = state.get("evolution", 0) + 1
    history = state.get("history", [])
    anomalies = []
    alerts = []

    # Immediate thresholds
    if current["cpu"] > 85:
        anomalies.append("🔴 CPU حرج (>85%)")
        alerts.append({"level": "critical", "msg": "CPU high", "value": current["cpu"]})
    elif current["cpu"] > 70:
        anomalies.append("⚠️ CPU مرتفع")

    if current["memory"] > 90:
        anomalies.append("🔴 الذاكرة حرجة (>90%)")
        alerts.append({"level": "critical", "msg": "Memory critical", "value": current["memory"]})
    elif current["memory"] > 80:
        anomalies.append("⚠️ الذاكرة مرتفعة")

    if current["disk"] > 92:
        anomalies.append("🔴 الديسك شبه ممتلئ")
        alerts.append({"level": "critical", "msg": "Disk almost full", "value": current["disk"]})
    elif current["disk"] > 85:
        anomalies.append("⚠️ الديسك مرتفع")

    # Trend analysis (last 10 runs)
    if len(history) >= 5:
        recent = history[-10:]
        cpu_vals = [h.get("cpu", 0) for h in recent]
        mem_vals = [h.get("memory", 0) for h in recent]

        try:
            cpu_avg = mean(cpu_vals)
            mem_avg = mean(mem_vals)
            cpu_std = stdev(cpu_vals) if len(cpu_vals) > 1 else 0

            if current["cpu"] > cpu_avg + (2 * cpu_std) and current["cpu"] > 50:
                anomalies.append(f"📈 ارتفاع مفاجئ في CPU (متوسط سابق {cpu_avg:.1f}%)")

            if current["memory"] > mem_avg + 15:
                anomalies.append(f"📈 ارتفاع ملحوظ في الذاكرة (متوسط سابق {mem_avg:.1f}%)")
        except Exception:
            pass

    if not anomalies:
        anomalies.append("✅ النظام مستقر وسليم")

    return evolution, anomalies, alerts

def main():
    now = datetime.now(timezone.utc)
    state = load_state()
    snapshot = get_system_snapshot()
    evolution, anomalies, alerts = analyze(state, snapshot)

    snapshot["timestamp"] = now.isoformat()
    snapshot["signature"] = generate_signature(snapshot)

    history = state.get("history", [])
    history.append(snapshot)
    if len(history) > 150:
        history = history[-150:]

    state["history"] = history
    state["evolution"] = evolution
    state["anomalies"] = anomalies
    state["alerts"] = alerts[-20:]  # keep last 20 alerts
    state["last_run"] = now.isoformat()
    state["status"] = "sovereign_active"
    state["hostname"] = socket.gethostname()
    state["os"] = platform.system()
    state["identity"] = "MFR-Cognition v4 — Sovereign Sentinel"

    save_state(state)

    # Professional report
    border = "═" * 54
    report = f"""
╔{border}╗
║     MFR-COGNITION v4 — SOVEREIGN SENTINEL          ║
╠{border}╣
║  الهوية   : {state['identity']}
║  الجهاز   : {state['hostname']}
║  النظام   : {state['os']}
║  التطور   : الجيل #{evolution}
║  التوقيت  : {now.strftime('%Y-%m-%d %H:%M:%S')} UTC
║  التوقيع  : {snapshot['signature']}
╠{border}╣
║  CPU      : {snapshot['cpu']}%
║  الذاكرة  : {snapshot['memory']}%
║  الديسك   : {snapshot['disk']}%
║  LoadAvg  : {snapshot['load_avg']}
║  شبكة↑    : {snapshot['net_sent_mb']} MB
║  شبكة↓    : {snapshot['net_recv_mb']} MB
╠{border}╣
║  التحليل  :
"""
    for a in anomalies:
        report += f"║    {a}\n"

    report += f"""╠{border}╣
║  السجل    : {len(history)} تشغيل محفوظ
║  الحالة   : {state['status']}
╚{border}╝
"""

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)

if __name__ == "__main__":
    main()
