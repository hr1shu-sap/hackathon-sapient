# feedback_logger.py

import json
import time
from pathlib import Path
from typing import Dict, Optional

LOG_DIR = Path("rlhf_logs")
LOG_DIR.mkdir(exist_ok=True)

FEEDBACK_FILE = LOG_DIR / "feedback_events.jsonl"
TRUST_FILE = LOG_DIR / "user_trust.json"
STATS_FILE = LOG_DIR / "signal_stats.json"


class FeedbackLogger:
    """
    RLHF logger for Honest Stylist.

    Logs:
    - prompt
    - model response
    - explanation style
    - user feedback
    - computed reward

    Maintains:
    - per-user trust
    - per-signal reward stats
    - per-explanation confidence
    """

    # --------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------

    @staticmethod
    def make_json_safe(obj):
        """
        Recursively convert objects to JSON-serializable structures.
        """
        if obj is None:
            return None

        if isinstance(obj, (str, int, float, bool)):
            return obj

        if isinstance(obj, dict):
            return {str(k): FeedbackLogger.make_json_safe(v) for k, v in obj.items()}

        if isinstance(obj, list):
            return [FeedbackLogger.make_json_safe(v) for v in obj]

        # numpy / other bools
        if hasattr(obj, "item"):
            try:
                return obj.item()
            except Exception:
                pass

        # fallback: string representation
        return str(obj)


    def log_event(
        self,
        *,
        user_id: str,
        prompt: str,
        response: str,
        user_feedback: Dict,
        context: Dict
    ):
        """
        Log a single RLHF interaction and update learning stats.
        """

        reward = self._compute_reward(user_feedback)

        record = {
            "timestamp": time.time(),
            "user_id": user_id,
            "prompt": prompt,
            "response": response,
            "reward": reward,
            "user_feedback": user_feedback,
            "context": context
        }

        safe_record = FeedbackLogger.make_json_safe(record)

        with open(FEEDBACK_FILE, "a") as f:
            f.write(json.dumps(safe_record) + "\n")

        # Update learning stores
        self._update_user_trust(user_id, user_feedback)
        self._update_signal_stats(context, reward)

        return reward

    # --------------------------------------------------
    # REWARD COMPUTATION (CORE RLHF)
    # --------------------------------------------------

    def _compute_reward(self, user_feedback: Dict) -> float:
        """
        Convert user feedback into a scalar reward.
        Range approx: [-2.0, +3.0]
        """

        reward = 0.0

        # Verdict agreement
        if user_feedback.get("agree") is True:
            reward += 1.0
        elif user_feedback.get("agree") is False:
            reward -= 1.0

        # Explanation helpfulness (1–5 scale)
        helpfulness = user_feedback.get("explanation_helpful")
        if isinstance(helpfulness, int):
            reward += (helpfulness - 3) * 0.3

        # Recommendation click = strong signal
        if user_feedback.get("recommendation_clicked"):
            reward += 1.2

        # User override reason = gold signal
        if user_feedback.get("override_reason"):
            reward += 0.5

        return round(reward, 3)

    # --------------------------------------------------
    # USER TRUST TRACKING
    # --------------------------------------------------

    def _update_user_trust(self, user_id: str, user_feedback: Dict):
        trust = self._load_json(TRUST_FILE)

        if user_id not in trust:
            trust[user_id] = {
                "total": 0,
                "agree": 0,
                "disagree": 0,
                "override": 0
            }

        trust[user_id]["total"] += 1

        if user_feedback.get("agree") is True:
            trust[user_id]["agree"] += 1
        elif user_feedback.get("override_reason"):
            trust[user_id]["override"] += 1
        else:
            trust[user_id]["disagree"] += 1

        self._save_json(TRUST_FILE, trust)

    def get_user_trust_score(self, user_id: str) -> float:
        """
        Returns trust score between 0–1.
        """
        trust = self._load_json(TRUST_FILE)

        if user_id not in trust or trust[user_id]["total"] == 0:
            return 0.5  # neutral prior

        return round(trust[user_id]["agree"] / trust[user_id]["total"], 3)

    # --------------------------------------------------
    # SIGNAL & EXPLANATION LEARNING
    # --------------------------------------------------

    def _update_signal_stats(self, context: Dict, reward: float):
        """
        Aggregate reward per signal and explanation style.
        """

        stats = self._load_json(STATS_FILE)

        # --- Body balance signals ---
        signals = context.get("body_signals", {})
        for signal, active in signals.items():
            if not active:
                continue

            if signal not in stats:
                stats[signal] = {"count": 0, "total_reward": 0.0}

            stats[signal]["count"] += 1
            stats[signal]["total_reward"] += reward

        # --- Explanation style ---
        expl_style = context.get("explanation_style")
        if expl_style:
            key = f"explanation::{expl_style}"
            if key not in stats:
                stats[key] = {"count": 0, "total_reward": 0.0}

            stats[key]["count"] += 1
            stats[key]["total_reward"] += reward

        self._save_json(STATS_FILE, stats)

    # --------------------------------------------------
    # READ APIs (FOR AGENTS)
    # --------------------------------------------------

    def get_signal_weight(self, signal: str) -> float:
        """
        Convert historical reward into a multiplicative weight.
        """
        stats = self._load_json(STATS_FILE)
        data = stats.get(signal)

        if not data or data["count"] < 5:
            return 1.0  # insufficient data

        avg = data["total_reward"] / data["count"]

        if avg > 0.5:
            return 1.2
        if avg < -0.5:
            return 0.7
        return 1.0

    def get_explanation_confidence(self, style: str) -> float:
        """
        Returns confidence score 0–1 for an explanation style.
        """
        stats = self._load_json(STATS_FILE)
        key = f"explanation::{style}"

        if key not in stats or stats[key]["count"] == 0:
            return 0.5

        avg = stats[key]["total_reward"] / stats[key]["count"]
        return max(0.0, min(1.0, 0.5 + avg / 4))

    # --------------------------------------------------
    # INTERNAL HELPERS
    # --------------------------------------------------

    def _load_json(self, path: Path) -> Dict:
        if not path.exists():
            return {}
        with open(path, "r") as f:
            return json.load(f)

    def _save_json(self, path: Path, data: Dict):
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
