import streamlit as st
from src.systems.culture import CultureSystem

def render_spirit(state, living_df, engine):
    st.subheader("👻 The Spirit of the Tribe (AI)")
    
    # Chief Profile
    chief_id = state.globals.get('chief_id')
    if chief_id:
        chief_row = living_df[living_df['id'] == chief_id]
        if not chief_row.empty:
            c = chief_row.iloc[0]
            st.success(f"👑 **Chief {c['id']}**\n\nAge: **{c['age']:.1f}**")
            cols = st.columns(3)
            cols[0].write(f"Wisdom (C): {c['trait_conscientiousness']:.2f}")
            cols[1].write(f"Kindness (A): {c['trait_agreeableness']:.2f}")
            cols[2].write(f"Chaos (N): {c['trait_neuroticism']:.2f}")
    else:
        st.warning("No Chief elected yet!")
        
    culture_sys = next((s for s in engine.systems if isinstance(s, CultureSystem)), None)
    if culture_sys:
        # Current Policies
        st.markdown("### ⚖️ Tribal Laws (AI Controlled)")
        
        # Mating Strictness
        m_strict = state.globals.get('policy_mating_strictness', 0.5)
        m_label = "Free Love"
        if m_strict > 0.8: m_label = "🧬 Eugenics (Strict)"
        elif m_strict > 0.4: m_label = "🚫 Incest Ban (No Siblings)"
        else: m_label = "❤️ Free Love (Risk High)"
        
        st.write(f"**Mating Law:** {m_label}")
        st.progress(m_strict)
        
        # Rationing Strictness
        r_strict = state.globals.get('policy_rationing_strictness', 0.5)
        r_label = "Communism"
        if r_strict > 0.6: r_label = "🛡️ Women & Children First"
        elif r_strict > 0.3: r_label = "⚒️ Workers First"
        else: r_label = "🍞 Shared Equally"
        
        st.write(f"**Rationing Law:** {r_label}")
        st.progress(r_strict)
        
        st.markdown("---")
        st.markdown("### Brain Activity")
        if culture_sys.last_state:
            st.write(f"**Observed State:** {culture_sys.last_state}")
            st.write(f"**Last Reward:** {culture_sys._calculate_reward(state):.2f}")
            
        # Reset Button (User Requested)
        if st.button("🤯 Reset AI Brain"):
            culture_sys.reset_brain()
            st.success("AI Memory Wiped! Starting fresh reinforcement learning...")
            st.rerun()
        
        # Q-Table Visualization
        if culture_sys.q_table:
            st.text(f"Brain Knowledge Size: {len(culture_sys.q_table)} States")
            # Convert Q-Table to DataFrame for view
            q_data = []
            for k, v in list(culture_sys.q_table.items())[:10]: # Show top 10
                row = {"State": str(k), "Values": str([f"{x:.1f}" for x in v])}
                q_data.append(row)
            st.table(q_data)
    else:
        st.error("Spirit AI not found.")
