import streamlit as st
import altair as alt

def render_civilization(state, living_df):
    st.subheader("🏛️ Civilization & Technology")
    
    # 1. Era & Evo Score
    era = state.globals.get('era', 'Paleolithic')
    score = state.globals.get('evo_score', 0)
    
    e1, e2 = st.columns([3, 1])
    e1.metric("Current Era", era, delta=f"Evo Score: {score:.0f}")
    
    # Progress Bar based on Era
    thresholds = {'Paleolithic': 500, 'Mesolithic': 1500, 'Neolithic': 5000, 'Bronze Age': 10000}
    target = thresholds.get(era, 10000)
    # If Era is Bronze Age, we are max?
    if era == 'Bronze Age':
        st.progress(1.0)
    else:
        try:
            prog = min(1.0, score / target)
        except ZeroDivisionError:
            prog = 0.0
        st.progress(prog, text=f"Progress to Next Age ({prog:.1%})")
        
    st.markdown("---")
    
    # --- World Map ---
    st.subheader("🌍 World Map (Tribal Territories)")
    
    if 'x' in living_df.columns and not living_df.empty:
        # Create Map with Altair
        
        # Layer 1: Terrain (Background)
        terrain_chart = None
        if hasattr(state, 'map_data') and state.map_data is not None:
            # Rect mark for grid (Explicit Tiling)
            # Use x, y, x2, y2 to define the box
            terrain_chart = alt.Chart(state.map_data).mark_rect().encode(
                x=alt.X('x', scale=alt.Scale(domain=[0, 100]), axis=None),
                y=alt.Y('y', scale=alt.Scale(domain=[0, 100]), axis=None),
                x2='x2',
                y2='y2',
                color=alt.Color('color', scale=None), # Use direct hex color
                tooltip=['terrain', 'resource_bonus']
            ).properties(
                width=600,
                height=600
            )

        # Layer 2: Agents (Foreground)
        base = alt.Chart(living_df).encode(
            x=alt.X('x', scale=alt.Scale(domain=[0, 100]), axis=None),
            y=alt.Y('y', scale=alt.Scale(domain=[0, 100]), axis=None),
            color=alt.Color('tribe_id', legend=alt.Legend(title="Tribe")),
            tooltip=['id', 'age', 'job', 'tribe_id']
        )
        
        points = base.mark_circle(size=60, opacity=0.8).interactive()
        
        # Layering
        if terrain_chart:
            final_chart = terrain_chart + points
        else:
            final_chart = points
            
        st.altair_chart(final_chart, use_container_width=True)
        
    else:
        st.info("No spatial data initialized yet.")

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("⚔️ Distinct Tribes")
        if 'tribe_id' in living_df.columns:
            # Pie Chart
            tribe_counts = living_df['tribe_id'].value_counts().reset_index()
            tribe_counts.columns = ['Tribe', 'Count']
            
            # Custom Colors if we can map them?
            # Altair allows domain/range colors
            base = alt.Chart(tribe_counts).encode(theta=alt.Theta("Count", stack=True))
            pie = base.mark_arc(outerRadius=120).encode(
                color=alt.Color("Tribe"),
                tooltip=["Tribe", "Count"]
            )
            st.altair_chart(pie)
    
    with c2:
        st.subheader("📚 Knowledge & Skills")
        
        if hasattr(state, 'skills') and not state.skills.empty:
            # Show top discovered skills
            sdf = state.skills
            skill_counts = sdf['skill'].value_counts()
            
            # Max level per skill
            max_levels = sdf.groupby('skill')['level'].max()
            
            st.write("**Discovered Technologies:**")
            for skill, count in skill_counts.items():
                lvl = max_levels.get(skill, 0)
                st.write(f"- **{skill}** (Learners: {count}, Max Mastery: {lvl:.2f})")
                
        else:
            st.info("No skills discovered yet. Wait for an Einstein!")
