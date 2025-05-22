import streamlit as st
import streamlit.components.v1 as components

# Set page config to use full width
st.set_page_config(layout="wide")

# Custom CSS for grid lines
st.markdown("""
    <style>
    .grid-container {
        display: grid;
        grid-template-columns: 2fr 1fr;
        grid-template-rows: 1fr 5fr 3fr;
        gap: 10px;
        background-color: #1a2b3c;
        padding: 10px;
        height: 100vh;
    }
    .grid-item {
        background-color: #2c3e50;
        padding: 15px;
        text-align: center;
        color: #ecf0f1;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# Create the grid container
st.markdown("""
    <div class="grid-container">
        <div class="grid-item">Row 1, Col 1</div>
        <div class="grid-item">Row 1, Col 2</div>
        <div class="grid-item">Row 2, Col 1</div>
        <div class="grid-item">Row 2, Col 2</div>
        <div class="grid-item">Row 3, Col 1</div>
        <div class="grid-item">Row 3, Col 2</div>
    </div>
    """, unsafe_allow_html=True)
