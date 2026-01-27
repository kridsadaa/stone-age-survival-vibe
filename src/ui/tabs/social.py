import streamlit as st

def render_social(state, living_df):
    st.subheader("🕸️ Social Web (Kinship & Affairs)")
    
    if hasattr(state, 'relationships') and not state.relationships.empty:
        rels = state.relationships
        
        # Stats
        r_counts = rels['type'].value_counts()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Connections", len(rels))
        c2.metric("❤️ Lovers/Spouses", r_counts.get('Lover', 0) + r_counts.get('Spouse', 0))
        c3.metric("💔 Ex-Partners", r_counts.get('Ex', 0))
        
        st.markdown("#### Relationship Types")
        st.bar_chart(r_counts)
        
        st.markdown("#### Recent Romances")
        # Show last 10
        recent = rels.sort_values('start_day', ascending=False).head(10)
        st.dataframe(recent)
        
        # Family Sizes (Children count per mother)
        # We can aggregate from population 'mother_id'
        if 'mother_id' in living_df.columns:
            kids_count = living_df['mother_id'].value_counts()
            st.markdown("#### Top Mothers (Most Children)")
            st.bar_chart(kids_count.head(20))
            
    else:
        st.info("No social web formed yet (Wait for relationships to form).")
