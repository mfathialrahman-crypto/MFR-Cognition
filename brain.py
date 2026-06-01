import os, json, platform, socket, hashlib
from datetime import datetime, timezone

STATE = "state.json"
REPORT = "report.txt"

def load_state():
    try:
        with open(STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"history": [], "anomalies": [], "evolution": 0}

def save_state(data):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def analyze(state):
    evolution = state.get("evolution", 0) + 1
    history = state.get("history", [])
    anomalies = []

    # تحليل ذكي للتاريخ
    if len(history) >= 3:
        last = history[-1]
        if last.get("cpu", 0) > 80:
            anomalies.append("⚠️ CPU مرتفع جداً")
        if last.get("memory", 0) > 85:
            anomalies.append("⚠️ الذاكرة ممتلئة")
        if last.get("disk", 0) > 90:
            anomalies.append("🔴 الديسك على وشك الامتلاء")
        if not anomalies:
            anomalies.append("✅ النظام سليم تماماً")

    return evolution, anomalies

def get_system_snapshot():
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        net = psutil.net_io_counters()
        net_sent = round(net.bytes_sent / 1024 / 1024, 2)
        net_recv = round(net.bytes_recv / 1024 / 1024, 2)
    except:
        cpu = mem = disk = net_sent = net_recv = 0

    return {
        "cpu": cpu,
        "memory": mem,
        "disk": disk,
        "net_sent_mb": net_sent,
        "net_recv_mb": net_recv
    }

def generate_signature(data):
    raw = json.dumps(data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def main():
    now = datetime.now(timezone.utc)
    state = load_state()
    snapshot = get_system_snapshot()
    evolution, anomalies = analyze(state)

    snapshot["timestamp"] = now.isoformat()
    snapshot["signature"] = generate_signature(snapshot)

    history = state.get("history", [])
    history.append(snapshot)
    if len(history) > 100:
        history = history[-100:]

    state["history"] = history
    state["evolution"] = evolution
    state["anomalies"] = anomalies
    state["last_run"] = now.isoformat()
    state["status"] = "sovereign_active"
    state["hostname"] = socket.gethostname()
    state["os"] = platform.system()
    state["identity"] = "MFR-Cognition v3"

    save_state(state)

    # تقرير احترافي
    border = "═" * 50
    report = f"""
╔{border}╗
║         MFR-COGNITION — SOVEREIGN BRAIN v3        ║
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
║  شبكة↑    : {snapshot['net_sent_mb']} MB
║  شبكة↓    : {snapshot['net_recv_mb']} MB
╠{border}╣
║  التحليل  :
"""
    for a in anomalies:
        report += f"║    {a}\n"

    report += f"""╠{border}╣
║  السجل    : {len(history)} تشغيل محفوظ
╚{border}╝
"""

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)

if __name__ == "__main__":
    main()
