import streamlit as st

def render_genetics(living_df):
    st.subheader("🧬 Genetics & Evolution")
    
    if 'genetic_vulnerability' in living_df.columns:
        avg_vul = living_df['genetic_vulnerability'].mean()
        high_risk_count = len(living_df[living_df['genetic_vulnerability'] > 0.7])
        
        g1, g2 = st.columns(2)
        g1.metric("Avg Genetic Vulnerability", f"{avg_vul:.3f}", help="0.0 = Diverse, 1.0 = Clone")
        g2.metric("High Risk (Inbred)", high_risk_count, delta="Vulnerable Agents")
        
        st.markdown("#### Vulnerability Distribution")
        # Histogram
        st.bar_chart(living_df['genetic_vulnerability'])
        
        st.markdown("#### Skin Tone Distribution")
        if 'skin_tone' in living_df.columns:
            st.bar_chart(living_df['skin_tone'])
        else:
            st.info("Skin tone data not available yet (wait for next gen).")
        
    st.info("Genetic Vulnerability increases with inbreeding (parents with similar genomes). High vulnerability leads to weaker immunity.")
