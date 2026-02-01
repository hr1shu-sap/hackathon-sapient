# recommendation_agent.py

from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END

from garment_catalog import get_full_catalog
from ai_recommender import AIRecommender


# --------------------------------------------------
# STATE DEFINITION
# --------------------------------------------------

class RecommendationState(TypedDict):
    user_profile: Dict
    current_garment: Dict
    rule_result: Dict
    candidates: List[Dict]
    recommendations: List[Dict]


# --------------------------------------------------
# NODES
# --------------------------------------------------

def load_catalog_node(state: RecommendationState):
    catalog = get_full_catalog()

    candidates = [
        g for g in catalog
        if g.get("sku") != state["current_garment"].get("sku")
    ]

    return {**state, "candidates": candidates}


def recommend_node(state: RecommendationState):
    recommender = AIRecommender(
        gemini_client=state.get("gemini_client")
    )

    recs = recommender.recommend(
        user_profile=state["user_profile"],
        current_garment=state["current_garment"],
        rule_result=state["rule_result"],
        top_k=3,
        catalog=state["candidates"]
    )

    return {**state, "recommendations": recs}


# --------------------------------------------------
# GRAPH
# --------------------------------------------------

def build_recommendation_agent():
    graph = StateGraph(RecommendationState)

    graph.add_node("load_catalog", load_catalog_node)
    graph.add_node("recommend", recommend_node)

    graph.set_entry_point("load_catalog")
    graph.add_edge("load_catalog", "recommend")
    graph.add_edge("recommend", END)

    return graph.compile()


recommendation_agent = build_recommendation_agent()