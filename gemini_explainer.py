# import os
# import google.generativeai as genai
# from typing import Dict

# class GeminiExplainer:
#     """Generate honest explanations using Gemini 1.5 Flash"""

#     def __init__(self, api_key: str = None):
#         if api_key is None:
#             api_key = os.getenv("GOOGLE_API_KEY")
#         if not api_key:
#             raise ValueError("GOOGLE_API_KEY not set")

#         genai.configure(api_key=api_key)
#         self.model = genai.GenerativeModel("gemini-1.5-flash")

#     def explain_verdict(
#         self,
#         verdict: str,
#         user_profile: Dict,
#         garment: Dict,
#         rule_reasons: list,
#         score: int
#     ) -> Dict:
#         context = self._build_context(user_profile, garment, rule_reasons, score, verdict)
#         prompt = self._create_prompt(context)
#         response = self.model.generate_content(prompt)
#         return self._parse_response(response.text)

#     def _build_context(self, user_profile, garment, rule_reasons, score, verdict):
#         reasons_text = "\n".join([f"- {r['text']} ({r['penalty']} pts)" for r in rule_reasons])
        
#         # We now include the specific body ratios for the LLM to use as proof
#         ratios = user_profile.get('body_ratios', {})
#         s_h = ratios.get('s_h', 'N/A')
#         w_h = ratios.get('w_h', 'N/A')

#         context = f"""
# USER STYLE DNA:
# - Season: {user_profile.get('season')}
# - Body Shape: {user_profile.get('body_shape')} (Shoulder-Hip: {s_h}, Waist-Hip: {w_h})
# - Temperature: {user_profile.get('temperature')}
# - Contrast: {user_profile.get('contrast')}

# GARMENT:
# - Name: {garment.get('name')}
# - Silhouette: {garment.get('silhouette')}
# - Shoulder Emphasis: {garment.get('shoulder_emphasis')}
# - Neckline: {garment.get('neckline')}

# RULE ENGINE VERDICT:
# - Score: {score}/100
# - Notes: {reasons_text}
# """
#         return context.strip()

#     def _create_prompt(self, context):
#         return f"""
# {context}

# You are 'The Honest Stylist'. Use the data above to give a scientific, direct, and slightly witty verdict.

# TASK:
# 1) EXPLANATION: Explain WHY this works or fails. Reference the specific body shape or ratios.
# 2) PIVOT: Name a specific garment type or color from the catalog that would solve the primary conflict.
# 3) PIVOT_WHY: Explain the geometric or color-science reason why the pivot is better.

# RULES:
# - Be brutally honest. If they look like a rectangle in a boxy tee, say so.
# - Use the ratio data (e.g., "Your shoulder-to-hip ratio of {context.split('Shoulder-Hip: ')[1].split(',')[0]} confirms...")
# - Keep it concise.

# FORMAT:
# EXPLANATION: ...
# PIVOT: ...
# PIVOT_WHY: ...
# """.strip()

#     def _parse_response(self, text: str) -> Dict:
#         result = {"why_verdict": "", "pivot_suggestion": "", "pivot_reason": ""}
#         for line in text.split("\n"):
#             if line.startswith("EXPLANATION:"):
#                 result["why_verdict"] = line.replace("EXPLANATION:", "").strip()
#             elif line.startswith("PIVOT:"):
#                 result["pivot_suggestion"] = line.replace("PIVOT: ", "").strip()
#             elif line.startswith("PIVOT_WHY:"):
#                 result["pivot_reason"] = line.replace("PIVOT_WHY: ", "").strip()
#         return result

# gemini_explainer.py

import json
import google.generativeai as genai

class GeminiExplainer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def explain(self, user_profile, garment, rule_result):
        prompt = f"""
You are a professional fashion stylist.

USER BODY BALANCE:
{json.dumps(user_profile["body_balance"], indent=2)}

USER COLOR PROFILE:
Season: {user_profile["season"]}
Contrast: {user_profile["contrast"]}

GARMENT:
{json.dumps(garment, indent=2)}

STYLE SIGNALS:
{json.dumps(rule_result["signals"], indent=2)}

TASK:
1. Explain clearly why this garment works or does not work.
2. Focus on proportions, visual balance, and color harmony.
3. If it works, explain why it flatters.
4. If it doesn’t, explain what visually feels off.
5. Be concise, confident, and human.

Tone: honest stylist, not polite assistant.
"""

        response = self.model.generate_content(prompt)
        return response.text.strip()
