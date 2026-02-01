# gemini_explainer.py

import json
from typing import Dict, Tuple
from google import genai


class GeminiExplainer:
    """
    Gemini-powered explanation engine for Honest Stylist.

    Returns:
    - prompt (for RLHF logging)
    - explanation (for UI)
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = "AIzaSyDF8LRHh-e4i34x2VNm1Kz0RtjCX-z56Lo"
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required")

        self.client = genai.Client(api_key=api_key)
        self.model = model

    # --------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------

    def explain(
        self,
        user_profile: Dict,
        garment: Dict,
        rule_result: Dict
    ) -> Tuple[str, str]:
        """
        Returns:
        (prompt, explanation_text)
        """

        prompt = self._build_prompt(
            user_profile=user_profile,
            garment=garment,
            rule_result=rule_result
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )

            explanation = response.text.strip()

            if not explanation:
                explanation = "This piece technically works, but doesn’t add much visual advantage."

            return prompt, explanation

        except Exception as e:
            # Fail gracefully — never break the UI
            fallback = (
                "This garment isn’t a strong visual match because it doesn’t align cleanly "
                "with your proportions or color balance."
            )
            return prompt, fallback

    # --------------------------------------------------
    # PROMPT CONSTRUCTION
    # --------------------------------------------------

    def _build_prompt(
        self,
        user_profile: Dict,
        garment: Dict,
        rule_result: Dict
    ) -> str:
        """
        Build a stable, JSON-safe prompt for Gemini.
        """

        body_balance = self._safe_json(user_profile.get("body_balance", {}))
        color_profile = {
            "season": user_profile.get("season"),
            "contrast": user_profile.get("contrast"),
        }

        reasons = [
            r.get("text")
            for r in rule_result.get("reasons", [])
        ]

        verdict = rule_result.get("verdict")

        prompt = f"""
You are a brutally honest professional fashion stylist.
You do NOT sugarcoat feedback.

USER BODY BALANCE:
{json.dumps(body_balance, indent=2)}

USER COLOR PROFILE:
{json.dumps(color_profile, indent=2)}

GARMENT BEING EVALUATED:
{json.dumps(self._safe_json(garment), indent=2)}

STYLE ENGINE VERDICT:
{verdict}

STYLE SIGNALS FIRED:
{json.dumps(reasons, indent=2)}

TASK:
1. Explain clearly WHY this garment works or does not work.
2. Focus on proportions, visual balance, and color harmony.
3. If it works, explain what it enhances.
4. If it doesn't, explain what visually feels off.
5. Be concise (2–4 sentences).
6. No generic compliments. No hedging language.

Tone:
Direct. Human. Stylist in a fitting room.
"""

        return prompt.strip()

    # --------------------------------------------------
    # SAFETY
    # --------------------------------------------------

    def _safe_json(self, obj):
        """
        Converts non-serializable objects safely.
        """
        try:
            json.dumps(obj)
            return obj
        except Exception:
            return self._stringify(obj)

    def _stringify(self, obj):
        if isinstance(obj, dict):
            return {k: self._stringify(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._stringify(v) for v in obj]
        return str(obj)
