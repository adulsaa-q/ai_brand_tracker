import streamlit as st
import json
import os

st.set_page_config(
    page_title="Thailand AI Market & Decision Intelligence",
    page_icon="🇹🇭",
    layout="wide"
)

st.title("🇹🇭 Thailand AI Market & Decision Intelligence Platform")
st.caption("Generative Engine Optimization (GEO) · Multi-Model Share of Voice · Thai Consumer Intent")

summary_file = "data/latest_run_summary.json"
if not os.path.exists(summary_file):
    st.info("💡 ไม่พบข้อมูลล่าสุด กรุณารัน Pipeline จำลองข้อมูลก่อน")
    if st.button("🚀 รัน Offline Simulation Pipeline ทันที"):
        from src.runner import run_intelligence_pipeline
        run_intelligence_pipeline(count=15, seed=42, engine_type="mock")
        st.rerun()
    st.stop()

with open(summary_file, "r", encoding="utf-8") as f:
    data = json.load(f)

metrics = data.get("metrics", {})
brands = metrics.get("brands", [])
observations = data.get("observations", [])
opportunities = data.get("opportunities", [])

st.sidebar.header("⚙️ Controls & Filters")
selected_vertical = st.sidebar.selectbox("อุตสาหกรรม (Vertical)", ["E-Commerce & Beauty Retail", "Banking (Coming Soon)", "Healthcare (Coming Soon)"])

tab1, tab2, tab3 = st.tabs(["📊 Share of Voice & Ranking", "🔍 Thai Consumer Queries", "💡 Strategic Actions"])

with tab1:
    st.subheader("📈 AI Share of Voice & Net Recommendation Score")
    if brands:
        top_brand = brands[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Queries Audited", metrics.get("total_queries", 0))
        c2.metric("Top Recommended Brand", top_brand["brand"], f"{top_brand['share_of_voice_pct']}% SoV")
        c3.metric("Best Avg Rank", f"#{top_brand['average_rank']}", "Rank 1 = Top Choice")
        c4.metric("Net Sentiment Score", f"{top_brand['net_sentiment_score']}%", "Positive Ratio")
        st.divider()
        st.write("### Brand Comparison Matrix")
        st.table(brands)

with tab2:
    st.subheader("🔍 Thai Consumer Queries & Citations")
    for idx, obs in enumerate(observations[:6], start=1):
        with st.expander(f"Q{idx}: {obs['query_text']} ({obs.get('category', 'ทั่วไป')})"):
            st.write(f"**AI Response:**\n{obs['response_raw_text']}")
            st.write("**Brand Mentions:**")
            st.json(obs.get("brand_mentions", []))

with tab3:
    st.subheader("💡 Strategic Opportunities & Actions")
    if opportunities:
        for opp in opportunities:
            st.warning(f"⚠️ **{opp['title']}**\n\n**Impact:** {opp['impact']}\n\n**Recommended Action:** {opp['recommended_action']}")
    else:
        st.success("✅ แบรนด์ครองความเป็นผู้นำในทุกคำถามสำคัญ!")
