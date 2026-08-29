import json
import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

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
    st.info("💡 ไม่พบข้อมูลการตรวจวัดล่าสุด กรุณากดปุ่มด้านล่างเพื่อรัน Intelligence Pipeline")
    if st.button("🚀 รัน Offline Simulation Pipeline ทันที (0 API Key)"):
        from src.runner import run_intelligence_pipeline
        run_intelligence_pipeline(count=20, seed=42, engine_type="mock", include_control=True)
        st.rerun()
    st.stop()

with open(summary_file, encoding="utf-8") as f:
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
selected_vertical = st.sidebar.selectbox("อุตสาหกรรม (Vertical)", ["E-Commerce & Beauty Retail", "Banking & FinTech (Coming Soon)", "Healthcare (Coming Soon)", "Automotive EV (Coming Soon)"])

st.sidebar.subheader("📅 Temporal Context Active")
for ev in active_events:
    st.sidebar.info(f"✨ **{ev.get('name_th', '')}**")

st.sidebar.divider()
if st.sidebar.button("🔄 รัน Pipeline รอบใหม่ (Re-run)"):
    from src.runner import run_intelligence_pipeline
    run_intelligence_pipeline(count=20, seed=100, engine_type="mock", include_control=True)
    st.rerun()

# 6 Executive Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Share of Voice & Ranking",
    "🔍 Query Universe & Evidence",
    "🌐 Citation Influence Graph",
    "🛡️ Claim & Policy Audit",
    "💡 Strategic Opportunity Engine",
    "⚡ AI Knowledge Freshness & Lag"
])

with tab1:
    st.subheader("📈 AI Share of Voice (SoV) & Net Recommendation Score (NRS)")
    if brands:
        df_brands = pd.DataFrame(brands)
        top_brand = brands[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Queries Audited", metrics.get("total_queries", 0))
        c2.metric("Market Leader (SoV)", top_brand["brand"], f"{top_brand['share_of_voice_pct']}%")
        c3.metric("Top Recommendation NRS", f"{top_brand.get('net_recommendation_score', 0)}%", "Intent Weighted")
        c4.metric("Market Sentiment Index", f"{top_brand['net_sentiment_score']}%", "Positive Ratio")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_sov = px.bar(
                df_brands,
                x="brand",
                y="share_of_voice_pct",
                title="🏆 AI Share of Voice (Mention Rate %)",
                color="share_of_voice_pct",
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig_sov, use_container_width=True)

        with col_c2:
            fig_nrs = px.bar(
                df_brands,
                x="brand",
                y="net_recommendation_score",
                title="🎯 Net Recommendation Score (NRS %)",
                color="net_recommendation_score",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig_nrs, use_container_width=True)

        st.divider()
        st.write("### 🏆 Brand Comparison Matrix")
        st.dataframe(df_brands, use_container_width=True)

with tab2:
    st.subheader("🔍 Thai Consumer Queries & Evidence Drilldown")
    query_types = ["All Queries", "Control Benchmark Set", "Exploratory Dynamic Set"]
    selected_type = st.selectbox("Filter Query Set", query_types)
    
    filtered_obs = observations
    if selected_type == "Control Benchmark Set":
        filtered_obs = [o for o in observations if o.get("is_control_set")]
    elif selected_type == "Exploratory Dynamic Set":
        filtered_obs = [o for o in observations if not o.get("is_control_set")]

    st.write(f"แสดงทั้งหมด **{len(filtered_obs)}** ข้อคำถาม:")
    for idx, obs in enumerate(filtered_obs[:12], start=1):
        tag = "📌 [CONTROL BENCHMARK]" if obs.get("is_control_set") else "⚡ [EXPLORATORY]"
        with st.expander(f"{tag} Q{idx}: {obs['query_text']} (หมวด: {obs.get('category', 'ทั่วไป')})"):
            st.markdown(f"**AI Grounded Response:**\n{obs.get('response_raw_text', '')}")
            st.markdown("**Structured Brand Mentions & Sentiment Breakdown:**")
            st.json(obs.get("brand_mentions", []))

with tab3:
    st.subheader("🌐 Web Citation & Source Authority Graph")
    st.write("เว็บไซต์และแหล่งข้อมูลที่มีอิทธิพลสูงสุดต่อการแนะนำแบรนด์ของ AI:")
    c_rankings = citations_data.get("domain_rankings", [])
    if c_rankings:
        df_citations = pd.DataFrame(c_rankings)
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            fig_donut = px.pie(
                df_citations.head(8),
                names="domain",
                values="citation_count",
                title="🍩 Top Cited Web Domains by AI",
                hole=0.4
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        with col_c2:
            st.write("### 🏆 Domain Authority Leaderboard")
            st.dataframe(df_citations, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูล Citation ในชุดตัวอย่างนี้")

with tab4:
    st.subheader("🛡️ AI Claim Intelligence & Policy Verification")
    st.write("ตรวจสอบความถูกต้องของข้อความอ้างอิงโปรโมชั่น/เงื่อนไขที่ AI กล่าวถึง:")
    if claims_data:
        for cl in claims_data:
            badge = "⚠️ CONDITIONAL" if cl.get("audit_verdict") == "CONDITIONAL" else "✅ VERIFIED"
            st.warning(f"**[{badge}] {cl.get('brand')}**: อ้างถึง '{cl.get('extracted_claim')}'\n\n**ข้อเท็จจริง:** {cl.get('note')}")
    else:
        st.success("✅ ไม่พบข้อความ Hallucination หรือเงื่อนไขที่บิดเบือนในชุดตัวอย่าง")

with tab5:
    st.subheader("💡 Strategic Opportunity Engine & Prioritized Action Items")
    st.write("ค้นหาช่องว่างทางการตลาดและข้อเสนอแนะเชิงกลยุทธ์ตามกรอบ **What? Why? So What? Now What?:**")
    if opportunities:
        for opp in opportunities:
            st.error(f"🚨 **{opp.get('title')}**  `{opp.get('priority', 'P1')}`\n\n"
                     f"• **ผลกระทบ:** {opp.get('impact')}\n\n"
                     f"• **หลักฐาน:** {opp.get('evidence', '')}\n\n"
                     f"• **คำแนะนำเชิงกลยุทธ์:** {opp.get('recommended_action')}")
    else:
        st.success("✅ แบรนด์ครองความเป็นผู้นำในทุกคำถามสำคัญ")

with tab6:
    st.subheader("⚡ AI Information Freshness & Knowledge Lag")
    col_a, col_b = st.columns(2)
    col_a.metric("Grounding Real-Time Rate", lag_data.get("grounding_realtime_rate", "N/A"))
    col_b.metric("Information Lag Estimate", lag_data.get("estimated_information_lag", "N/A"))
    st.info(f"💡 **คำแนะนำด้านสถาปัตยกรรม:** {lag_data.get('recommendation', '')}")
