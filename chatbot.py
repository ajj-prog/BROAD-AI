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
                st.markdown(f"**{r.get('Name','Unknown')}**  \n"
                            f"⭐ {r.get('Rating','N/A')} — {r.get('Type','N/A')}  \n"
                            f"📍 {r.get('Location','Unknown')}  \n"
                            f"💰 {r.get('Price','N/A')}")

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

        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Save Itinerary as CSV",
            data=csv_data,
            file_name="broad_itinerary.csv",
            mime="text/csv"
        )

        if st.button("Generate AI itinerary"):
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
                places_text = filtered_df.to_string(index=False)
                prompt = f"""
Create a 1-day itinerary for Saint Lucia based on these interests: {user_interests}.
Use only the following places (highest rated first if rating available):
{places_text}
Format the itinerary in morning, afternoon, evening blocks with short, engaging descriptions.
Do not include greetings or sign-offs.
"""
                res = model.generate_content(prompt)
                st.subheader("Your Suggested Itinerary")
                st.write(res.text)
            except Exception as e:
                st.error(f"AI error: {e}")

# --------------------- CHATBOT --------------------- #
elif st.session_state.page == "💬 Chatbot":

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
