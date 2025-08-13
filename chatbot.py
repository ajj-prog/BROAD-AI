import streamlit as st
import pandas as pd

import google.generativeai as genai
import plotly.express as px
import folium
from streamlit_folium import st_folium

# ---------------------
# Configure Google Generative AI
# ---------------------
# Make sure you have added SECRET_KEY in Streamlit Cloud Secrets
# Example in Secrets: SECRET_KEY="YOUR_ACTUAL_KEY_HERE"
genai.configure(api_key=st.secrets["SECRET_KEY"])

# ---------------------
# Load CSVs and clean columns
# ---------------------
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

# Fill missing columns safely
for df in [tourism_df, restaurant_df, cultural_df, edu_df]:
    for col, default in [("Latitude", 0.0), ("Longitude", 0.0), ("Rating", "N/A"), ("Type", "N/A"), ("Price", "N/A")]:
        if col not in df.columns:
            df[col] = default
        df[col] = df[col].fillna(default)
