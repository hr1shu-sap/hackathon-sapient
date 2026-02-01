# feedback_dashboard.py

import json
import streamlit as st
import pandas as pd
from pathlib import Path
from collections import Counter

LOG_FILE = Path("rlhf_logs/feedback_events.jsonl")
TRUST_FILE = Path("rlhf_logs/user_trust.json")

st.set_page_config(page_title="Honest Stylist – Feedback Analytics", layout="wide")

st.title("📊 Honest Stylist – Feedback Analytics")

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

def load_feedback():
    if not LOG_FILE.exists():
        return []

    records = []
    with open(LOG_FILE) as f:
        for line in f:
            records.append(json.loads(line))
    return records


def load_trust():
    if not TRUST_FILE.exists():
        return {}
    with open(TRUST_FILE) as f:
        return json.load(f)


data = load_feedback()
trust = load_trust()

if not data:
    st.warning("No feedback data yet.")
    st.stop()

df = pd.DataFrame(data)

# --------------------------------------------------
# HIGH-LEVEL METRICS
# --------------------------------------------------

st.markdown("## 🔍 System Health")

agree_rate = df["user_feedback"].apply(lambda x: x.get("agree") is True).mean()
override_rate = df["user_feedback"].apply(lambda x: bool(x.get("override"))).mean()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Feedback", len(df))
col2.metric("Agreement Rate", f"{agree_rate:.2%}")
col3.metric("Override Rate", f"{override_rate:.2%}")
col4.metric("Unique Users", df["user_id"].nunique())

# --------------------------------------------------
# TRUST SCORES
# --------------------------------------------------

st.markdown("## 🧠 User Trust Scores")

trust_df = pd.DataFrame.from_dict(trust, orient="index")
trust_df["trust_score"] = trust_df["agree"] / trust_df["total"]

st.dataframe(
    trust_df.sort_values("trust_score", ascending=False),
    use_container_width=True
)

# --------------------------------------------------
# EXPLANATION ANALYSIS
# --------------------------------------------------

st.markdown("## 💬 Explanation Quality")

explanations = df["response"]
feedback = df["user_feedback"]

accepted = explanations[feedback.apply(lambda x: x.get("agree") is True)]
rejected = explanations[feedback.apply(lambda x: x.get("agree") is False)]

col1, col2 = st.columns(2)

with col1:
    st.subheader("✔️ Accepted Explanations")
    for e in accepted.head(5):
        st.success(e)

with col2:
    st.subheader("❌ Rejected Explanations")
    for e in rejected.head(5):
        st.error(e)

# --------------------------------------------------
# FAILURE MODES
# --------------------------------------------------

st.markdown("## 🚨 Common Failure Signals")

reason_texts = []
for ctx in df["context"]:
    for r in ctx.get("rule_result", {}).get("reasons", []):
        reason_texts.append(r.get("text", ""))

common_failures = Counter(reason_texts).most_common(10)

st.bar_chart(
    pd.DataFrame(common_failures, columns=["Reason", "Count"]).set_index("Reason")
)

# --------------------------------------------------
# LEARNING OPPORTUNITIES
# --------------------------------------------------

st.markdown("## 🎯 Learning Opportunities")

comments = df["user_feedback"].apply(lambda x: x.get("comment")).dropna()

st.subheader("Most Common User Corrections")
for c, count in Counter(comments).most_common(5):
    st.write(f"• **{c}** ({count})")

# --------------------------------------------------
# RAW DATA (OPTIONAL)
# --------------------------------------------------

with st.expander("🔎 Raw Feedback Records"):
    st.dataframe(df, use_container_width=True)