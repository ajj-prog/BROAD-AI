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

# =========================
# Config / Load
# =========================
load_dotenv()
genai.configure(api_key=os.getenv("SECRET_KEY"))

def clean_columns(df):
    df.columns = df.columns.str.strip().str.title()
    return df

tourism_df = clean_columns(pd.read_csv("tourism.csv"))
edu_df = clean_columns(pd.read_csv("edu.csv"))
cultural_df = clean_columns(pd.read_csv("cultural.csv"))
restaurant_df = clean_columns(pd.read_csv("resturant.csv"))  # (kept filename as-is)

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

# =========================
# Session state defaults
# =========================
if "page" not in st.session_state: st.session_state.page = "🏠 Home"
if "active_button" not in st.session_state: st.session_state.active_button = "🏠 Home"
if "chat_messages" not in st.session_state: st.session_state.chat_messages = []
if "gemini_history" not in st.session_state: st.session_state.gemini_history = []
if "show_loader" not in st.session_state: st.session_state.show_loader = True
if "qa_index" not in st.session_state: st.session_state.qa_index = 0
if "qa_cycle_enabled" not in st.session_state: st.session_state.qa_cycle_enabled = False

# =========================
# Full-page loading screen (covers entire UI)
# =========================
if st.session_state.show_loader:
    loading_screen = """
    <style>
    #loading-container {
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        background: linear-gradient(to bottom, #FF8C00, #7B1FA2);
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-20px); }
    }
    .bounce {
        display: inline-block;
        animation: bounce 1s infinite;
        font-size: 3em;
    }
    </style>

    <style id="hide-ui">header, footer, .stSidebar {display: none !important;}</style>
    <div id="loading-container">
        <h1 style="font-size:3em; text-align:center;">🌴 BROAD ISLAND INTEL 🌴</h1>
        <div style="margin: 20px;">
            <span class="bounce">⏳</span>
        </div>
        <p style="font-size:1.5em;">Just a minute ^^</p>
    </div>
    """
    st.markdown(loading_screen, unsafe_allow_html=True)
    # Simulate load (or replace with real preload work)
    time.sleep(2.5)
    # Remove loader and reveal UI
    st.session_state.show_loader = False
    st.markdown("""
    <script>
      const loader = document.getElementById('loading-container');
      if (loader) loader.style.display = 'none';
      const hideUI = document.getElementById('hide-ui');
      if (hideUI) hideUI.remove();
    </script>
    """, unsafe_allow_html=True)

# =========================
# Global styling (gradient + controls + chat)
# =========================
st.markdown("""
<style>
/* App & Sidebar background gradients (orange -> purple, top->bottom) */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to bottom, #FF8C00 0%, #8E24AA 45%, #6A1B9A 100%);
    color: #FFFFFF;
}
[data-testid="stSidebar"] {
    background: linear-gradient(to bottom, #FF8C00 0%, #8E24AA 100%);
}

/* Buttons (match brand colors) */
.stButton>button, .stDownloadButton>button {
    background: linear-gradient(90deg, #FF8C00, #8E24AA);
    color: #FFFFFF;
    font-weight: 700;
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1rem;
    box-shadow: 0 6px 14px rgba(0,0,0,0.15);
}
.stButton>button:hover, .stDownloadButton>button:hover {
    background: linear-gradient(90deg, #FFA733, #9C27B0);
}

/* Inputs not transparent */
[data-testid="stTextInputRoot"] input,
textarea, select {
    background: rgba(255,255,255,0.95) !important;
    color: #000 !important;
    border-radius: 10px !important;
}
.stTextInput>div>div>input {
    background: rgba(255,255,255,0.95) !important;
    color: #000 !important;
}

/* Chat message bubbles */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.9);
    color: #000;
    border-radius: 12px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
}
.st-chat-message-content {
    background: rgba(255,255,255,0.9) !important;
    color: #000 !important;
    border-radius: 12px !important;
}

/* Friendly cards */
.broad-card {
    background: rgba(255,255,255,0.14);
    border-radius: 14px;
    padding: 16px;
    box-shadow: 0 8px 18px rgba(0,0,0,0.12);
}

/* Sidebar "Active" pill */
.sidebar-active {
    padding:6px 8px; border-radius:10px; font-weight:bold; color:white;
    background: linear-gradient(90deg,#FF8C00,#8E24AA); margin-top:8px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# Sidebar Navigation
# =========================
st.sidebar.title("🌴 BROAD ISLAND INTEL")
pages = ["🏠 Home", "📅 Itinerary Planner", "💬 Chatbot"]
for p in pages:
    if st.sidebar.button(p):
        st.session_state.page = p
        st.session_state.active_button = p

st.sidebar.markdown(
    f"<div class='sidebar-active'>Active: {st.session_state.active_button}</div>",
    unsafe_allow_html=True
)

# =========================
# Page: Home
# =========================
if st.session_state.page == "🏠 Home":
    st.markdown(
        """
        <div class='broad-card' style='padding:30px;'>
            <h1 style='text-align:center; color:#FFFFFF;'>🌴 Welcome to BROAD ISLAND INTEL 🌴</h1>
            <p style='text-align:center; color:#FFF0C1; font-size:18px;'>
                Your Saint Lucia guide for <span style="color:#FFD24C; font-weight:bold;">Tourism</span>, 
                <span style="color:#E1B0FF; font-weight:bold;">Culture</span>, 
                <span style="color:#FFD24C; font-weight:bold;">Education</span>, and <span style="color:#E1B0FF; font-weight:bold;">Cuisine</span>!  
            </p>
        </div>
        """, unsafe_allow_html=True
    )

    # Four friendly category cards
    st.markdown("""
    <div style='display:flex; gap:16px; margin-top:20px; flex-wrap:wrap;'>
        <div class='broad-card' style='flex:1; min-width:220px;'>
            <h3>🏖 Explore Tourism</h3>
            <p>Discover top beaches, waterfalls, and scenic spots around Saint Lucia.</p>
        </div>
        <div class='broad-card' style='flex:1; min-width:220px;'>
            <h3>🎭 Dive into Culture</h3>
            <p>Learn about historical sites, traditions, and local festivals.</p>
        </div>
        <div class='broad-card' style='flex:1; min-width:220px;'>
            <h3>🏫 Education</h3>
            <p>Explore museums, libraries, and educational landmarks.</p>
        </div>
        <div class='broad-card' style='flex:1; min-width:220px;'>
            <h3>🍴 Local Cuisine</h3>
            <p>Find the best restaurants and authentic Saint Lucian dishes.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <p style='margin-top:25px; color:#FFF7DA; font-size:16px;'>
        Use the sidebar to explore pages, plan itineraries, or chat with our AI assistant for quick recommendations.  
        🌞 Start your Saint Lucia adventure now! 🌴
        </p>
        """, unsafe_allow_html=True
    )

    # ---------- Rotating sample Q&A (cycles) ----------
    sample_qa = [
        ("Where can I find the best beaches in Saint Lucia?",
         "Try Reduit Beach or Anse Chastanet for crystal-clear water and soft sand!"),
        ("What is a must-see cultural landmark?",
         "Derek Walcott Square in Castries is perfect for history and photo opportunities."),
        ("Any recommendations for authentic Saint Lucian food?",
         "Don’t miss the national dish, Green Fig & Saltfish, at a local spot!"),
        ("Where can I go hiking?",
         "Tet Paul Nature Trail offers moderate hikes with stunning views of the Pitons."),
        ("Are there museums to visit?",
         "Yes—check out the Saint Lucia Folk Research Centre and local art galleries."),
    ]

    # Controls for cycling
    col1, col2 = st.columns([1, 1])
    with col1:
        st.session_state.qa_cycle_enabled = st.toggle("🔁 Auto-cycle Q&A", value=st.session_state.qa_cycle_enabled)
    with col2:
        if st.button("⏭ Next Q&A"):
            st.session_state.qa_index = (st.session_state.qa_index + 1) % len(sample_qa)

    q, a = sample_qa[st.session_state.qa_index]
    st.markdown(
        f"""
        <div style='margin-top:16px; padding:20px; border-radius:15px; background: rgba(255,255,255,0.25);'>
            <h4 style='color:#FFD580;'>💡 Sample Question</h4>
            <p style='color:#FFFFFF; font-weight:bold; margin-bottom:10px;'>{q}</p>
            <h4 style='color:#FFD580;'>🤖 Example Response</h4>
            <p style='color:#FFF0C1;'>{a}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Auto-cycle logic (only if enabled, and only on Home)
    if st.session_state.qa_cycle_enabled:
        time.sleep(4)  # cycle interval (seconds)
        st.session_state.qa_index = (st.session_state.qa_index + 1) % len(sample_qa)
        st.experimental_rerun()

    # Page overview footer (brief)
    st.markdown("---")
    st.markdown("**Page Quick Guide**  \n"
                "• 🏠 Home: Friendly overview + rotating Q&A.  \n"
                "• 📅 Itinerary Planner: Filter places by interest, map view, and AI itinerary.  \n"
                "• 💬 Chatbot: Ask anything about Saint Lucia.")

# =========================
# Page: Itinerary Planner
# =========================
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
        # Sort by rating if numeric
        if "Rating" in filtered_df.columns:
            filtered_df["Rating"] = pd.to_numeric(filtered_df["Rating"], errors="coerce")
            filtered_df = filtered_df.sort_values(by="Rating", ascending=False)

        # Display itinerary entries grouped by source
        for source, group in filtered_df.groupby("Source"):
            header = "Where are you heading o_o" if source == "Tourism" else \
                     "Where to eat > <" if source == "Restaurant" else \
                     "Culture trip incoming 🎭" if source == "Cultural" else "Education stops 🏫"
            st.subheader(header)
            for _, r in group.iterrows():
                st.markdown(f"**{r.get('Name','Unknown')}**  \n"
                            f"⭐ {r.get('Rating','N/A')} — {r.get('Type','N/A')}  \n"
                            f"📍 {r.get('Location','Unknown')}  \n"
                            f"💰 {r.get('Price','N/A')}")

        # Interactive map
        map_df = filtered_df.dropna(subset=["Latitude", "Longitude"]).copy()
        if not map_df.empty:
            m = folium.Map(location=[13.9094, -60.9789], zoom_start=10, tiles="OpenStreetMap")
            color_map = {"Tourism": "blue", "Restaurant": "red", "Cultural": "green", "Education": "purple"}
            for _, r in map_df.iterrows():
                folium.Marker(
                    location=[r["Latitude"], r["Longitude"]],
                    popup=f"<b>{r.get('Name','Unknown')}</b><br>"
                          f"⭐ {r.get('Rating','N/A')}<br>"
                          f"{r.get('Type','N/A')}<br>"
                          f"💰 {r.get('Price','N/A')}",
                    tooltip=r.get('Name','Unknown'),
                    icon=folium.Icon(color=color_map.get(r["Source"], "gray"))
                ).add_to(m)
            st_folium(m, width=700, height=500)

        # Save itinerary as CSV
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Save Itinerary as CSV",
            data=csv_data,
            file_name="broad_itinerary.csv",
            mime="text/csv"
        )

        # AI-generated itinerary
        if st.button("✨ Generate AI itinerary"):
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

    # Page overview footer
    st.markdown("---")
    st.markdown("**About this page:** Filter by interests, browse grouped results, view locations on a map, "
                "download your list, and generate a quick AI itinerary.")

# =========================
# Page: Chatbot
# =========================
elif st.session_state.page == "💬 Chatbot":
    st.header("💬 Chat with BROAD")
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask me about Saint Lucia..."):
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.spinner("Thinking..."):
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
                chat = model.start_chat(history=st.session_state.gemini_history)
                reply = chat.send_message(user_input).text
                st.session_state.gemini_history.append({"role": "user", "parts": [user_input]})
                st.session_state.gemini_history.append({"role": "model", "parts": [reply]})
            except Exception as e:
                reply = f"⚠️ Error: {e}"
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

    # Page overview footer
    st.markdown("---")
    st.markdown("**About this page:** Ask anything about Saint Lucia—tourism, culture, food, logistics—and get instant help.")
