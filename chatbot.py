import streamlit as st
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import os
import plotly.express as px
import folium
from streamlit_folium import st_folium

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
st.sidebar.title("BROAD ISLAND INTEL")
pages = ["Home", "Itinerary Planner", "Chatbot"]
for p in pages:
    if st.sidebar.button(p):
        st.session_state.page = p
        st.session_state.active_button = p

st.sidebar.markdown(
    f"<div style='padding:6px 8px;border-radius:6px;font-weight:bold;color:white;"
    f"background:linear-gradient(90deg,#FF6B6B,#FF4B4B);margin-top:8px'>"
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
        # Sort by rating if numeric
        if "Rating" in filtered_df.columns:
            filtered_df["Rating"] = pd.to_numeric(filtered_df["Rating"], errors="coerce")
            filtered_df = filtered_df.sort_values(by="Rating", ascending=False)

        # Display itinerary entries
        for source, group in filtered_df.groupby("Source"):
            header = "Where are you heading o_o" if source=="Tourism" else \
                     "Where to eat > <" if source=="Restaurant" else \
                     "Culture trip incoming 🎭" if source=="Cultural" else "Education stops 🏫"
            st.subheader(header)
            for _, r in group.iterrows():
                st.markdown(f"**{r.get('Name','Unknown')}**  \n"
                            f"⭐ {r.get('Rating','N/A')} — {r.get('Type','N/A')}  \n"
                            f"📍 {r.get('Location','Unknown')}  \n"
                            f"💰 {r.get('Price','N/A')}")

        # ---------------------
        # Interactive map
        # ---------------------
        map_df = filtered_df.dropna(subset=["Latitude","Longitude"]).copy()
        if not map_df.empty:
            m = folium.Map(location=[13.9094,-60.9789], zoom_start=10, tiles="OpenStreetMap")
            color_map = {"Tourism":"blue","Restaurant":"red","Cultural":"green","Education":"purple"}
            for _, r in map_df.iterrows():
                folium.Marker(
                    location=[r["Latitude"], r["Longitude"]],
                    popup=f"<b>{r.get('Name','Unknown')}</b><br>"
                          f"⭐ {r.get('Rating','N/A')}<br>"
                          f"{r.get('Type','N/A')}<br>"
                          f"💰 {r.get('Price','N/A')}",
                    tooltip=r.get('Name','Unknown'),
                    icon=folium.Icon(color=color_map.get(r["Source"],"gray"))
                ).add_to(m)
            st_folium(m, width=700, height=500)

        # ---------------------
        # Save itinerary CSV
        # ---------------------
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Save Itinerary as CSV",
            data=csv_data,
            file_name="broad_itinerary.csv",
            mime="text/csv"
        )

        # ---------------------
        # AI-generated itinerary
        # ---------------------
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
