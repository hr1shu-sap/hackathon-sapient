
# stylist_agent.py
from typing import TypedDict
from langgraph.graph import StateGraph

from vision_analyzer import VisionAnalyzer
from rule_engine import StylingAnalyzer
from recommendation_agent import recommendation_agent
from gemini_explainer import explanation_node
from feedback_logger import FeedbackLogger

# -------- State --------
class StylistState(TypedDict):
    image_path: str
    garment: dict

    user_profile: dict
    rule_result: dict
    explanation: dict
    recommendations: list

    # 🧠 RLHF
    user_feedback: dict | None
    reward: float | None


vision = VisionAnalyzer()
rules = StylingAnalyzer()

# -------- Nodes --------
def vision_node(state: StylistState):
    profile = vision.analyze_photo(state["image_path"])
    return {"user_profile": profile}

def rule_node(state: StylistState):
    result = rules.analyze(
        user_profile=state["user_profile"],
        garment=state["garment"]
    )
    return {"rule_result": result}

def recommendation_node(state):
    rec_state = recommendation_agent.invoke({
        "user_profile": state["user_profile"],
        "current_garment": state["garment"],
        "rule_result": state["rule_result"],
        "gemini_client": state.get("gemini_client")
    })

    return {
        **state,
        "recommendations": rec_state["recommendations"]
    }

def feedback_capture_node(state: StylistState):
    return {
        **state,
        "user_feedback": state.get("user_feedback")
    }

def feedback_update_node(state: StylistState):
    feedback = state.get("user_feedback")
    if not feedback:
        return state

    reward = 0.0

    # --- Verdict agreement ---
    if feedback.get("verdict_agree") is True:
        reward += 1.0
    elif feedback.get("verdict_agree") is False:
        reward -= 1.0

    # --- Explanation quality ---
    reward += (feedback.get("explanation_helpful", 3) - 3) * 0.3

    # --- Recommendation trust ---
    if feedback.get("recommendation_clicked"):
        reward += 1.2

    # --- User-written correction (gold) ---
    if feedback.get("user_reason"):
        reward += 0.5

    # 🔐 Persist learning
    FeedbackLogger.log(
        state=state,
        reward=reward
    )

    return {
        **state,
        "reward": reward
    }



# -------- Graph --------
graph = StateGraph(StylistState)

graph.add_node("vision", vision_node)
graph.add_node("rules", rule_node)
graph.add_node("explanation", explanation_node)
graph.add_node("recommendation", recommendation_node)
graph.add_node("feedback_capture", feedback_capture_node)
graph.add_node("feedback_update", feedback_update_node)

graph.set_entry_point("vision")

graph.add_edge("vision", "rules")
graph.add_edge("rules", "explanation")
graph.add_edge("explanation", "recommendation")
graph.add_edge("recommendation", "feedback_capture")
graph.add_edge("feedback_capture", "feedback_update")
graph.set_exit_point("feedback_update")

stylist_agent = graph.compile()

