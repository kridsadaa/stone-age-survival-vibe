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
        
        # Enhanced Display
        if not recent.empty:
            # Create quick lookups
            # Use single set_index to avoid multiple passes if dataframe is large
            pop_idx = state.population.set_index('id')
            pop_gender = pop_idx['gender'].to_dict()
            # Handle case where tribe_id might be missing in older saves
            if 'tribe_id' in pop_idx.columns:
                pop_tribe = pop_idx['tribe_id'].to_dict()
            else:
                pop_tribe = {}
            
            def get_tribe_icon(tid):
                s = str(tid)
                if 'Red' in s: return "🔴"
                if 'Blue' in s: return "🔵"
                if 'Green' in s: return "🟢"
                return "🏳️"

            disp_rows = []
            for _, row in recent.iterrows():
                id_a, id_b = row['id_a'], row['id_b']
                
                ga = pop_gender.get(id_a, '?')
                gb = pop_gender.get(id_b, '?')
                ta = pop_tribe.get(id_a, 'Unknown')
                tb = pop_tribe.get(id_b, 'Unknown')
                
                ia = "👨" if ga == 'Male' else ("👩" if ga == 'Female' else "👤")
                ib = "👨" if gb == 'Male' else ("👩" if gb == 'Female' else "👤")
                
                ita = get_tribe_icon(ta)
                itb = get_tribe_icon(tb)
                
                # Pair Label
                is_gay = (ga == gb) and ga != '?'
                is_cross = (ta != tb) and ta != 'Unknown' and tb != 'Unknown'
                
                status_tags = []
                if is_gay: status_tags.append("LGBTQ+ 🏳️‍🌈")
                if is_cross: status_tags.append("Cross-Tribe 🤝")
                if not status_tags: status_tags.append("Common 👫")
                
                status_str = " ".join(status_tags)
                
                disp_rows.append({
                    "Couple": f"{ita}{ia} {id_a[-4:]} + {itb}{ib} {id_b[-4:]}",
                    "Type": row['type'],
                    "Status": status_str,
                    "Since": f"Day {row['start_day']}"
                })
                
            st.dataframe(disp_rows, use_container_width=True)
        else:
            st.write("No romances yet.")
        
        # Family Sizes (Children count per mother)
        # We can aggregate from population 'mother_id'
        if 'mother_id' in living_df.columns:
            kids_count = living_df['mother_id'].value_counts()
            
            # Only show if counts exist
            if not kids_count.empty:
                st.markdown("#### Top Mothers (Most Children)")
                st.bar_chart(kids_count.head(20))
    
    st.divider()
    st.subheader("🗣️ The Rumor Mill (Gossip & Opinions)")
    
    import pandas as pd # Ensure pandas is available
    
    if hasattr(state, 'opinions') and state.opinions:
        # Convert to DF
        op_list = [{"Observer": k[0], "Target": k[1], "Score": v} for k, v in state.opinions.items()]
        op_df = pd.DataFrame(op_list)
        
        if not op_df.empty:
            c1, c2 = st.columns(2)
            
            # 1. Most Famous (Mentioned mostly)
            fame = op_df['Target'].value_counts().head(5)
            with c1:
                st.markdown("#### 🌟 Most Talked About")
                for tid, count in fame.items():
                    # Get Avg Score
                    avg = op_df[op_df['Target'] == tid]['Score'].mean()
                    emoji = "😍" if avg > 20 else ("😡" if avg < -20 else "😐")
                    st.write(f"**{tid}**: {count} mentions ({emoji} {avg:.1f})")

            # 2. Strongest Opinions (Love/Hate)
            with c2:
                st.markdown("#### 💬 Hot Takes")
                # Sample 5 strong opinions
                strong = op_df[op_df['Score'].abs() > 30]
                if not strong.empty:
                    sample = strong.sample(min(5, len(strong)))
                    for _, row in sample.iterrows():
                        obs = row['Observer']
                        tgt = row['Target']
                        sc = row['Score']
                        desc = "Worships" if sc > 50 else ("Loathes" if sc < -50 else "Likes/Dislikes")
                        st.caption(f"**{obs}** {desc} **{tgt}** ({sc:.0f})")
                else:
                    st.write("Opinions are mild.")
                    
            # 3. Network View (Optional Table)
            with st.expander("See All Opinions"):
                 st.dataframe(op_df, use_container_width=True)
        else:
            st.write("No gossip yet.")
    else:
        st.info("The air is quiet. No rumors yet.")
