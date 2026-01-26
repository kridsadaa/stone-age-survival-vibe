import streamlit as st
import pandas as pd
from src.simulation import World
import time

st.set_page_config(page_title="Stone Age Survival", layout="wide")

st.title("🗿 Stone Age Survival Simulation")

# Initialize Session State
if 'world' not in st.session_state:
    st.session_state.world = World()
    st.session_state.auto_play = False

def advance_day():
    st.session_state.world.tick()

# Sidebar Controls
with st.sidebar:
    st.header("Controls")
    if st.button("Advance 1 Day"):
        advance_day()
    
    # Auto-play logic is tricky in Streamlit without reruns. 
    # We can use a simple toggle to "simulate X days" instantly or just manual steps.
    # For a true "Animation", we'd typically use st.empty() loop.
    
    days_to_sim = st.number_input("Fast Forward Days", min_value=1, max_value=1000000, value=1)
    if st.button("Simulate Batch"):
        progress_bar = st.progress(0)
        status = st.empty()
        start_t = time.time()
        
        # UI updates are slow. Update every 10% of the total days as requested
        update_step = max(1, int(days_to_sim * 0.1))
        
        for i in range(days_to_sim):
            st.session_state.world.tick()
            
            if (i + 1) % update_step == 0 or (i + 1) == days_to_sim:
                progress_bar.progress((i + 1) / days_to_sim)
                status.caption(f"Simulating Day {st.session_state.world.day}... ({(i+1)/days_to_sim:.0%})")
                
        elapsed = time.time() - start_t
        st.success(f"Simulated {days_to_sim} days in {elapsed:.2f}s ({days_to_sim/elapsed:.1f} days/sec).")

    st.markdown("### Debug Stats")
    st.write(f"Total Resources: {st.session_state.world.resources}")
    
    if st.button("🔄 Reset Simulation"):
        st.session_state.world = World()
        st.rerun()

    st.markdown("---")
    st.markdown("### 🧠 Tribal Intelligence (AI)")
    
    # Check if AI exists (backward compatibility)
    if hasattr(st.session_state.world, 'ai'):
        ai_action = st.session_state.world.ai_action
        policies = ["Gathering Priority", "Balanced", "Healing Priority"]
        
        st.info(f"**Current Policy**: {policies[ai_action]}")
        
        # Brain Details
        with st.expander("AI Brain (Q-Values)"):
            world = st.session_state.world
            # Reconstruct current state key for visualization
            living_p = [p for p in world.population if p.is_alive]
            current_state = world.ai.get_state_key(
                world.current_season, world.resources, 
                len(living_p), 
                sum(1 for p in living_p if p.infected_diseases)
            )
            
            if current_state in world.ai.q_table:
                q_vals = world.ai.q_table[current_state]
                st.write(f"**State**: {current_state}")
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Gather", f"{q_vals[0]:.2f}")
                col_b.metric("Balance", f"{q_vals[1]:.2f}")
                col_c.metric("Heal", f"{q_vals[2]:.2f}")
            else:
                st.write(f"**State**: {current_state}")
                st.write("New State (Exploring)")
    else:
        st.warning("AI not initialized. Please reset simulation.")

# Main Dashboard
world = st.session_state.world
living_pop = [p for p in world.population if p.is_alive]
dead_pop = [p for p in world.population if not p.is_alive]

healers = sum(1 for p in living_pop if p.job == "Healer")
gatherers = sum(1 for p in living_pop if p.job == "Gatherer")

# Season Logic
season_emojis = {"Spring": "🌸", "Summer": "☀️", "Autumn": "🍂", "Winter": "❄️"}
current_season = world.current_season
season_display = f"{season_emojis[current_season]} {current_season}"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Day & Season", f"Day {world.day}", delta=season_display)
col2.metric("Population", len(living_pop), delta=f"{len(living_pop) - 50} from start" if world.day > 0 else 0)
col3.metric("Food Storage", int(world.resources), delta="Stockpile")
col4.metric("Infected", sum(1 for p in living_pop if p.infected_diseases))

# Job Stats
st.caption(f"**Roles**: 🏹 Gatherers: {gatherers} | 💊 Healers: {healers} (Recovery Bonus: +{healers * 5}%)")

# Detailed Views
tab1, tab2, tab3 = st.tabs(["Village Status", "The Chronicle", "Data Export"])

with tab1:
    st.subheader("Population Demographics")
    if living_pop:
        # Pagination Controls
        col_p1, col_p2 = st.columns([1, 4])
        page_size = 50
        total_pages = max(1, (len(living_pop) + page_size - 1) // page_size)
        
        with col_p1:
            page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
            
        # Slice Data
        start_idx = (page_number - 1) * page_size
        end_idx = min(start_idx + page_size, len(living_pop))
        page_pop = living_pop[start_idx:end_idx]
        
        st.caption(f"Showing {start_idx+1}-{end_idx} of {len(living_pop)} villagers")

        # Create DataFrame for display (Only for current page)
        data = []
        for p in page_pop:
            data.append({
                "ID": p.id,
                "Family ID": p.family_id,
                "Age": f"{p.age:.1f}", # Show decimal age
                "Gender": p.gender,
                "Job": p.job,
                "HP": int(p.current_hp),
                "Stamina": int(p.stamina),
                "Traits": ", ".join([t['name'] for t in p.traits]),
                "Infection": ", ".join(p.infected_diseases),
                "Personality": f"O:{p.personality['Openness']:.1f} C:{p.personality['Conscientiousness']:.1f}" # Brief
            })
        df = pd.DataFrame(data)
        
        # Enable Selection
        event = st.dataframe(
            df, 
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        selected_person_id = None
        if len(event.selection.rows) > 0:
            selected_row_idx = event.selection.rows[0]
            selected_person_id = df.iloc[selected_row_idx]["ID"]
        
        # Charts
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.caption("Age Distribution")
            st.bar_chart(df['Age'].astype(float).astype(int).value_counts())
            
        with col_c2:
            st.caption("Average Tribe Personality (OCEAN)")
            # Calculate avg personality
            avg_traits = {"Openness": 0, "Conscientiousness": 0, "Extraversion": 0, "Agreeableness": 0, "Neuroticism": 0}
            if living_pop:
                for p in living_pop:
                    for k in avg_traits:
                        avg_traits[k] += p.personality.get(k, 0.5)
                for k in avg_traits:
                    avg_traits[k] /= len(living_pop)
            
            st.bar_chart(pd.Series(avg_traits))

    st.divider()
    st.subheader("🔍 Agent Inspector")
    if living_pop:
        # Prepare lists
        agent_ids = [p.id for p in living_pop]
        agent_labels = [f"{p.id} ({p.gender}, Age {int(p.age)})" for p in living_pop]
        id_map = {p.id: p for p in living_pop}
        
        # Determine selection index
        default_index = 0
        if selected_person_id and selected_person_id in agent_ids:
             default_index = agent_ids.index(selected_person_id)
        
        selected_label = st.selectbox(
            "Select Villager (or click row in table above)", 
            options=agent_labels,
            index=default_index
        )
        
        if selected_label:
            p_id = selected_label.split(" ")[0]
            person = id_map.get(p_id)
            
            p_col1, p_col2, p_col3 = st.columns(3)
            
            with p_col1:
                st.markdown(f"**ID:** `{person.id}`")
                st.markdown(f"**Age:** {person.age:.1f}")
                st.markdown(f"**Gender:** {person.gender}")
                st.markdown(f"**Job:** {person.job}")
                st.markdown(f"**Family:** `{person.family_id}`")
                
            with p_col2:
                st.metric("HP", f"{person.current_hp:.0f}/100")
                st.metric("Stamina", f"{person.stamina:.0f}/100")
                if person.is_pregnant:
                    st.warning(f"Pregnant ({person.pregnancy_days} days)")
            
            with p_col3:
                st.caption("Personality (OCEAN)")
                st.bar_chart(person.personality)
                
            st.markdown("**Traits:**")
            if person.traits:
                for t in person.traits:
                     st.code(f"{t['name']}: {t['bonus']}")
            else:
                st.write("-")
                
            st.markdown("**Health Status:**")
            if person.infected_diseases:
                for d_id, progress in person.infected_diseases.items():
                    d_name = next((d['name'] for d in world.diseases if d['id'] == d_id), d_id)
                    st.error(f"Infected with {d_name} (Recovery: {progress:.0f}%)")
            
            if person.immunities:
                 st.success(f"Immune to: {', '.join(person.immunities)}")
            
            # Family Tree Visualization
            st.markdown("### 🌳 Family Tree")
            with st.expander("View Lineage"):
                try:
                    import graphviz
                    graph = graphviz.Digraph()
                    graph.attr(rankdir='TB')
                    
                    # Central Node (The Agent)
                    label = f"{person.id}\n({person.gender})"
                    graph.node('ME', label, shape='box', style='filled', color='lightblue')
                    
                    # Parents
                    if person.parents:
                        for i, parent_obj in enumerate(person.parents):
                             p_label = f"{parent_obj.id}\n({parent_obj.gender})"
                             p_node_id = f"P{i}"
                             # Check if parent is alive to style
                             if not parent_obj.is_alive:
                                 p_label += "\n(Deceased)"
                                 graph.node(p_node_id, p_label, style='dashed')
                             else:
                                 graph.node(p_node_id, p_label)
                             
                             graph.edge(p_node_id, 'ME', label='Parent')
                    
                    # Children
                    children = [k for k in world.population if person in k.parents]
                    
                    if children:
                        for i, child in enumerate(children):
                            c_label = f"{child.id}\n({child.gender})"
                            c_node_id = f"C{i}"
                            if not child.is_alive:
                                c_label += "\n(Deceased)"
                                c_node_id = f"C{i}_dead" # Unique ID for dead nodes if needed, strictly not necessary but safe
                                graph.node(c_node_id, c_label, style='dashed')
                            else:
                                 graph.node(c_node_id, c_label)
                            
                            graph.edge('ME', c_node_id, label='Child')
                    
                    st.graphviz_chart(graph)
                except ImportError:
                    st.warning("⚠️ **Graphviz Library not found.**")
                    st.info("To view Family Trees, you need to install Graphviz:\n1. Install Python package: `pip install graphviz`\n2. Install System Binary: https://graphviz.org/download/")
                except Exception as e:
                    st.error(f"Error rendering graph: {e}")
                    st.info("Make sure Graphviz executables are in your system PATH.")
                
    else:
        st.write("No villagers alive.")

with tab2:
    st.subheader("Event Log")
    for log in world.chronicle:
        if "died" in log:
            st.error(log)
        elif "born" in log:
            st.success(log)
        elif "OUTBREAK" in log:
            st.warning(log)
        else:
            st.text(log)

with tab3:
    st.subheader("Export Data")
    if st.button("Generate CSV Snapshot"):
        # Full export including dead
        all_data = []
        for p in world.population:
            all_data.append({
                "ID": p.id,
                "Status": "Alive" if p.is_alive else "Dead",
                "Cause of Death": p.cause_of_death,
                "Age": p.age,
                "Gender": p.gender,
                "HP": p.current_hp,
                "Traits": [t['name'] for t in p.traits]
            })
        export_df = pd.DataFrame(all_data)
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Population CSV",
            data=csv,
            file_name=f"stone_age_pop_day_{world.day}.csv",
            mime="text/csv",
        )
