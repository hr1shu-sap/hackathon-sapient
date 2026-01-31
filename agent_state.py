from typing import TypedDict, Optional, List, Dict
from vision_analyzer import VisionAnalyzer 
from rule_engine import StylingAnalyzer
from gemini_explainer import GeminiExplainer
from ai_recommender import AIRecommender
from garment_catalog import get_full_catalog
from feedback_logger import feedback_to_reward, log_feedback
import os


class StylistState(TypedDict):
    # Inputs
    image_path: str
    garment: Dict

    # Vision
    user_profile: Optional[Dict]
    confidence: float

    # Rules
    rule_result: Optional[Dict]
    verdict_score: Optional[int]

    # LLM outputs
    explanation: Optional[Dict]
    recommendations: Optional[List[Dict]]

    # RLHF
    user_feedback: Optional[str]
    reward: Optional[float]

# Node functions — implemented at module level (not inside the TypedDict)
def vision_node(state: StylistState):
    vision = VisionAnalyzer()
    profile = vision.analyze_photo(state["image_path"])

    return {
        **state,
        "user_profile": profile,
        "confidence": profile.get("confidence", 0.0),
    }


def confidence_router(state: StylistState):
    if state.get("confidence", 0.0) < 0.4:
        return "end"
    return "rules"


def rule_node(state: StylistState):
    analyzer = StylingAnalyzer()
    result = analyzer.analyze(
        state.get("user_profile"),
        state.get("garment"),
    )

    return {
        **state,
        "rule_result": result,
        "verdict_score": result.get("score") if isinstance(result, dict) else None,
    }


def verdict_router(state: StylistState):
    score = state.get("verdict_score") or 0
    if score < 60:
        return "recommend"
    return "explain"


def explain_node(state: StylistState):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return state

    explainer = GeminiExplainer(api_key)
    explanation = explainer.explain_verdict(
        verdict=(state.get("rule_result") or {}).get("verdict", ""),
        user_profile=state.get("user_profile"),
        garment=state.get("garment"),
        rule_reasons=(state.get("rule_result") or {}).get("reasons", []),
        score=state.get("verdict_score"),
    )

    return {**state, "explanation": explanation}


def recommendation_node(state: StylistState):
    recommender = AIRecommender()

    recs = recommender.recommend(
        user_profile=state.get("user_profile"),
        current_garment=state.get("garment"),
        catalog=get_full_catalog(),
        rule_result=state.get("rule_result"),
    )

    return {**state, "recommendations": recs}


def feedback_node(state: StylistState):
    reward = feedback_to_reward(state.get("user_feedback"))
    return {**state, "reward": reward}


def learning_node(state: StylistState):
    log_feedback({
        "garment_sku": (state.get("garment") or {}).get("sku"),
        "score": state.get("verdict_score"),
        "reward": state.get("reward"),
        "season": (state.get("user_profile") or {}).get("season"),
        "body_shape": (state.get("user_profile") or {}).get("body_shape"),
    })
    return state




    
