import streamlit as st
import pandas as pd
import ast
import math

def render_inspector(living_df, state=None):
    """
    Renders the Agent Inspector with Master-Detail view.
    Master: Filterable/Paginated Table.
    Detail: Detailed tabs for selected agent.
    """
    st.header("🕵️ Agent Inspector (Master-Detail)")
    
    if living_df.empty and (state is None or state.population.empty):
        st.warning("No population to inspect.")
        return

    # --- MASTER VIEW (Browser) ---
    selected_id = _render_browser(living_df)
    
    st.divider()
    
    # --- DETAIL VIEW ---
    if selected_id:
        # Fetch fresh data for the selected ID
        agent_data = None
        
        # Priority 1: State Population (Includes recently deceased if frame preserved or if full history exists)
        if state is not None and hasattr(state, 'population') and not state.population.empty:
            matches = state.population[state.population['id'] == selected_id]
            if not matches.empty:
                agent_data = matches.iloc[0]
                
        # Priority 2: Living DF (Fallback)
        if agent_data is None and not living_df.empty:
             matches = living_df[living_df['id'] == selected_id]
             if not matches.empty:
                 agent_data = matches.iloc[0]
        
        if agent_data is not None:
            _render_details(agent_data, living_df)
        else:
            st.warning(f"⚠️ Agent {selected_id} is unavailable (Deceased/Exiled).")
            st.error(f"Agent {selected_id} not found (might have died).")

def _render_browser(df):
    """Renders filters, pagination, and data table."""
    with st.expander("🔎 Search & Filter", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        
        search_term = c1.text_input("Search Name/ID", "")
        
        roles = ["All"] + sorted(df['role'].astype(str).unique().tolist())
        role_filter = c2.selectbox("Role", options=roles)
        
        tribes = ["All"] + sorted(df.get('tribe_id', pd.Series(['None'])).astype(str).unique().tolist())
        tribe_filter = c3.selectbox("Tribe", options=tribes)
        
        sort_by = c4.selectbox("Sort By", ["Age (High-Low)", "Age (Low-High)", "Prestige", "Health"])
        
    # Apply Filters
    filtered = df.copy()
    
    if search_term:
        filtered = filtered[filtered['id'].astype(str).str.contains(search_term, case=False)]
    if role_filter != "All":
        filtered = filtered[filtered['role'] == role_filter]
    if tribe_filter != "All":
        filtered = filtered[filtered['tribe_id'] == tribe_filter]
        
    # Apply Sort
    if sort_by == "Age (High-Low)":
        filtered = filtered.sort_values('age', ascending=False)
    elif sort_by == "Age (Low-High)":
        filtered = filtered.sort_values('age', ascending=True)
    elif sort_by == "Prestige":
        if 'prestige' in filtered.columns:
            filtered = filtered.sort_values('prestige', ascending=False)
    elif sort_by == "Health":
        filtered = filtered.sort_values('hp', ascending=False)
        
    # Pagination
    total_rows = len(filtered)
    PAGE_SIZE = 20
    if total_rows > 0:
        total_pages = math.ceil(total_rows / PAGE_SIZE)
    else:
        total_pages = 1
        
    c_page, c_total = st.columns([1, 4])
    # Keep page in session state to persist between re-runs if possible, 
    # but strictly local variable ensures reset on filter change if not careful.
    # Let's use a simple number input.
    current_page = c_page.number_input("Page", min_value=1, max_value=total_pages, value=1)
    c_total.caption(f"Showing {total_rows} agents. (Page {current_page}/{total_pages})")
    
    start_idx = (current_page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    
    # Prepare Table Data
    display_cols = ['id', 'age', 'gender', 'role', 'tribe_id', 'hp', 'stamina', 'prestige', 'is_pregnant']
    safe_cols = [c for c in display_cols if c in filtered.columns]
    
    view_df = filtered.iloc[start_idx:end_idx][safe_cols].copy()
    
    # Format for display
    if 'age' in view_df.columns: view_df['age'] = view_df['age'].astype(int)
    if 'hp' in view_df.columns: view_df['hp'] = view_df['hp'].round(1)
    if 'prestige' in view_df.columns: view_df['prestige'] = view_df['prestige'].round(1)
    
    # Define options for selection
    select_options = filtered['id'].tolist()
    
    # Interactive Table with Selection
    # Interactive Table with Selection
    event = st.dataframe(
        view_df, 
        use_container_width=True, 
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="inspector_table_main"
    )
    
    # Session State for Selection (Syncs Table & Dropdown)
    if 'inspector_selected_id' not in st.session_state:
        st.session_state.inspector_selected_id = select_options[0] if select_options else None
    if 'last_table_selection' not in st.session_state:
        st.session_state.last_table_selection = None
        
    # Handle Table Click (Only if selection CHANGED)
    if event:
        new_selection = event.selection.rows
        if new_selection != st.session_state.last_table_selection:
            # User interacted with table
            st.session_state.last_table_selection = new_selection
            if new_selection:
                try:
                    row_idx = new_selection[0]
                    if 0 <= row_idx < len(view_df):
                        clicked_id = view_df.iloc[row_idx]['id']
                        st.session_state.inspector_selected_id = clicked_id
                except:
                    pass
            
    # Popup / Dropdown (Synced)
    def _update_from_dropdown():
        st.session_state.inspector_selected_id = st.session_state.insp_dd_key
        
    current_val = st.session_state.inspector_selected_id
    # Validate
    if current_val not in select_options:
        current_val = select_options[0] if select_options else None
        
    current_idx = 0
    if current_val in select_options:
        current_idx = select_options.index(current_val)

    # Helper to label the dropdown
    def _label(aid):
        r = filtered[filtered['id'] == aid]
        if not r.empty:
            r = r.iloc[0]
            return f"{r['id']} ({r['role']}, {int(r['age'])}y)"
        return str(aid)

    st.markdown("👇 **Select Agent to Verify:**")
    st.selectbox(
        "Select Agent", 
        options=select_options, 
        index=current_idx,
        format_func=_label,
        key="insp_dd_key",
        on_change=_update_from_dropdown
    )
    
    return st.session_state.inspector_selected_id

def _render_details(agent, living_df):
    """Renders the detailed inspector view for one agent."""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        _render_profile_card(agent)
        
    with col2:
        tabs = st.tabs(["📊 Overview", "👨‍👩‍👧‍👦 Relationships", "📜 History"])
        
        with tabs[0]:
            _render_overview_tab(agent)
            
        with tabs[1]:
            _render_relationships_tab(agent, living_df)
            
        with tabs[2]:
            _render_history_tab(agent['id'])

# --- REUSED COMPONENTS ---
def _render_profile_card(agent):
    """Left Column: Portrait and quick stats"""
    st.markdown("### Profile")
    
    # Determine Emoji Portrait
    gender = agent['gender']
    age = agent['age']
    emoji = "👶"
    if age > 3: emoji = "👦" if gender == 'Male' else "👧"
    if age > 18: emoji = "👨" if gender == 'Male' else "👩"
    if age > 50: emoji = "👴" if gender == 'Male' else "👵"
    
    st.markdown(f"<h1 style='text-align: center; font-size: 80px;'>{emoji}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>{agent['id']}</h3>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center;'><b>{agent['role']}</b></div>", unsafe_allow_html=True)
    st.divider()
    
    # Key Stats
    c1, c2 = st.columns(2)
    c1.metric("Age", f"{int(agent['age'])}")
    c2.metric("Prestige", f"{agent.get('prestige', 0):.1f}")
    
    # Health Bars
    hp_pct = min(1.0, max(0.0, agent['hp'] / agent.get('max_hp', 100)))
    st.write(f"Health ({int(agent['hp'])})")
    st.progress(hp_pct)
    
    stam_pct = min(1.0, max(0.0, agent['stamina'] / 100.0))
    st.write(f"Stamina ({int(agent['stamina'])})")
    st.progress(stam_pct)

def _render_overview_tab(agent):
    """Tab 1: Detailed Attributes & Inventory"""
    st.subheader("Attributes")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Tribe:** {agent.get('tribe_id', 'None')}")
        st.write(f"**Job:** {agent['job']}")
        st.write(f"**Generation:** {agent.get('generation', 1)}")
        
    with col2:
        # Traits
        st.caption("Personal Traits")
        openness = agent.get('trait_openness', 0.5)
        consc = agent.get('trait_conscientiousness', 0.5)
        neuro = agent.get('trait_neuroticism', 0.5)
        
        st.write(f"Openness: {openness:.2f}")
        st.write(f"Diligence: {consc:.2f}")
        st.write(f"Neuroticism: {neuro:.2f}")

    st.divider()
    st.subheader("Biological Status")
    
    # Nutrients
    try:
        if isinstance(agent.get('nutrients'), str):
            nutrients = ast.literal_eval(agent['nutrients'])
        else:
            nutrients = agent.get('nutrients', {})
            
        c1, c2, c3 = st.columns(3)
        c1.metric("Protein", f"{nutrients.get('protein', 0):.0f}")
        c2.metric("Carbs", f"{nutrients.get('carbs', 0):.0f}")
        c3.metric("Vitamins", f"{nutrients.get('vitamins', 0):.0f}")
    except:
        st.caption("Nutrient data unavailable")
        
    # Injuries
    try:
        injuries = ast.literal_eval(agent.get('injuries', "[]"))
        if injuries:
            st.warning(f"🤕 Injuries: {', '.join(injuries)}")
        else:
            st.success("No current injuries")
    except: pass

def _render_relationships_tab(agent, population):
    st.subheader("Family Tree")
    
    # Parents
    try:
        parents = ast.literal_eval(agent.get('parents', "[]"))
        if parents:
            st.write(f"**Parents:** {', '.join(parents)}")
        else:
            st.write("**Parents:** Unknown (Gen 1)")
    except:
        st.write("**Parents:** Error")
        
    # Children
    try:
        children = ast.literal_eval(agent.get('children', "[]"))
        if children:
            st.write(f"**Children ({len(children)}):**")
            st.caption(", ".join(children))
        else:
            st.write("**Children:** None")
    except:
        st.write("**Children:** Error")
        
    st.divider()
    st.subheader("Social Connections")
    
    if 'engine' in st.session_state:
        state = st.session_state.engine.state
        aid = agent['id']
        
        # Filter relationships where this agent is A or B
        # Since relationships are double-directional (as per simulation.py), checking id_a is enough if we trust the engine.
        # But let's check id_a to be safe and consistent with typical query patterns.
        rels = state.relationships
        if not rels.empty:
            my_rels = rels[rels['id_a'] == aid].copy()
            
            if not my_rels.empty:
                for _, r in my_rels.iterrows():
                    partner_id = r['id_b']
                    rtype = r['type']
                    affection = r.get('affection', 0.5)
                    start_day = r.get('start_day', 0)
                    duration = state.day - start_day
                    
                    with st.container():
                        c1, c2 = st.columns([1, 2])
                        c1.markdown(f"**{rtype}**")
                        c1.caption(f"{partner_id}")
                        
                        c2.write(f"Affection: {int(affection*100)}% (Duration: {duration} days)")
                        c2.progress(min(1.0, max(0.0, affection)))
                        st.divider()
            else:
                st.info("No active social relationships.")
    else:
        st.warning("Engine state not accessible for relationship details.")


def _render_history_tab(agent_id):
    st.subheader("Action History")
    
    if 'engine' in st.session_state:
        state = st.session_state.engine.state
        logs = state.get_logs_for_agent(agent_id)
        
        if logs:
            for entry in reversed(logs[-20:]): # Show last 20
                cat_icon = {
                    "General": "📝",
                    "Social": "💬",
                    "Combat": "⚔️",
                    "Health": "🏥",
                    "Economy": "💰",
                    "Crime": "🚔"
                }.get(entry.get('category', 'General'), "🔹")
                
                st.markdown(f"**Day {entry.get('tick', '?')}** {cat_icon} {entry.get('message', '')}")
        else:
            st.caption("No recent history recorded for this agent.")
    else:
        st.error("Engine state not accessible.")
