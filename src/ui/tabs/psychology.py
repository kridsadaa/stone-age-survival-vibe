import streamlit as st

def render_psychology(living_df):
    st.subheader("🧠 Tribal Psychology")
    
    if 'happiness' in living_df.columns:
        avg_happy = living_df['happiness'].mean()
        rebels = len(living_df[living_df['rebellion'] > 0.5])
        criminals = len(living_df[living_df['criminal_history'] > 0])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("😊 Avg Happiness", f"{avg_happy:.1f}", help="Below 50 is bad. Below 20 is RIOT.")
        c2.metric("😠 Rebels", rebels, delta="Dissidents", delta_color="inverse")
        c3.metric("👮 Criminals", criminals, delta="Thieves")
        
        st.markdown("#### Mind State")
        st.bar_chart(living_df[['happiness', 'rebellion']].head(50))
        
        # Ocean Distribution
        st.markdown("#### Personality Types (OCEAN)")
        st.scatter_chart(living_df, x='trait_openness', y='trait_conscientiousness', color='job')
        
        # Deep Psychology Split
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### ❤️ Libido & Attractiveness")
            if 'libido' in living_df.columns:
                 st.scatter_chart(living_df, x='libido', y='attractiveness', color='gender')
            else:
                 st.info("No Libido data.")
                 
        with c2:
            st.markdown("#### 🧠 Impulse Control (Prefrontal Cortex)")
            # Control = min(1.0, Age/25)
            # Visualize Age vs Rebellion to show the correlation
            st.scatter_chart(living_df, x='age', y='rebellion', color='trait_neuroticism')
            st.caption("Note: Youth (Age < 25) have higher rebellion/volatility due to undeveloped brains.")
