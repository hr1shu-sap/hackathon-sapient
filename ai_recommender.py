from typing import List, Dict
import random

class AIRecommender:
    """
    AI-powered recommendation layer.
    Uses GenAI reasoning + rule constraints to suggest better alternatives.
    """

    def __init__(self, gemini_client=None):
        """
        gemini_client: optional GeminiExplainer or GenAI client
        If None, falls back to heuristic ranking.
        """
        self.gemini = gemini_client

    # --------------------------------------------------

    def recommend(
        self,
        user_profile: Dict,
        current_garment: Dict,
        catalog: List[Dict],
        rule_result: Dict,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Return top-k alternative garments with reasons.
        """

        # Only recommend if current item is risky or bad
        if rule_result["score"] >= 60:
            return []

        # Step 1: Filter catalog by hard constraints
        candidates = self._filter_catalog(
            user_profile, current_garment, catalog
        )

        if not candidates:
            return []

        # Step 2: Rank candidates
        ranked = self._rank_candidates(
            user_profile, rule_result, candidates
        )

        # Step 3: Explain recommendations
        return self._explain_recommendations(
            user_profile,
            current_garment,
            ranked[:top_k]
        )

    # --------------------------------------------------
    # FILTERING (Deterministic, Fast)
    # --------------------------------------------------

    def _filter_catalog(self, user_profile, current, catalog):
        season = user_profile.get("season")
        vibe = current.get("vibe")          # optional: interview, date, casual
        category = current.get("category")  # dress, kurta, blazer

        filtered = []

        for g in catalog:
            if g["sku"] == current["sku"]:
                continue

            if season not in g.get("color_season", []):
                continue

            if category and g.get("category") != category:
                continue

            if vibe and g.get("vibe") != vibe:
                continue

            filtered.append(g)

        return filtered

    # --------------------------------------------------
    # RANKING (Rule-aware scoring)
    # --------------------------------------------------

    def _rank_candidates(self, user_profile, rule_result, candidates):
        body = user_profile.get("body_profile", {})
        signals = body.get("signals", {})

        scored = []

        for g in candidates:
            score = 0

            # Prefer waist definition if user has it
            if signals.get("defined_waist") and g.get("waist_definition") == "high":
                score += 2

            # Avoid repeating known mistakes
            for r in rule_result["reasons"]:
                if "shoulder" in r["text"].lower() and g.get("shoulder_emphasis") == "low":
                    score += 2
                if "waist" in r["text"].lower() and g.get("waist_definition") == "high":
                    score += 2

            # Light randomness for variety
            score += random.uniform(0, 0.5)

            scored.append((score, g))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [g for _, g in scored]

    # --------------------------------------------------
    # EXPLANATION (GenAI-powered, optional)
    # --------------------------------------------------

    def _explain_recommendations(
        self,
        user_profile,
        current_garment,
        recommendations
    ):
        results = []

        for g in recommendations:
            if self.gemini:
                reason = self._genai_reason(
                    user_profile, current_garment, g
                )
            else:
                reason = self._fallback_reason(current_garment, g)

            results.append({
                "sku": g["sku"],
                "name": g["name"],
                "reason": reason
            })

        return results

    def _genai_reason(self, user, current, candidate):
        prompt = f"""
You are an expert fashion stylist.

USER PROFILE:
- Season: {user.get("season")}
- Body signals: {user.get("body_profile", {}).get("signals")}

CURRENT GARMENT:
- Name: {current.get("name")}
- Issues: It was rated as risky or not recommended.

CANDIDATE GARMENT:
- Name: {candidate.get("name")}
- Silhouette: {candidate.get("silhouette")}
- Waist definition: {candidate.get("waist_definition")}
- Color: {candidate.get("color_name")}

TASK:
In ONE sentence, explain why the candidate garment is a better choice
than the current one. Be direct and specific.
"""
        response = self.gemini.model.generate_content(prompt)
        return response.text.strip()

    def _fallback_reason(self, current, candidate):
        return (
            f"This keeps a similar vibe but improves balance through "
            f"{candidate.get('silhouette')} and a more flattering color."
        )
