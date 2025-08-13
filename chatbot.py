import streamlit as st
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import os
import plotly.express as px
import folium
from streamlit_folium import st_folium
import random
import time

# ---------------------
# Loader (full page)
# ---------------------
loader = st.empty()
with loader.container():
    st.markdown("""
    <div style='position:fixed; top:0; left:0; width:100%; height:100%;
                background: rgba(0,0,0,0.8); z-index:9999; display:flex;
                flex-direction: column; justify-content:center; align-items:center;'>
        <div style='font-size:60px; animation:bob 1s infinite alternate;'>🌴</div>
        <div style='color:white; margin-top:20px; font-size:24px;'>Just a minute ^^</div>
        <style>
        @keyframes bob { 0% { transform: translateY(0); } 100% { transform: translateY(-20px); } }
        </style>
    </div>
    """, unsafe_allow_html=True)
time.sleep(3)
loader.empty()

# ---------------------
# Config / Load
# ---------------------
load_dotenv()
genai.configure(api_key=os.getenv("SECRET_KEY"))

def clean_columns(df):
    df.columns = df.columns.str.strip().str.title()
    return df

tourism_df = clean_columns(pd.read_csv("tourism.csv"))
edu_df = clean_columns(pd.read_csv("edu.csv"))
cultural_df = clean_columns(pd.read_csv("cultural.csv"))
restaurant_df = clean_columns(pd.read_csv("resturant.csv"))

# Mark origins
tourism_df['Source'] = "Tourism"
restaurant_df['Source'] = "Restaurant"
cultural_df['Source'] = "Cultural"
edu_df['Source'] = "Education"

# Fill missing columns and data safely
for df in [tourism_df, restaurant_df, cultural_df, edu_df]:
    for col, default in [("Latitude", 0.0), ("Longitude", 0.0), ("Rating", "N/A"), ("Type", "N/A"), ("Price", "N/A")]:
        if col not in df.columns:
            df[col] = default
        df[col] = df[col].fillna(default)

# --
