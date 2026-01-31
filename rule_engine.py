# 

class StylingAnalyzer:
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

    def analyze(self, user_profile: dict, garment: dict) -> dict:
        self.reset()
        shape = user_profile.get("body_shape")
        silhouette = garment.get("silhouette")
        shoulder_emph = garment.get("shoulder_emphasis")
        neckline = garment.get("neckline")

        # --- BODY SHAPE LOGIC ---
        if shape == "Hourglass":
            if silhouette == "fitted":
                self.add_bonus(20, "Fitted cut highlights your balanced proportions.")
            elif silhouette == "oversized":
                self.add_reason(15, "Oversized silhouettes may hide your natural waistline.")

        elif shape == "Apple":
            if neckline == "v-neck":
                self.add_bonus(15, "V-neckline elongates the torso and draws the eye upward.")
            if silhouette == "fitted":
                self.add_reason(25, "Tight fits can be less flattering on an oval frame.")

        elif shape == "Inverted Triangle":
            if shoulder_emph == "high":
                self.add_reason(30, "Strong shoulders exaggerate your upper frame.")
            if neckline == "v-neck":
                self.add_bonus(10, "V-neck helps visually narrow broad shoulders.")

        elif shape == "Pear":
            if shoulder_emph == "high":
                self.add_bonus(20, "Strong shoulders help balance wider hip proportions.")
            if silhouette == "fitted":
                self.add_reason(15, "Fitted bottoms can over-emphasize the lower half.")

        # --- COLOR LOGIC ---
        if user_profile.get("season") not in garment.get("color_season", []):
            self.add_reason(40, f"Color clashes with your {user_profile.get('season')} palette.")

        return self._format_result()

    def _format_result(self):
        # (Same formatting logic as before)
        return {"score": max(0, self.score), "reasons": self.reasons, "verdict": self._get_verdict()}