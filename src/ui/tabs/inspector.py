import streamlit as st

def render_inspector(living_df):
    st.subheader("Population DataFrame")
    st.dataframe(living_df.head(100)) # Show top 100 only
