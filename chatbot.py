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

# --------------------- CONFIG / LOAD --------------------- #
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

# --------------------- SESSION STATE --------------------- #
if "page" not in st.session_state: st.session_state.page = "🏠 Home"
if "active_button" not in st.session_state: st.session_state.active_button = "🏠 Home"
if "chat_messages" not in st.session_state: st.session_state.chat_messages = []
if "gemini_history" not in st.session_state: st.session_state.gemini_history = []

# --------------------- CUSTOM STYLES --------------------- #
st.markdown("""
<style>
/* Gradient Background */
.stApp {
    background: linear-gradient(to bottom, #FFA500, #800080);
    color: white;
}

/* Sidebar gradient */
[data-testid="stSidebar"] {
    background: linear-gradient(to bottom, #FFB84D, #993399);
    color: white;
}

/* Buttons */
div.stButton > button {
    background-color: #FFB84D;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 0.6em 1em;
    font-size: 1em;
    font-weight: bold;
}
div.stButton > button:hover {
    background-color: #993399;
}

/* Chat area */
.st-chat-message-content {
    background-color: white !important;
    color: black !important;
    border-radius: 10px !important;
    padding: 0.5em !important;
}

/* Text input solid white */
textarea, input[type="text"], input[type="password"], input[type="email"], input[type="number"] {
    background-color: white !important;
    color: black !important;
}
</style>
""", unsafe_allow_html=True)

# --------------------- SIDEBAR --------------------- #
st.sidebar.title("🌴 BROAD ISLAND INTEL")
pages = ["🏠 Home", "📅 Itinerary Planner", "💬 Chatbot"]
for p in pages:
    if st.sidebar.button(p):
        st.session_state.page = p
        st.session_state.active_button = p

st.sidebar.markdown(
    f"<div style='padding:6px 8px;border-radius:6px;font-weight:bold;color:white;"
    f"background:linear-gradient(90deg,#FFA500,#800080);margin-top:8px'>"
    f"Active: {st.session_state.active_button}</div>",
    unsafe_allow_html=True
)

# --------------------- HOME PAGE --------------------- #
if st.session_state.page == "🏠 Home":
    st.markdown(
        """
        <div style='padding:30px; border-radius:15px; background: rgba(255,255,255,0.15);'>
            <h1 style='text-align:center; color:#FFFFFF;'>🌴 Welcome to BROAD ISLAND INTEL 🌴</h1>
            <p style='text-align:center; color:#FFF0C1; font-size:18px;'>
                Your Saint Lucia guide for <span style="color:#FF9A00; font-weight:bold;">Tourism</span>, 
                <span style="color:#D580FF; font-weight:bold;">Culture</span>, 
                <span style="color:#FF9A00; font-weight:bold;">Education</span>, and <span style="color:#D580FF; font-weight:bold;">Cuisine</span>!  
            </p>
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown("""
    <div style='display:flex; gap:15px; margin-top:20px; flex-wrap: wrap;'>
        <div style='flex:1; min-width:200px; padding:15px; border-radius:12px; background: rgba(255,255,255,0.15);'>
            <h3>🏖 Explore Tourism</h3>
            <p>Discover top beaches, waterfalls, and scenic spots around Saint Lucia.</p>
        </div>
        <div style='flex:1; min-width:200px; padding:15px; border-radius:12px; background: rgba(255,255,255,0.15);'>
            <h3>🎭 Dive into Culture</h3>
            <p>Learn about historical sites, traditions, and local festivals.</p>
        </div>
        <div style='flex:1; min-width:200px; padding:15px; border-radius:12px; background: rgba(255,255,255,0.15);'>
            <h3>🏫 Education</h3>
            <p>Explore museums, libraries, and educational landmarks.</p>
        </div>
        <div style='flex:1; min-width:200px; padding:15px; border-radius:12px; background: rgba(255,255,255,0.15);'>
            <h3>🍴 Local Cuisine</h3>
            <p>Find the best restaurants and authentic Saint Lucian dishes.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <p style='margin-top:25px; color:#FFF0C1; font-size:16px;'>
        Use the sidebar to navigate through pages, plan itineraries, or chat with our AI assistant for recommendations!  
        🌞 Start your Saint Lucia adventure now! 🌴
        </p>
        """, unsafe_allow_html=True
    )

    # Rotating sample Q&A
    sample_qa = [
        ("Where can I find the best beaches in Saint Lucia?", "Try Reduit Beach or Anse Chastanet for crystal clear water and soft sand!"),
        ("What is a must-see cultural landmark?", "The Derek Walcott Square in Castries is perfect for history and photo opportunities."),
        ("Any recommendations for authentic Saint Lucian food?", "Don’t miss trying the national dish, Green Fig & Saltfish, at a local restaurant!"),
        ("Where can I go hiking?", "The Tet Paul Nature Trail offers moderate hikes with stunning views of the Pitons."),
        ("Are there museums to visit?", "Yes! The National Art Gallery and the Saint Lucia Folk Research Centre are great spots."),
    ]
    idx = int(time.time() // 3) % len(sample_qa)
    question, answer = sample_qa[idx]
    st.markdown(
        f"""
        <div style='margin-top:30px; padding:20px; border-radius:15px; background: rgba(255,255,255,0.25);'>
            <h4 style='color:#FFD580;'>💡 Sample Question</h4>
            <p style='color:#FFFFFF; font-weight:bold;'>{question}</p>
            <h4 style='color:#FFD580;'>🤖 Example Response</h4>
            <p style='color:#FFF0C1;'>{answer}</p>
        </div>
        """, unsafe_allow_html=True
    )

# --------------------- ITINERARY PLANNER --------------------- #
elif st.session_state.page == "📅 Itinerary Planner":
    st.header("📅 Plan Your Itinerary")
    user_interests = st.text_input("Enter your interests (comma separated, e.g., beach, hiking, seafood, education):")
    combined_df = pd.concat([tourism_df, restaurant_df, cultural_df, edu_df], ignore_index=True)
    if user_interests:
        keywords = [k.strip().lo]()
