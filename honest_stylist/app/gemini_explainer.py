# LLM-based explanation module
# Uses Gemini to generate brutally honest explanations
# NEVER decides verdict; only explains + suggests pivot

import os
import google.generativeai as genai
from typing import Dict

class GeminiExplainer:
    """Generate honest explanations using Gemini 1.5 Flash"""
    
    def __init__(self, api_key: str = None):
        """Initialize with API key (from .env or parameter)"""
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    def explain_verdict(
        self,
        verdict: str,
        user_profile: Dict,
        garment: Dict,
        rule_reasons: list,
        score: int
    ) -> Dict:
        """
        Generate explanation for verdict.
        
        Args:
        - verdict: "Works", "Risky", or "Don't buy"
        - user_profile: {skin_season, body_shape, skin_undertone, contrast_level}
        - garment: {name, color_name, color_season, silhouette, ...}
        - rule_reasons: list of {text, penalty}
        - score: 0-100
        
        Returns:
        {
            "why_verdict": "2-3 sentence explanation of the verdict",
            "pivot_suggestion": "Specific alternative garment description",
            "pivot_reason": "Why the pivot is better"
        }
        """
        
        # Build context for Gemini
        context = self._build_context(
            user_profile,
            garment,
            rule_reasons,
            score,
            verdict
        )
        
        # Create prompt
        prompt = self._create_prompt(context, verdict)
        
        # Call Gemini
        response = self.model.generate_content(prompt)
        
        # Parse response
        result = self._parse_response(response.text)
        
        return result
    
    def _build_context(self, user_profile, garment, rule_reasons, score, verdict):
        """Build context string for Gemini"""
        reasons_text = "\n".join([f"- {r['text']} (-{r['penalty']} pts)" for r in rule_reasons])
        
        context = f"""
USER PROFILE:
- Color Season: {user_profile.get('skin_season')}
- Body Shape: {user_profile.get('body_shape')}
- Skin Undertone: {user_profile.get('skin_undertone')}
- Contrast Level: {user_profile.get('contrast_level')}

GARMENT:
- Name: {garment.get('name')}
- Color: {garment.get('color_name')}
- Silhouette: {garment.get('silhouette')}
- Shoulder Emphasis: {garment.get('shoulder_emphasis')}
- Visual Weight: {garment.get('visual_weight')}

RULE ENGINE ANALYSIS:
Score: {score}/100
Verdict: {verdict}

Penalties Applied:
{reasons_text}
"""
        return context.strip()
    
    def _create_prompt(self, context, verdict):
        """Create the prompt for Gemini"""
        
        prompt = f"""You are a brutally honest fashion stylist. DO NOT be polite or encouraging unless facts support it.

{context}

TASK:
1. Explain WHY this verdict applies in 2-3 sentences max. Be direct and specific.
2. Suggest ONE specific pivot garment (by type and color) that would work better.
3. Explain WHY the pivot works in 1-2 sentences.

OUTPUT FORMAT:
EXPLANATION: [2-3 sentences, brutally honest]
PIVOT: [garment type + color, e.g., "Fitted navy sweater instead"]
PIVOT_WHY: [1-2 sentences explaining why]

TONE RULES:
- No "I think" or "perhaps" - be definitive
- No upselling or being nice
- Use facts from the profile and rule engine
- Be specific (not "something darker" but "charcoal gray")
"""
        return prompt.strip()
    
    def _parse_response(self, text: str) -> Dict:
        """Parse Gemini response into structured format"""
        
        result = {
            "why_verdict": "",
            "pivot_suggestion": "",
            "pivot_reason": ""
        }
        
        lines = text.split("\n")
        
        for i, line in enumerate(lines):
            if line.startswith("EXPLANATION:"):
                result["why_verdict"] = line.replace("EXPLANATION:", "").strip()
            elif line.startswith("PIVOT:"):
                result["pivot_suggestion"] = line.replace("PIVOT:", "").strip()
            elif line.startswith("PIVOT_WHY:"):
                result["pivot_reason"] = line.replace("PIVOT_WHY:", "").strip()
        
        # Fallback if parsing fails
        if not result["why_verdict"]:
            result["why_verdict"] = text[:200] + "..."
        
        if not result["pivot_suggestion"]:
            result["pivot_suggestion"] = "A different style to try"
        
        if not result["pivot_reason"]:
            result["pivot_reason"] = "This would suit you better based on your profile."
        
        return result
