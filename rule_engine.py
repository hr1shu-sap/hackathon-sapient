# rule_engine.py

class StylingAnalyzer:
    """
    Rule-based styling engine using BODY BALANCE → SIGNALS.
    This engine produces structured, explainable reasons
    that can later be expanded by an LLM.
    """

    def __init__(self):
        self.score = 100
        self.reasons = []

    # --------------------------------------------------
    # INTERNAL HELPERS
    # --------------------------------------------------

    def reset(self):
        self.score = 100
        self.reasons = []

    def add_reason(self, penalty: int, code: str, text: str):
        self.score -= penalty
        self.reasons.append({
            "type": "penalty",
            "code": code,
            "text": text,
            "impact": penalty
        })

    def add_bonus(self, bonus: int, code: str, text: str):
        self.score += bonus
        self.reasons.append({
            "type": "bonus",
            "code": code,
            "text": text,
            "impact": -bonus
        })

    # --------------------------------------------------
    # MAIN ANALYSIS
    # --------------------------------------------------

    def analyze(self, user_profile: dict, garment: dict) -> dict:
        self.reset()

        # ----------------------------------------------
        # BODY BALANCE SIGNALS
        # ----------------------------------------------
        body = user_profile.get("body_balance", {})
        confidence = body.get("confidence", 0.0)

        shoulder_bias = body.get("shoulder_bias", 0.0)      # +ve = shoulder dominant
        hip_bias = body.get("hip_bias", 0.0)                # +ve = hip dominant
        waist_def = body.get("waist_definition", 0.0)       # higher = more defined

        shoulder_dominant = shoulder_bias > 0.10
        hip_dominant = hip_bias > 0.10
        defined_waist = waist_def > 0.15

        # ----------------------------------------------
        # GARMENT ATTRIBUTES
        # ----------------------------------------------
        silhouette = garment.get("silhouette")              # fitted, straight, oversized
        shoulder_emph = garment.get("shoulder_emphasis")    # low, medium, high
        neckline = garment.get("neckline")                  # v-neck, crew, boat, etc.
        visual_weight = garment.get("visual_weight")        # light, medium, heavy

        # ----------------------------------------------
        # BODY × GARMENT INTERACTION
        # ----------------------------------------------
        if confidence >= 0.6:

            # ---- Shoulder dominance ----
            if shoulder_dominant:
                if shoulder_emph == "high":
                    self.add_reason(
                        25,
                        "SHOULDER_OVERLOAD",
                        "Strong shoulder detailing adds visual bulk to an already upper-dominant frame."
                    )
                if neckline in ["v-neck", "deep_v"]:
                    self.add_bonus(
                        10,
                        "SHOULDER_SOFTENING",
                        "V-necklines visually narrow the shoulder line and restore balance."
                    )

            # ---- Hip dominance ----
            if hip_dominant:
                if silhouette == "fitted":
                    self.add_reason(
                        20,
                        "HIP_OVEREMPHASIS",
                        "A fitted silhouette can over-emphasize the lower half."
                    )
                if shoulder_emph == "high":
                    self.add_bonus(
                        15,
                        "UPPER_BALANCE",
                        "Added shoulder structure helps counterbalance hip dominance."
                    )

            # ---- Waist definition ----
            if defined_waist:
                if silhouette == "fitted":
                    self.add_bonus(
                        15,
                        "WAIST_HIGHLIGHT",
                        "This cut complements your natural waist definition."
                    )
                elif silhouette == "oversized":
                    self.add_reason(
                        10,
                        "WAIST_HIDDEN",
                        "Loose silhouettes hide one of your strongest proportion cues."
                    )

            # ---- Visual weight ----
            if visual_weight == "heavy" and not defined_waist:
                self.add_reason(
                    10,
                    "WEIGHT_OVERWHELM",
                    "Heavy fabrics without shaping can overwhelm your frame."
                )

        else:
            # Low confidence → conservative styling
            self.add_reason(
                5,
                "LOW_BODY_CONFIDENCE",
                "Body balance signals are weak; recommendations are intentionally conservative."
            )

        # ----------------------------------------------
        # COLOR HARMONY (HIGH CONFIDENCE RULE)
        # ----------------------------------------------
        user_season = user_profile.get("season")
        garment_seasons = garment.get("color_season", [])

        if user_season and user_season not in garment_seasons:
            self.add_reason(
                40,
                "COLOR_MISMATCH",
                f"This color falls outside your {user_season} palette."
            )

        # ----------------------------------------------
        # FINAL VERDICT
        # ----------------------------------------------
        return self._format_result()

    # --------------------------------------------------
    # OUTPUT FORMAT
    # --------------------------------------------------

    def _format_result(self) -> dict:
        if self.score >= 75:
            verdict = "Works very well"
            verdict_short = "✓ STRONG MATCH"
        elif self.score >= 55:
            verdict = "Mostly works"
            verdict_short = "✓ WORKS"
        elif self.score >= 40:
            verdict = "Risky choice"
            verdict_short = "⚠ RISKY"
        else:
            verdict = "Not recommended"
            verdict_short = "✗ DON'T BUY"

        return {
            "score": max(0, min(100, self.score)),
            "verdict": verdict,
            "verdict_short": verdict_short,
            "reasons": self.reasons
        }
