import streamlit as st
from src.engine.core import WorldState

def render_governance(state: WorldState):
    """
    Renders the Governance Control Panel.
    Displays:
    1. Active Policies (Mating, Rationing).
    2. Tribe Chiefs (Political Structure).
    3. AI Status (Brain Logs).
    """
    st.header("📜 Tribal Governance")
    st.caption("Decentralized Command: Each tribe follows its own Spirit.")
    
    if not hasattr(state, 'tribes') or not state.tribes:
        st.warning("No tribes established yet.")
        return

    # Tribe Selector
    tribe_options = list(state.tribes.keys())
    selected_tid = st.selectbox("Select Tribe to Inspect", tribe_options)
    
    # Get Tribe Data
    tribe_data = state.tribes[selected_tid]
    policies = tribe_data.get('policies', {})
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader(f"⚖️ {selected_tid} Policies")
        
        # Mating Policy
        m_policy = policies.get('mating_label', 'Strict')
        st.write(f"**Mating Policy:** {m_policy}")
        if m_policy == 'Strict':
            st.info("🚫 **Strict Duty**: Only fittest couples may breed.")
        else:
            st.success("💕 **Open Love**: Everyone is free to love.")
            
        st.divider()
        
        # Rationing Policy
        r_policy = policies.get('rationing_label', 'Communal')
        st.write(f"**Rationing Policy:** {r_policy}")
        if r_policy == 'Communal':
            st.info("🍲 **Communal Sharing**: Food is shared equally.")
        elif r_policy == 'Meritocracy':
            st.warning("🏆 **Meritocracy**: Workers & Chiefs eat first.")
        elif r_policy == 'ChildFirst':
            st.success("👶 **Children First**: The future comes first.")

    with col2:
        st.subheader(f"👑 {selected_tid} Leadership")
        
        chief_id = tribe_data.get('chief_id')
        if chief_id:
            st.success(f"**Chief {chief_id}** is leading.")
        else:
            st.error("No Leader! Anarchy prevails.")
 
    st.divider()
    
    # AI Action Log & Spirit
    st.subheader(f"👻 Spirit of the {selected_tid} (AI Brain)")
    
    if 'engine' in st.session_state:
        engine = st.session_state.engine
        
        # Find CultureSystem
        ai_system = None
        for s in engine.systems:
            if hasattr(s, 'brains'): # New attribute
                ai_system = s
                break
        
        if ai_system:
            c1, c2 = st.columns([2, 1])
            
            with c1:
                st.markdown("### 🧠 Brain Activity")
                # Get Specific Brain
                brain = ai_system.brains.get(selected_tid, {})
                last_state = ai_system.last_states.get(selected_tid)
                
                if last_state:
                    st.write(f"**Observed State:** {last_state}")
                
                if brain:
                    st.caption(f"Knowledge Size: {len(brain)} States")
                    
                    if last_state:
                         current_q = brain.get(last_state)
                         if current_q:
                             st.markdown("#### 📊 Current Decision Values")
                             
                             actions = [
                                 "M+ R+", "M+ R=", "M+ R-",
                                 "M= R+", "M= R=", "M= R-",
                                 "M- R+", "M- R=", "M- R-"
                             ]
                             
                             chart_data = {"Action": actions, "Q-Value": current_q}
                             st.bar_chart(chart_data, x="Action", y="Q-Value", color="#FF4B4B")
                         else:
                             st.info("Current state is new. Exploring...")
                else:
                    st.warning("Brain Empty (New Tribe).")

            with c2:
                st.markdown("### ⚙️ Brain Control")
                if st.button(f"🤯 Reset {selected_tid} Brain"):
                     if hasattr(ai_system, 'reset_brain'):
                         ai_system.reset_brain(tid=selected_tid)
                         st.success("Memory Wiped!")
                         st.rerun()
        else:
            st.warning("Culture System (AI) not found or incompatible.")
    else:
        st.error("Engine not found.")
