# import os
# from langgraph.graph import StateGraph

# from agent_state import StylistState
# from vision_analyzer import VisionAnalyzer
# from rule_engine import StylingAnalyzer
# from gemini_explainer import GeminiExplainer
# from garment_catalog import get_full_catalog
# from feedback_logger import log_feedback, feedback_to_reward
# from ai_recommender import AIRecommender  # if you have this

# # --------------------------------------------------
# # Nodes
# # --------------------------------------------------

# def vision_node(state: StylistState):
#     vision = VisionAnalyzer()
#     profile = vision.analyze_photo(state["image_path"])

#     return {
#         **state,
#         "user_profile": profile,
#         "confidence": profile.get("confidence", 0.0)
#     }


# def confidence_router(state: StylistState):
#     if state["confidence"] < 0.4:
#         return "stop"
#     return "rules"


# def rule_node(state: StylistState):
#     analyzer = StylingAnalyzer()
#     result = analyzer.analyze(
#         state["user_profile"],
#         state["garment"]
#     )

#     return {
#         **state,
#         "rule_result": result,
#         "verdict_score": result["score"]
#     }


# def verdict_router(state: StylistState):
#     if state["verdict_score"] < 60:
#         return "recommend"
#     return "explain"


# def explain_node(state: StylistState):
#     api_key = os.getenv("GOOGLE_API_KEY")
#     if not api_key:
#         return state

#     explainer = GeminiExplainer(api_key)
#     explanation = explainer.explain_verdict(
#         verdict=state["rule_result"].get("verdict", ""),
#         user_profile=state["user_profile"],
#         garment=state["garment"],
#         rule_reasons=state["rule_result"]["reasons"],
#         score=state["verdict_score"]
#     )

#     return {**state, "explanation": explanation}


# def recommend_node(state: StylistState):
#     recommender = AIRecommender()

#     recs = recommender.recommend(
#         user_profile=state["user_profile"],
#         current_garment=state["garment"],
#         catalog=get_full_catalog(),
#         rule_result=state["rule_result"]
#     )

#     return {**state, "recommendations": recs}


# def feedback_node(state: StylistState):
#     reward = feedback_to_reward(state.get("user_feedback"))

#     return {
#         **state,
#         "reward": reward
#     }


# def learning_node(state: StylistState):
#     log_feedback({
#         "garment_sku": state["garment"]["sku"],
#         "score": state["verdict_score"],
#         "reward": state.get("reward"),
#         "season": state["user_profile"].get("season"),
#         "body_shape": state["user_profile"].get("body_shape")
#     })

#     return state


# # --------------------------------------------------
# # Graph
# # --------------------------------------------------

# graph = StateGraph(StylistState)

# graph.add_node("vision", vision_node)
# graph.add_node("rules", rule_node)
# graph.add_node("explain", explain_node)
# graph.add_node("recommend", recommend_node)
# graph.add_node("feedback", feedback_node)
# graph.add_node("learn", learning_node)
# graph.add_node("stop", lambda s: s)  # dummy safe stop node

# # Entry
# graph.set_entry_point("vision")

# # Routing
# graph.add_conditional_edges(
#     "vision",
#     confidence_router,
#     {
#         "rules": "rules",
#         "stop": "stop"
#     }
# )

# graph.add_conditional_edges(
#     "rules",
#     verdict_router,
#     {
#         "recommend": "recommend",
#         "explain": "explain"
#     }
# )

# # Flow
# graph.add_edge("recommend", "explain")
# graph.add_edge("explain", "feedback")
# graph.add_edge("feedback", "learn")

# # Finish
# graph.set_finish_point("learn")

# # Compile
# stylist_agent = graph.compile()


# stylist_agent.py
from typing import TypedDict
from langgraph.graph import StateGraph

from vision_analyzer import VisionAnalyzer
from rule_engine import StylingAnalyzer

# -------- State --------
class StylistState(TypedDict):
    image_path: str
    garment: dict
    user_profile: dict
    rule_result: dict

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

# -------- Graph --------
graph = StateGraph(StylistState)

graph.add_node("vision", vision_node)
graph.add_node("rules", rule_node)

graph.set_entry_point("vision")
graph.add_edge("vision", "rules")
graph.set_finish_point("rules")

stylist_agent = graph.compile()
