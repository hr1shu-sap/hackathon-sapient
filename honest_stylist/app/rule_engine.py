# Rule engine for styling verdicts
# Scores are cumulative (start at 100, apply penalties)
# >= 60 → "Works"
# 40-59 → "Risky"
# < 40 → "Don't buy"

class StylingAnalyzer:
    """Rule-based styling verdict engine"""
    
    def __init__(self):
        self.score = 100
        self.reasons = []
        
    def reset(self):
        """Reset for new analysis"""
        self.score = 100
        self.reasons = []
        
    def add_reason(self, penalty: int, text: str):
        """Add a penalty and reason"""
        self.score -= penalty
        self.reasons.append({
            "text": text,
            "penalty": penalty
        })
        
    def analyze(self, user_profile: dict, garment: dict) -> dict:
        """
        Run full analysis.
        
        user_profile must contain:
        - skin_season: str (e.g., "Cool Winter", "Soft Autumn")
        - body_shape: str (e.g., "Inverted Triangle", "Pear", "Rectangle")
        - skin_undertone: str (e.g., "warm", "cool", "neutral")
        - contrast_level: str (e.g., "low", "medium", "high")
        
        garment must contain:
        - color_season: list of str
        - silhouette: str
        - shoulder_emphasis: str
        - visual_weight: str
        - brightness: str
        """
        self.reset()
        
        # Rule 1: Color season match
        if user_profile.get("skin_season") not in garment.get("color_season", []):
            self.add_reason(
                40,
                f"This color drains your complexion — it competes with your natural glow instead of enhancing it."
            )
        
        # Rule 2: Body shape + shoulder emphasis conflict
        body_shape = user_profile.get("body_shape")
        shoulder_emph = garment.get("shoulder_emphasis")
        
        if body_shape == "Inverted Triangle" and shoulder_emph == "high":
            self.add_reason(
                30,
                f"This emphasizes your shoulders — you already have width up top, so this will make your upper body look even heavier."
            )
        
        if body_shape == "Pear" and shoulder_emph == "low":
            self.add_reason(
                25,
                f"This lacks shoulder structure — your hips are wider, so you need visual interest up top to balance your frame."
            )
        
        # Rule 3: Visual weight consideration
        # Heavy pieces can make some shapes look heavier
        if garment.get("visual_weight") == "heavy":
            if user_profile.get("body_shape") == "Rectangle":
                self.add_reason(
                    15,
                    f"Heavy fabric will add bulk to your frame — you need lighter, more tailored pieces to define your silhouette."
                )
        
        # Rule 4: Undertone + brightness combo
        undertone = user_profile.get("skin_undertone")
        brightness = garment.get("brightness")
        
        if undertone == "cool" and brightness == "very_high":
            self.add_reason(
                10,
                f"This bright color is too jarring — it creates harsh contrast against your cool skin tone and washes out your features."
            )
        
        if undertone == "warm" and brightness == "very_high":
            self.add_reason(
                5,
                f"This bright color might overwhelm your warmth — it's almost too vibrant and could look costume-y."
            )
        
        # Rule 5: Contrast level + neckline
        # High contrast faces look better in defined necklines
        if user_profile.get("contrast_level") == "low" and garment.get("neckline") == "turtleneck":
            self.add_reason(
                10,
                f"This neckline is too heavy — your softer contrast works better with open, airy necklines that don't overpower your face."
            )
        
        # Rule 6: Silhouette bonus for pear shapes with fitted tops
        if body_shape == "Pear" and garment.get("silhouette") == "fitted":
            self.score += 10
            self.reasons.append({
                "text": "A fitted silhouette creates structure at the shoulders — this balances your hip width and creates a flattering line.",
                "penalty": -10  # Negative = bonus
            })
        
        return self._format_result()
    
    def generate_pivot_suggestion(self, user_profile: dict, garment: dict) -> str:
        """Generate a specific pivot suggestion based on what failed."""
        body_shape = user_profile.get("body_shape")
        shoulder_emph = garment.get("shoulder_emphasis")
        silhouette = garment.get("silhouette")
        
        # If color season failed, suggest color alternatives
        if user_profile.get("skin_season") not in garment.get("color_season", []):
            season = user_profile.get("skin_season", "your undertone")
            return f"Try this piece in jewel tones, deep neutrals, or true black that match {season}—they'll enhance your complexion instead of competing with it."
        
        # If shoulders are too emphasized on inverted triangle, suggest low shoulders
        if body_shape == "Inverted Triangle" and shoulder_emph == "high":
            return "Try the same piece with dropped or soft shoulders—it'll balance your frame without adding width."
        
        # If pear shape lacks shoulder interest, suggest higher shoulder emphasis
        if body_shape == "Pear" and shoulder_emph == "low":
            return "Try this with structured shoulders, off-shoulder, or a bold neckline—anything that draws attention upward."
        
        # If heavy visual weight on rectangle, suggest lighter fabrics
        if garment.get("visual_weight") == "heavy" and body_shape == "Rectangle":
            return "Try a lighter fabric or a more fitted cut—it'll give you definition without bulk."
        
        # If brightness is too extreme, suggest toned-down version
        if garment.get("brightness") == "very_high":
            return "Try the same color in a more muted or softened version—it'll harmonize better with your skin."
        
        # Default fallback
        return "Try this piece in a different silhouette or color that aligns with your profile."
    
    def _format_result(self) -> dict:
        """Format final result"""
        if self.score >= 60:
            verdict = "This actually suits you"
            verdict_short = "✓ WORKS"
        elif self.score >= 40:
            verdict = "This almost works — but it fails"
            verdict_short = "⚠ RISKY"
        else:
            verdict = "Don't buy this"
            verdict_short = "✗ DON'T BUY"
        
        return {
            "score": max(0, self.score),
            "verdict": verdict,
            "verdict_short": verdict_short,
            "reasons": self.reasons
        }
