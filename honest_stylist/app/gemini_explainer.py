import json
from typing import Dict, Tuple, Optional
import google.generativeai as genai

class GeminiExplainer:
    """
    Gemini-powered explanation engine for Honest Stylist.

    Supports:
    - explain_verdict: returns dict with 'why_verdict', 'pivot_suggestion', 'pivot_reason'
    - explain: returns (prompt, explanation_text) tuple for RLHF logging/UI
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    # --------------------------------------------------
    # PUBLIC API: RLHF-style (prompt, explanation)
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
            explanation = getattr(response, "text", "").strip()
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
    # PUBLIC API: Honest Stylist (dict output)
    # --------------------------------------------------
    def explain_verdict(
        self,
        verdict: str,
        user_profile: Dict,
        garment: Dict,
        rule_reasons: Optional[list] = None,
        score: Optional[int] = None
    ) -> Dict:
        """
        Returns:
            {
                "why_verdict": ...,
                "pivot_suggestion": ...,
                "pivot_reason": ...
            }
        """
        # Build prompt for main verdict explanation
        prompt = self._build_prompt(
            user_profile=user_profile,
            garment=garment,
            rule_result={
                "verdict": verdict,
                "reasons": rule_reasons or [],
                "score": score
            }
        )
        why_verdict = None
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            why_verdict = getattr(response, "text", "").strip()
        except Exception:
            why_verdict = (
                "This garment isn’t a strong visual match because it doesn’t align cleanly "
                "with your proportions or color balance."
            )

        # Build prompt for pivot suggestion
        pivot_prompt = self._build_pivot_prompt(
            user_profile=user_profile,
            garment=garment,
            verdict=verdict,
            rule_reasons=rule_reasons or [],
            score=score
        )
        pivot_suggestion = None
        pivot_reason = None
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=pivot_prompt
            )
            # Try to parse as JSON, else fallback to text
            try:
                pivot_json = json.loads(getattr(response, "text", ""))
                pivot_suggestion = pivot_json.get("pivot_suggestion")
                pivot_reason = pivot_json.get("pivot_reason")
            except Exception:
                pivot_suggestion = getattr(response, "text", "").strip()
                pivot_reason = ""
        except Exception:
            pivot_suggestion = "Try a different color or silhouette."
            pivot_reason = "No further details available."

        return {
            "why_verdict": why_verdict,
            "pivot_suggestion": pivot_suggestion,
            "pivot_reason": pivot_reason
        }

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

    def _build_pivot_prompt(
        self,
        user_profile: Dict,
        garment: Dict,
        verdict: str,
        rule_reasons: list,
        score: Optional[int]
    ) -> str:
        """
        Build a prompt for Gemini to suggest a pivot (alternative).
        """
        color_profile = {
            "season": user_profile.get("season"),
            "contrast": user_profile.get("contrast"),
        }
        reasons = [
            r.get("text")
            for r in rule_reasons
        ]
        prompt = f"""
You are a brutally honest professional fashion stylist.

USER COLOR PROFILE:
{json.dumps(color_profile, indent=2)}

GARMENT BEING EVALUATED:
{json.dumps(self._safe_json(garment), indent=2)}

STYLE ENGINE VERDICT:
{verdict}

STYLE SIGNALS FIRED:
{json.dumps(reasons, indent=2)}

TASK:
Suggest a single, actionable alternative (pivot) that would work better for this user.
Respond in JSON with keys: "pivot_suggestion", "pivot_reason".
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