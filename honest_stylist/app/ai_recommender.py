# ai_recommender.py

from typing import List, Dict, Optional
import random

from garment_catalog import get_full_catalog


class AIRecommender:
    """
    AI-powered garment recommendation engine.

    - Always returns top-K alternatives
    - Uses garment_catalog as source of truth
    - Uses Gemini for reasoning when available
    - Falls back PER ITEM (never globally)
    """

    def __init__(self, gemini_client=None):
        """
        gemini_client: GeminiExplainer instance or None
        """
        self.gemini = gemini_client

    # --------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------

    def recommend(
        self,
        user_profile: Dict,
        current_garment: Dict,
        rule_result: Dict,
        top_k: int = 3,
        catalog: Optional[List[Dict]] = None
    ) -> List[Dict]:

        # 1️⃣ Load catalog
        if catalog is None:
            catalog = get_full_catalog()

        if not catalog:
            return []

        # 2️⃣ Remove current garment
        candidates = [
            g for g in catalog
            if g.get("sku") != current_garment.get("sku")
        ]

        if not candidates:
            return []

        # 3️⃣ Rank candidates
        ranked = self._rank_candidates(
            user_profile=user_profile,
            current_garment=current_garment,
            rule_result=rule_result,
            candidates=candidates
        )

        # 4️⃣ Explain top-K
        results = []
        for g in ranked[:top_k]:
            reason = self._safe_reason(
                user_profile, current_garment, g, rule_result
            )

            results.append({
                "sku": g.get("sku"),
                "name": g.get("name"),
                "color": g.get("color_name"),
                "silhouette": g.get("silhouette"),
                "reason": reason
            })

        return results

    # --------------------------------------------------
    # RANKING (DETERMINISTIC + LEARNED SIGNALS)
    # --------------------------------------------------

    def _rank_candidates(
        self,
        user_profile: Dict,
        current_garment: Dict,
        rule_result: Dict,
        candidates: List[Dict]
    ) -> List[Dict]:

        season = user_profile.get("season")
        signals = user_profile.get("body_profile", {}).get("signals", {})

        scored = []

        for g in candidates:
            score = 0.0

            # ---- Color harmony (strong signal) ----
            if season in g.get("color_season", []):
                score += 5.0

            # ---- Body balance ----
            if signals.get("shoulder_dominant") and g.get("shoulder_emphasis") == "low":
                score += 1.5

            if signals.get("hip_dominant") and g.get("shoulder_emphasis") == "high":
                score += 1.5

            # ---- Avoid previous mistakes ----
            for r in rule_result.get("reasons", []):
                text = r.get("text", "").lower()

                if "shoulder" in text and g.get("shoulder_emphasis") == "low":
                    score += 1.0

                if "heavy" in text and g.get("visual_weight") == "light":
                    score += 1.0

                if "color" in text and season in g.get("color_season", []):
                    score += 1.0

            # ---- Diversity ----
            score += random.uniform(0, 0.4)

            scored.append((score, g))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [g for _, g in scored]

    # --------------------------------------------------
    # REASONING (SAFE, PER-ITEM)
    # --------------------------------------------------

    def _safe_reason(
        self,
        user_profile: Dict,
        current: Dict,
        candidate: Dict,
        rule_result: Dict
    ) -> str:
        """
        Try Gemini → fallback per item (never raise)
        """

        if self.gemini:
            try:
                return self._genai_reason(
                    user_profile, current, candidate, rule_result
                )
            except Exception as e:
                # 👇 Loggable if you want RLHF later
                print("⚠️ Gemini failed for recommendation:", e)

        return self._fallback_reason(user_profile, current, candidate)

    # --------------------------------------------------
    # GENAI REASONING
    # --------------------------------------------------

    def _genai_reason(
        self,
        user: Dict,
        current: Dict,
        candidate: Dict,
        rule_result: Dict
    ) -> str:

        penalties = [
            r.get("text", "")
            for r in rule_result.get("reasons", [])
            if r.get("penalty", 0) > 0
        ]

        prompt = f"""
You are a sharp, opinionated fashion stylist.

USER:
- Season: {user.get("season")}
- Body balance signals: {user.get("body_profile", {}).get("signals")}

ORIGINAL GARMENT:
- {current.get("name")}
- Color: {current.get("color_name")}
- Silhouette: {current.get("silhouette")}

ISSUES IDENTIFIED:
{penalties if penalties else "No major issues, but not optimal."}

BETTER OPTION:
- {candidate.get("name")}
- Color: {candidate.get("color_name")}
- Silhouette: {candidate.get("silhouette")}
- Shoulder emphasis: {candidate.get("shoulder_emphasis")}
- Visual weight: {candidate.get("visual_weight")}

TASK:
Explain in ONE specific sentence why this option works better.
No generic phrases. Mention balance or color explicitly.
"""

        response = self.gemini.client.models.generate_content(
            model=self.gemini.model_name,
            contents=prompt
        )

        text = response.text.strip()
        if not text:
            raise ValueError("Empty Gemini response")

        return text

    # --------------------------------------------------
    # FALLBACK (SMART, NON-GENERIC)
    # --------------------------------------------------

    def _fallback_reason(
        self,
        user: Dict,
        current: Dict,
        candidate: Dict
    ) -> str:

        season = user.get("season")
        signals = user.get("body_profile", {}).get("signals", {})
        reasons = []

        if season in candidate.get("color_season", []):
            reasons.append(
                f"the {candidate.get('color_name')} aligns better with your {season} palette"
            )

        if signals.get("shoulder_dominant") and candidate.get("shoulder_emphasis") == "low":
            reasons.append(
                "it softens the upper frame instead of adding bulk"
            )

        if signals.get("hip_dominant") and candidate.get("shoulder_emphasis") == "high":
            reasons.append(
                "the added shoulder structure restores visual balance"
            )

        if candidate.get("visual_weight") == "light":
            reasons.append(
                "the lighter fabric avoids a heavy, top-loaded look"
            )

        if not reasons:
            return (
                "this piece avoids the balance and proportion issues of the original choice"
            )

        return "This works better because " + ", ".join(reasons[:2]) + "."