import streamlit as st
import json
import os
import sys

# Ensure src path is accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(
    page_title="Thailand AI Market & Decision Intelligence Platform",
    page_icon="🇹🇭",
    layout="wide"
)

st.title("🇹🇭 Thailand AI Market & Decision Intelligence Platform")
st.caption("Enterprise GEO · Multi-Model Share of Voice · Citation Influence Graph · Consumer Intent Engine")

summary_file = "data/latest_run_summary.json"
if not os.path.exists(summary_file):
    st.info("💡 ไม่พบข้อมูลการตรวจวัดล่าสุด กรุณารัน Pipeline เพื่อสร้างข้อมูลตัวอย่าง")
    if st.button("🚀 รัน Offline Simulation Pipeline ทันที (0 API Key)"):
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
citations_data = data.get("citations_analysis", {})
claims_data = data.get("claims_audit", [])
lag_data = data.get("information_lag", {})
active_events = data.get("active_events", [])

# Sidebar
st.sidebar.header("⚙️ Market Controls & Context")
selected_vertical = st.sidebar.selectbox("อุตสาหกรรม (Vertical)", ["E-Commerce & Beauty Retail", "Banking & Finance (Coming Soon)", "Healthcare (Coming Soon)"])

st.sidebar.subheader("📅 Temporal Context Active")
for ev in active_events:
    st.sidebar.info(f"✨ **{ev.get('name_th', '')}**")

# 6 Executive Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Share of Voice & Ranking",
    "🔍 Query Universe & Evidence",
    "🌐 Citation Influence Map",
    "🛡️ Claim & Policy Audit",
    "💡 Strategic Opportunity Engine",
    "⚡ AI Knowledge Freshness & Lag"
])

with tab1:
    st.subheader("📈 AI Share of Voice (SoV) & Net Recommendation Score (NRS)")
    if brands:
        top_brand = brands[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Queries Audited", metrics.get("total_queries", 0))
        c2.metric("Top Recommended Brand", top_brand["brand"], f"{top_brand['share_of_voice_pct']}% SoV")
        c3.metric("Best Avg Rank", f"#{top_brand['average_rank']}", "Rank 1 = Top Choice")
        c4.metric("Market Sentiment Index", f"{top_brand['net_sentiment_score']}%", "Positive Ratio")
        
        st.divider()
        st.write("### 🏆 Brand Comparison Matrix")
        st.table(brands)

with tab2:
    st.subheader("🔍 Thai Consumer Queries & Grounded Answers")
    for idx, obs in enumerate(observations[:8], start=1):
        with st.expander(f"Q{idx}: {obs['query_text']} (หมวดหมู่: {obs.get('category', 'ทั่วไป')})"):
            st.markdown(f"**AI Raw Response:**\\n{obs.get('response_raw_text', '')}")
            st.markdown("**Platform Mentions & Sentiment Breakdown:**")
            st.json(obs.get("brand_mentions", []))

with tab3:
    st.subheader("🌐 Web Citation & Source Authority Graph")
    st.write("เว็บไซต์และแหล่งข้อมูลที่มีอิทธิพลสูงสุดต่อการแนะนำแบรนด์ของ AI:")
    c_rankings = citations_data.get("domain_rankings", [])
    if c_rankings:
        st.table(c_rankings)
    else:
        st.info("ไม่พบข้อมูล Citation ในชุดตัวอย่างนี้")

with tab4:
    st.subheader("🛡️ AI Claim Intelligence & Policy Verification")
    st.write("ตรวจสอบความถูกต้องของข้อความอ้างอิงโปรโมชั่น/เงื่อนไขที่ AI กล่าวถึง:")
    if claims_data:
        for cl in claims_data:
            st.warning(f"⚠️ **{cl.get('brand')}**: อ้างถึง '{cl.get('extracted_claim')}'\\n\\n**ข้อเท็จจริง:** {cl.get('note')}")
    else:
        st.success("✅ ไม่พบข้อความ Hallucination หรือเงื่อนไขที่บิดเบือนในชุดตัวอย่าง")

with tab5:
    st.subheader("💡 Strategic White Space & Prioritized Action Items")
    if opportunities:
        for opp in opportunities:
            st.error(f"🚨 **{opp['title']}**\\n\\n**ผลกระทบ:** {opp['impact']}\\n\\n**คำแนะนำเชิงกลยุทธ์:** {opp['recommended_action']}")
    else:
        st.success("✅ แบรนด์ครองความเป็นผู้นำในทุกคำถามสำคัญ")

with tab6:
    st.subheader("⚡ AI Information Freshness & Knowledge Lag")
    col_a, col_b = st.columns(2)
    col_a.metric("Grounding Real-Time Rate", lag_data.get("grounding_realtime_rate", "N/A"))
    col_b.metric("Information Lag Estimate", lag_data.get("estimated_information_lag", "N/A"))
    st.info(f"💡 **คำแนะนำด้านสถาปัตยกรรม:** {lag_data.get('recommendation', '')}")
