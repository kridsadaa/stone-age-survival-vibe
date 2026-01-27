import streamlit as st
import altair as alt

def render_overview(living_df):
    if len(living_df) > 0:
        st.subheader("Demographics")
        
        # Age Distribution
        chart_data = living_df[['age', 'gender']].copy()
        chart_data['age_group'] = (chart_data['age'] // 10) * 10
        
        c = alt.Chart(chart_data).mark_bar().encode(
            x='age_group:O',
            y='count()',
            color='gender'
        )
        st.altair_chart(c, use_container_width=True)
        
        # Job Distribution
        st.caption("Job Roles")
        job_counts = living_df['job'].value_counts()
        st.bar_chart(job_counts)
