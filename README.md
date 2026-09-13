# MFR-Cognition v4.1 — Cognitive Core

**Role in the ecosystem:** Context • Memory • Verification • Decision Trace

## Purpose

MFR-Cognition is the cognitive runtime layer. It does not just detect thresholds — it produces structured, traceable decisions.

## Decision Pipeline

```
INPUT (metrics)
   ↓
EVIDENCE collection
   ↓
REASONING (thresholds + statistical)
   ↓
CONFIDENCE scoring
   ↓
STRUCTURED OUTPUT (decision object)
```

Every decision contains:
- input snapshot
- evidence list
- anomalies found
- confidence score
- final status

## Files

| File             | Purpose                              |
|------------------|--------------------------------------|
| `brain.py`       | Cognitive runtime                    |
| `state.json`     | Full persistent state + history      |
| `decisions.json` | Recent decision traces               |
| `report.txt`     | Human-readable report                |

## Run

```bash
pip install -r requirements.txt
python brain.py
```

## Automation

Runs every 2 hours via GitHub Actions.

---

**Ecosystem position:**  
Receives telemetry context → produces verified decisions with confidence.
