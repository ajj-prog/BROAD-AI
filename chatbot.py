import streamlit as st
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import os
import plotly.express as px
import folium
from streamlit_folium import st_folium

# ---------------------
# Page & Chat Styling
# ---------------------
st.markdown(
    """
    <style>
    /* Full-page vertical gradient background */
    body, .stApp, .main {
        background: linear-gradient(to bottom, #FF9A00, #8E2DE2);
        background-attachment: fixed;
        color: #FFFFFF;
    }

    /* Sidebar gradient matching page */
    [data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #FF9A00, #8E2DE2);
        color: white;
        padding: 10px;
    }

    /* Styled sidebar buttons with emojis */
    .sidebar-button {
        display: block;
        width: 100%;
        margin-bottom: 10px;
        padding: 8px;
        border-radius: 8px;
        font-weight: bold;
        background: linear-gradient(to right, #FF9A00, #8E2DE2);
        color: white;
        text-align: center;
        cursor: pointer;
    }

    /* Highlight boxes for Itinerary Planner entries */
    .highlight {
        background-color: rgba(255, 255, 255, 0.15);
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }

    /* Page overview boxes */
    .page-overview {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 12px;
        border-radius: 8px;
        margin-top: 20px;
        font-style: italic;
        color: #FFFFFF;
    }

    /* Chat area styling */
    .stChatMessage.user {
        background-color: rgba(255, 165, 0, 0.4) !important;  /* semi-transparent orange */
        color: #FFFFFF !important;
        border-radius: 10px;
        padding: 8px;
    }
    .stChatMessage.assistant {
        background-color: rgba(142, 45, 226, 0.4) !important; /* semi-transparent purple */
        color: #FFFFFF !important;
        border-radius: 10px;
        padding: 8px;
    }

    /* Chat input box styling */
    div[data-testid="stChatInput"] textarea {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: #FFFFFF !important;
        border-radius: 8px;
        padding: 8px;
    }

    div[data-testid="stChatInput"] button {
        background: linear-gradient(to right, #FF9A00, #8E2DE2) !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        padding: 8px 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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

tourism_df['Source'] = "Tourism"
restaurant_df['Source'] = "Restaurant"
cultural_df['Source'] = "Cultural"
edu_df['Source'] = "Education"

for df in [tourism_df, restaurant_df, cultural_df, edu_df]:
    for col, default in [("Latitude", 0.0), ("Longitude", 0.0), ("Rating", "N/A"), ("Type", "N/A"), ("Price", "N/A")]:
        if col not in df.columns:
            df[col] = default
        df[col] = df[col].fillna(default)

# ---------------------
# Session state defaults
# ---------------------
if "page" not in st.session_state: st.session_state.page = "Home"
if "active_button" not in st.session_state: st.session_state.active_button = "Home"
if "chat_messages" not in st.session_state: st.session_state.chat_messages = []
if "gemini_history" not in st.session_state: st.session_state.gemini_history = []

# ---------------------
# Sidebar
# ---------------------
st.sidebar.title("🌴 BROAD ISLAND INTEL")
pages = ["Home", "Itinerary Planner", "Chatbot"]
buttons = ["🏠 Home", "📅 Itinerary Planner", "💬 Chatbot"]
for btn, p in zip(buttons, pages):
    if st.sidebar.button(btn):
        st.session_state.page = p
        st.session_state.active_button = p

st.sidebar.markdown(
    f"<div style='padding:6px 8px;border-radius:6px;font-weight:bold;color:white;"
    f"background:linear-gradient(90deg,#FF9A00,#8E2DE2);margin-top:8px'>"
    f"Active: {st.session_state.active_button}</div>",
    unsafe_allow_html=True
)

# ---------------------
# Page: Home
# ---------------------
if st.session_state.page == "Home":
    st.title("🌴 BROAD ISLAND INTEL")
    st.markdown("""
    Welcome! BROAD ISLAND INTEL is your Saint Lucia cultural, tourism, and education guide.  
    - Explore top tourist sites, cultural landmarks, and restaurants.  
    - Plan your personalized itinerary.  
    - Chat with the AI assistant for quick recommendations.
    """)
    st.markdown("""
    <div class='page-overview'>
    <b>Home:</b> Get an overview of Saint Lucia’s highlights and access other pages.  
    <b>Itinerary Planner:</b> Enter your interests to create a personalized itinerary with maps and CSV download.  
    <b>Chatbot:</b> Ask BROAD questions about Saint Lucia and get AI-generated suggestions.
    </div>
    """, unsafe_allow_html=True)

# ---------------------
# Page: Itinerary Planner
# ---------------------
elif st.session_state.page == "Itinerary Planner":
    st.header("📅 Plan Your Itinerary")
    user_interests = st.text_input("Enter your interests (comma separated, e.g., beach, hiking, seafood, education):")
    combined_df = pd.concat([tourism_df, restaurant_df, cultural_df, edu_df], ignore_index=True)

    if user_interests:
        keywords = [k.strip().lower() for k in user_interests.split(",")]
        mask = combined_df.apply(lambda row: any(kw in str(row).lower() for kw in keywords), axis=1)
        filtered_df = combined_df[mask]
    else:
        filtered_df = combined_df.copy()

    if filtered_df.empty:
        st.warning("No matches found. Try different interests.")
    else:
        if "Rating" in filtered_df.columns:
            filtered_df["Rating"] = pd.to_numeric(filtered_df["Rating"], errors="coerce")
            filtered_df = filtered_df.sort_values(by="Rating", ascending=False)

        for source, group in filtered_df.groupby("Source"):
            header = "Where are you heading o_o" if source=="Tourism" else \
                     "Where to eat > <" if source=="Restaurant" else \
                     "Culture trip incoming 🎭" if source=="Cultural" else "Education stops 🏫"
            st.subheader(header)
            for _, r in group.iterrows():
                st.markdown(f"<div class='highlight'>"
                            f"**{r.get('Name','Unknown')}**  <br>"
                            f"⭐ {r.get('Rating','N/A')} — {r.get('Type','N/A')}  <br>"
                            f"📍 {r.get('Location','Unknown')}  <br>"
                            f"💰 {r.get('Price','N/A')}"
                            f"</div>", unsafe_allow_html=True)

        map_df = filtered_df.dropna(subset=["Latitude","Longitude"]).copy()
        if not map_df.empty:
            m = folium.Map(location=[13.9094,-60.9789], zoom_start=10, tiles="OpenStreetMap")
            color_map = {"Tourism":"blue","Restaurant":"red","Cultural":"green","Education":"purple"}
            for _, r in map_df.iterrows():
                folium.Marker(
                    location=[r["Latitude"], r["Longitude"]],
                    popup=f"<b>{r.get('Name','Unknown')}</b><br>⭐ {r.get('Rating','N/A')}<br>{r.get('Type','N/A')}<br>💰 {r.get('Price','N/A')}",
                    tooltip=r.get('Name','Unknown'),
                    icon=folium.Icon(color=color_map.get(r["Source"],"gray"))
                ).add_to(m)
            st_folium(m, width=700, height=500)

        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Save Itinerary as CSV", csv_data, "broad_itinerary.csv", "text/csv")

        if st.button("Generate AI itinerary"):
            model = genai.GenerativeModel("gemini-2.0-flash")
            places_text = filtered_df.to_string(index=False)
            prompt = f"""
Create a 1-day itinerary for Saint Lucia based on these interests: {user_interests}.
Use only the following places (highest rated first if rating available):
{places_text}
Format the itinerary in morning, afternoon, evening blocks with short, engaging descriptions.
Do not include greetings or sign-offs.
"""
            try:
                res = model.generate_content(prompt)
                st.subheader("Your Suggested Itinerary")
                st.write(res.text)
            except Exception as e:
                st.error(f"AI error: {e}")

# ---------------------
# Page: Chatbot
# ---------------------
elif st.session_state.page == "Chatbot":
    st.header("💬 Chat with BROAD")
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask me about Saint Lucia..."):
        st.session_state.chat_messages.append({"role":"user","content":user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.spinner("Thinking..."):
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
                chat = model.start_chat(history=st.session_state.gemini_history)
                reply = chat.send_message(user_input).text
                st.session_state.gemini_history.append({"role":"user","parts":[user_input]})
                st.session_state.gemini_history.append({"role":"model","parts":[reply]})
            except Exception as e:
                reply = f"⚠️ Error: {e}"
        st.session_state.chat_messages.append({"role":"assistant","content":reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
