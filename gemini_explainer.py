import os
import warnings
from typing import Dict

# Try new package first, fall back to deprecated package with a warning
try:
    import google.genai as genai  # preferred
except Exception:
    try:
        import google.generativeai as genai  # deprecated
        warnings.warn(
            "All support for 'google.generativeai' has ended. Please switch to 'google.genai'.",
            FutureWarning,
        )
    except Exception:
        genai = None

class GeminiExplainer:
    """Generate honest explanations using Gemini 1.5 Flash"""

    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set")

        if genai is None:
            raise ImportError(
                "No Google GenAI client found. Install 'google-genai' or the older 'google-generativeai' package."
            )

        # Configure client if available (older package uses configure)
        if hasattr(genai, "configure"):
            genai.configure(api_key=api_key)

        # Prefer GenerativeModel API if present, otherwise try to use client constructors
        if hasattr(genai, "GenerativeModel"):
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        elif hasattr(genai, "Client"):
            # google.genai has a Client-based API; attempt to create a client wrapper
            self.client = genai.Client(api_key=api_key)
            self.model = None
        else:
            raise RuntimeError("Installed Google GenAI package does not expose a supported model API")

    def explain_verdict(
        self,
        verdict: str,
        user_profile: Dict,
        garment: Dict,
        rule_reasons: list,
        score: int
    ) -> Dict:
        context = self._build_context(user_profile, garment, rule_reasons, score, verdict)
        prompt = self._create_prompt(context)
        # Use available model/client interface
        if hasattr(self, "model") and self.model is not None:
            response = self.model.generate_content(prompt)
            text = getattr(response, "text", str(response))
        else:
            # google.genai Client path (best-effort)
            resp = self.client.generate_text(model="gemini-1.5-flash", prompt=prompt)
            text = resp.text if hasattr(resp, "text") else str(resp)

        return self._parse_response(text)

    def _build_context(self, user_profile, garment, rule_reasons, score, verdict):
        reasons_text = "\n".join([f"- {r['text']} ({r['penalty']} pts)" for r in rule_reasons])
        
        # We now include the specific body ratios for the LLM to use as proof
        ratios = user_profile.get('body_ratios', {})
        s_h = ratios.get('s_h', 'N/A')
        w_h = ratios.get('w_h', 'N/A')

        context = f"""
USER STYLE DNA:
- Season: {user_profile.get('season')}
- Body Shape: {user_profile.get('body_shape')} (Shoulder-Hip: {s_h}, Waist-Hip: {w_h})
- Temperature: {user_profile.get('temperature')}
- Contrast: {user_profile.get('contrast')}

GARMENT:
- Name: {garment.get('name')}
- Silhouette: {garment.get('silhouette')}
- Shoulder Emphasis: {garment.get('shoulder_emphasis')}
- Neckline: {garment.get('neckline')}

RULE ENGINE VERDICT:
- Score: {score}/100
- Notes: {reasons_text}
"""
        return context.strip()

    def _create_prompt(self, context):
        return f"""
{context}

You are 'The Honest Stylist'. Use the data above to give a scientific, direct, and slightly witty verdict.

TASK:
1) EXPLANATION: Explain WHY this works or fails. Reference the specific body shape or ratios.
2) PIVOT: Name a specific garment type or color from the catalog that would solve the primary conflict.
3) PIVOT_WHY: Explain the geometric or color-science reason why the pivot is better.

RULES:
- Be brutally honest. If they look like a rectangle in a boxy tee, say so.
- Use the ratio data (e.g., "Your shoulder-to-hip ratio of {context.split('Shoulder-Hip: ')[1].split(',')[0]} confirms...")
- Keep it concise.

FORMAT:
EXPLANATION: ...
PIVOT: ...
PIVOT_WHY: ...
""".strip()

    def _parse_response(self, text: str) -> Dict:
        result = {"why_verdict": "", "pivot_suggestion": "", "pivot_reason": ""}
        for line in text.split("\n"):
            if line.startswith("EXPLANATION:"):
                result["why_verdict"] = line.replace("EXPLANATION:", "").strip()
            elif line.startswith("PIVOT:"):
                result["pivot_suggestion"] = line.replace("PIVOT: ", "").strip()
            elif line.startswith("PIVOT_WHY:"):
                result["pivot_reason"] = line.replace("PIVOT_WHY: ", "").strip()
        return result