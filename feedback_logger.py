# # feedback_logger.py
# import json
# import datetime
# import os

# FEEDBACK_LOG_PATH = "feedback_log.jsonl"


# def log_feedback(event: dict):
#     """
#     Append a feedback event to a JSONL file.
#     This is the foundation for RLHF.
#     """

#     event["timestamp"] = datetime.datetime.utcnow().isoformat()

#     with open(FEEDBACK_LOG_PATH, "a") as f:
#         f.write(json.dumps(event) + "\n")


# def feedback_to_reward(feedback: str) -> float:
#     """
#     Deterministic reward mapping.
#     Can be replaced by a learned reward model later.
#     """
#     if feedback == "agree":
#         return +1.0
#     if feedback == "bought_anyway":
#         return +0.5
#     if feedback == "disagree":
#         return -1.0
#     return 0.0


# feedback_logger.py
import json
import time
import uuid
from pathlib import Path

FEEDBACK_DIR = Path("feedback_logs")
FEEDBACK_DIR.mkdir(exist_ok=True)

REWARD_MAP = {
    "agree": 1.0,
    "bought_anyway": 0.5,
    "disagree": -1.0
}

def log_feedback(agent_state: dict, feedback: str, user_reason: str = ""):
    payload = {
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "feedback": feedback,
        "reward": REWARD_MAP.get(feedback, 0),
        "user_reason": user_reason,
        "rule_result": agent_state["rule_result"],
        "body_balance": agent_state["user_profile"]["body_balance"],
        "garment": agent_state["garment"]
    }

    path = FEEDBACK_DIR / f"{payload['id']}.json"
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
