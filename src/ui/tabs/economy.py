import streamlit as st
import altair as alt
import pandas as pd

def render_economy(state, living_df):
    st.subheader("💰 Advanced Economy (Inventory & Resources)")
    
    # Global Resources (Realism Phase 5 - Dictionary)
    res = state.globals.get('resources', {})
    if isinstance(res, dict):
        # New Phase 5 Format
        c1, c2, c3 = st.columns(3)
        c1.metric("Wood Stockpile", f"{res.get('wood', 0):.0f}")
        c2.metric("Stone Stockpile", f"{res.get('stone', 0):.0f}")
        c3.metric("Food Stockpile", f"{res.get('food', 0):.0f}")
    else:
        # Legacy
        st.metric("Global Stockpile (Legacy)", f"{res:.0f}", delta="Communal Food")
    
    st.markdown("---")
    
    # Inventory Analysis
    if hasattr(state, 'inventory') and not state.inventory.empty:
        inv = state.inventory
        
        # 1. Total Resource Counts
        # Group by item, sum amount
        total_items = inv.groupby('item')['amount'].sum().reset_index()
        total_items.columns = ['Item', 'Total Amount']
        
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.markdown("### 📊 Resource Distribution")
            base = alt.Chart(total_items).encode(
                theta=alt.Theta("Total Amount", stack=True)
            )
            pie = base.mark_arc(outerRadius=120).encode(
                color=alt.Color("Item"),
                tooltip=["Item", "Total Amount"]
            )
            st.altair_chart(pie, use_container_width=True)
            
        with c2:
            st.markdown("### 📦 Stockpile")
            st.dataframe(total_items, hide_index=True)
            
        st.markdown("---")
        
        # 2. Spoilage Watch
        # Filter spoiling items
        spoiling = inv[inv['spoilage_rate'] > 0]
        if not spoiling.empty:
            avg_spoil = spoiling.groupby('item')['spoilage_rate'].mean()
            st.warning(f"⚠️ **Spoilage Rates (per day):**\n" + ", ".join([f"{k}: {v:.2f}" for k,v in avg_spoil.items()]))
            
        st.markdown("---")
        
        # 3. Tools & Technology Analysis
        # Count Tools
        tools_df = inv[inv['item'].isin(['Spear', 'Basket'])]
        
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("### 🛠️ Tools in Circulation")
            if not tools_df.empty:
                tool_counts = tools_df.groupby('item').size().reset_index(name='Count')
                
                bars = alt.Chart(tool_counts).mark_bar().encode(
                    x='item',
                    y='Count',
                    color='item',
                    tooltip=['item', 'Count']
                )
                st.altair_chart(bars, use_container_width=True)
                
                # Avg Durability
                avg_dur = tools_df.groupby('item')['durability'].mean()
                st.info(f"❤️ **Avg Durability:** " + ", ".join([f"{k}: {v:.1f}" for k,v in avg_dur.items()]))
            else:
                st.caption("No tools crafted yet.")
                
        with c4:
            #  st.markdown("### 🏆 Top Hoarders")
             # Reuse rich list logic below
             pass 

        # 4. Top Hoarders
        # Group by agent, count items
        rich_list = inv.groupby('agent_id')['amount'].sum().sort_values(ascending=False).head(10)
        
        st.markdown("### 🏆 Top Hoarders")
        # Merge with names/jobs?
        # living_df has details
        rich_df = rich_list.reset_index()
        rich_df.columns = ['id', 'Total Wealth']
        
        # Merge
        merged = rich_df.merge(living_df[['id', 'job', 'age', 'tribe_id']], on='id', how='left')
        st.dataframe(merged)
        
    else:
        st.info("Inventory is empty. Wait for gathering cycle...")
