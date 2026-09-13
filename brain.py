#!/usr/bin/env python3
"""
MFR-Cognition — Cognitive Core
Version: 4.1
Role: Context, Memory, Verification, Decision Trace
"""

import os
import json
import platform
import socket
import hashlib
from datetime import datetime, timezone
from statistics import mean, stdev
from typing import Dict, List, Any, Tuple

STATE = "state.json"
REPORT = "report.txt"
DECISIONS = "decisions.json"
MAX_HISTORY = 150
MAX_DECISIONS = 40

def utc_now():
    return datetime.now(timezone.utc)

def load_state() -> Dict:
    try:
        with open(STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "identity": "MFR-Cognition v4.1 — Cognitive Core",
            "history": [],
            "anomalies": [],
            "alerts": [],
            "decisions": [],
            "evolution": 0,
            "status": "initializing"
        }

def save_state(data: Dict):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_system_snapshot() -> Dict:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        net = psutil.net_io_counters()
        load_avg = os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.0
        return {
            "cpu": round(cpu, 1),
            "memory": round(mem, 1),
            "disk": round(disk, 1),
            "net_sent_mb": round(net.bytes_sent / 1024 / 1024, 2),
            "net_recv_mb": round(net.bytes_recv / 1024 / 1024, 2),
            "load_avg": round(load_avg, 2)
        }
    except Exception:
        return {
            "cpu": 0.0, "memory": 0.0, "disk": 0.0,
            "net_sent_mb": 0.0, "net_recv_mb": 0.0, "load_avg": 0.0
        }

def generate_signature(data: Dict) -> str:
    raw = json.dumps(data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def reason(state: Dict, current: Dict) -> Tuple[List[str], List[Dict], Dict]:
    """
    Cognitive reasoning pipeline:
    INPUT → EVIDENCE → REASONING → CONFIDENCE → OUTPUT
    """
    history = state.get("history", [])
    anomalies = []
    alerts = []
    evidence = []
    confidence = 0.5

    # --- Evidence collection ---
    evidence.append({"type": "metric", "name": "cpu", "value": current["cpu"]})
    evidence.append({"type": "metric", "name": "memory", "value": current["memory"]})
    evidence.append({"type": "metric", "name": "disk", "value": current["disk"]})

    # Absolute checks
    if current["cpu"] > 85:
        anomalies.append("CRITICAL: CPU > 85%")
        alerts.append({"level": "critical", "metric": "cpu", "value": current["cpu"]})
        evidence.append({"type": "threshold", "rule": "cpu > 85", "triggered": True})
        confidence += 0.25
    elif current["cpu"] > 70:
        anomalies.append("WARNING: CPU elevated")
        evidence.append({"type": "threshold", "rule": "cpu > 70", "triggered": True})
        confidence += 0.1

    if current["memory"] > 90:
        anomalies.append("CRITICAL: Memory > 90%")
        alerts.append({"level": "critical", "metric": "memory", "value": current["memory"]})
        evidence.append({"type": "threshold", "rule": "memory > 90", "triggered": True})
        confidence += 0.25
    elif current["memory"] > 80:
        anomalies.append("WARNING: Memory elevated")
        evidence.append({"type": "threshold", "rule": "memory > 80", "triggered": True})
        confidence += 0.1

    if current["disk"] > 92:
        anomalies.append("CRITICAL: Disk nearly full")
        alerts.append({"level": "critical", "metric": "disk", "value": current["disk"]})
        evidence.append({"type": "threshold", "rule": "disk > 92", "triggered": True})
        confidence += 0.2

    # Historical evidence
    if len(history) >= 5:
        recent = history[-10:]
        cpu_vals = [h.get("cpu", 0) for h in recent]
        mem_vals = [h.get("memory", 0) for h in recent]
        try:
            cpu_avg = mean(cpu_vals)
            mem_avg = mean(mem_vals)
            cpu_std = stdev(cpu_vals) if len(cpu_vals) > 1 else 0

            if current["cpu"] > cpu_avg + (2 * cpu_std) and current["cpu"] > 50:
                anomalies.append(f"TREND: CPU spike vs baseline {cpu_avg:.1f}%")
                evidence.append({
                    "type": "statistical",
                    "metric": "cpu",
                    "baseline": round(cpu_avg, 1),
                    "current": current["cpu"],
                    "std": round(cpu_std, 1)
                })
                confidence += 0.15

            if current["memory"] > mem_avg + 15:
                anomalies.append(f"TREND: Memory rising above baseline {mem_avg:.1f}%")
                evidence.append({
                    "type": "statistical",
                    "metric": "memory",
                    "baseline": round(mem_avg, 1),
                    "current": current["memory"]
                })
                confidence += 0.1
        except Exception:
            pass

    if not anomalies:
        anomalies.append("STABLE: No significant issues detected")
        confidence = 0.85

    confidence = min(0.98, max(0.3, confidence))

    decision = {
        "timestamp": utc_now().isoformat(),
        "input": {
            "cpu": current["cpu"],
            "memory": current["memory"],
            "disk": current["disk"]
        },
        "evidence": evidence,
        "anomalies": anomalies,
        "confidence": round(confidence, 2),
        "status": "critical" if any("CRITICAL" in a for a in anomalies) else
                  "warning" if any("WARNING" in a or "TREND" in a for a in anomalies) else "stable"
    }

    return anomalies, alerts, decision

def main():
    now = utc_now()
    state = load_state()
    snapshot = get_system_snapshot()

    anomalies, alerts, decision = reason(state, snapshot)

    snapshot["timestamp"] = now.isoformat()
    snapshot["signature"] = generate_signature(snapshot)

    # Update history
    history = state.get("history", [])
    history.append(snapshot)
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    # Update decisions
    decisions = state.get("decisions", [])
    decisions.append(decision)
    if len(decisions) > MAX_DECISIONS:
        decisions = decisions[-MAX_DECISIONS:]

    state["history"] = history
    state["evolution"] = state.get("evolution", 0) + 1
    state["anomalies"] = anomalies
    state["alerts"] = (state.get("alerts", []) + alerts)[-20:]
    state["decisions"] = decisions
    state["last_run"] = now.isoformat()
    state["status"] = "active"
    state["hostname"] = socket.gethostname()
    state["os"] = platform.system()
    state["identity"] = "MFR-Cognition v4.1 — Cognitive Core"
    state["last_decision"] = decision

    save_state(state)

    # Persist last decisions for external consumers
    with open(DECISIONS, "w", encoding="utf-8") as f:
        json.dump(decisions[-10:], f, indent=2, ensure_ascii=False)

    # Report
    border = "═" * 56
    report = f"""
╔{border}╗
║        MFR-COGNITION v4.1 — COGNITIVE CORE             ║
╠{border}╣
║  Identity   : {state['identity']}
║  Host       : {state['hostname']}
║  OS         : {state['os']}
║  Evolution  : Generation #{state['evolution']}
║  Timestamp  : {now.strftime('%Y-%m-%d %H:%M:%S')} UTC
║  Signature  : {snapshot['signature']}
╠{border}╣
║  CPU        : {snapshot['cpu']}%
║  Memory     : {snapshot['memory']}%
║  Disk       : {snapshot['disk']}%
║  LoadAvg    : {snapshot['load_avg']}
╠{border}╣
║  Decision Status : {decision['status'].upper()}
║  Confidence      : {decision['confidence']}
╠{border}╣
║  Reasoning Output:
"""
    for a in anomalies:
        report += f"║    • {a}\n"

    report += f"""╠{border}╣
║  History    : {len(history)} snapshots
║  Decisions  : {len(decisions)} recorded
╚{border}╝
"""

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)

if __name__ == "__main__":
    main()
