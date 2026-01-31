class StylingAnalyzer:
    """
    Rule-based styling verdict engine.
    Uses body balance signals instead of rigid body shapes.
    """

    def __init__(self):
        self.score = 100
        self.reasons = []

    def reset(self):
        self.score = 100
        self.reasons = []

    def add_reason(self, penalty, text):
        self.score -= penalty
        self.reasons.append({"text": text, "penalty": penalty})

    def add_bonus(self, bonus, text):
        self.score += bonus
        self.reasons.append({"text": text, "penalty": -bonus})

    # --------------------------------------------------
    # MAIN ANALYSIS
    # --------------------------------------------------

    def analyze(self, user_profile: dict, garment: dict) -> dict:
        self.reset()

        # ---- User signals ----
        body = user_profile.get("body_profile", {})
        signals = body.get("signals", {})
        body_conf = body.get("confidence", 0.0)

        shoulder_dom = signals.get("shoulder_dominant", False)
        hip_dom = signals.get("hip_dominant", False)
        defined_waist = signals.get("defined_waist", False)

        # ---- Garment attributes ----
        silhouette = garment.get("silhouette")              # fitted, a-line, oversized
        shoulder_emph = garment.get("shoulder_emphasis")    # low, medium, high
        neckline = garment.get("neckline")                  # v-neck, crew, off-shoulder
        waist_def = garment.get("waist_definition")         # low, medium, high
        visual_weight = garment.get("visual_weight")        # light, medium, heavy

        # --------------------------------------------------
        # BODY × GARMENT INTERACTION (confidence-gated)
        # --------------------------------------------------

        if body_conf >= 0.6:

            # ---- Shoulder dominance handling ----
            if shoulder_dom:
                if shoulder_emph == "high":
                    self.add_reason(
                        20,
                        "Strong shoulder details add bulk to an already upper-heavy silhouette."
                    )
                if neckline == "v-neck":
                    self.add_bonus(
                        10,
                        "V-neckline helps visually narrow the shoulder line."
                    )

            # ---- Hip dominance handling ----
            if hip_dom:
                if silhouette == "fitted":
                    self.add_reason(
                        15,
                        "Fitted cuts can over-emphasize the lower half."
                    )
                if shoulder_emph == "high":
                    self.add_bonus(
                        15,
                        "Shoulder structure helps rebalance the silhouette."
                    )

            # ---- Waist definition logic ----
            if defined_waist:
                if waist_def == "high":
                    self.add_bonus(
                        15,
                        "Defined waist works well with your natural proportions."
                    )
                elif waist_def == "low":
                    self.add_reason(
                        10,
                        "Lack of waist definition hides one of your strongest balance points."
                    )

            # ---- Visual weight ----
            if visual_weight == "heavy" and not defined_waist:
                self.add_reason(
                    10,
                    "Heavy fabrics without shaping can overwhelm your frame."
                )

        else:
            # Low confidence → soften body-based penalties
            self.add_reason(
                5,
                "Body analysis confidence is limited; recommendations are conservative."
            )

        # --------------------------------------------------
        # COLOR HARMONY (high confidence rule)
        # --------------------------------------------------

        user_season = user_profile.get("season")
        if user_season not in garment.get("color_season", []):
            self.add_reason(
                40,
                f"This color falls outside your {user_season} palette."
            )

        # --------------------------------------------------
        # FINAL VERDICT
        # --------------------------------------------------

        return self._format_result()

    # --------------------------------------------------

    def _format_result(self):
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
