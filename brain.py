import os
import json
from datetime import datetime

STATE = "state.json"
REPORT = "report.txt"

def load_state():
    if os.path.exists(STATE):
        try:
            with open(STATE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(data):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def main():
    state = load_state()

    state["last_run"] = datetime.utcnow().isoformat()
    state["status"] = "running"

    save_state(state)

    report = f"System executed successfully at {state['last_run']}"

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)

if __name__ == "__main__":
    main()