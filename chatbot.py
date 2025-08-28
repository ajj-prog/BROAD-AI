import streamlit as st
import pandas as pd
import time
import uuid
import google.generativeai as genai
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from datetime import datetime
from dotenv import load_dotenv
import os


# ------------------ Gemini & Data ------------------ #
load_dotenv()
genai.configure(api_key=os.getenv("SECRET_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")
tourism_df    = pd.read_csv("tourism.csv").assign(Source="Tourism")
cultural_df   = pd.read_csv("cultural.csv").assign(Source="Cultural")
edu_df        = pd.read_csv("edu.csv").assign(Source="Education")
restaurant_df = pd.read_csv("resturant.csv").assign(Source="Restaurant")
combined_df   = pd.concat([tourism_df, cultural_df, edu_df, restaurant_df], ignore_index=True)

# ------------------ Themes & Tips ------------------ #
themes = {
    "Cotton Clouds 🌈🍭": {"bg":"#FFDEE9","accent":"#B5FFFC"},
    "Midnight Neon 🦇💜":       {"bg":"#630458","accent":"#8A2BE2"},
    "Sunset Glow 🌅✨":         {"bg":"#FFA500","accent":"#800080"},
    "Mint & Mocha 🍃☕":        {"bg":"#C1E1C1","accent":"#A67B5B"},
}
tips = [
    "During La Rose, communities dress in red and sing traditional songs.",
    "Cocoa tea is a beloved breakfast drink made with grated cacao and spices.",
    "The Pitons are twin volcanic peaks and a UNESCO World Heritage Site.",
    "Jounen Kwéyòl celebrates Creole heritage with food, music, and fashion.",
    "Bouyon music blends jumpy rhythms with call-and-response vocals."
]

# ------------------ Session Defaults ------------------ #
st.session_state.setdefault("users", {})
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("user", {})
st.session_state.setdefault("theme", "Sunset Glow 🌅✨")
st.session_state.setdefault("selected_theme", "Sunset Glow 🌅✨")
st.session_state.setdefault("show_theme_modal", False)
st.session_state.setdefault("page", "🏠 Home")
st.session_state.setdefault("chat_messages", [])
st.session_state.setdefault("generated_itinerary", "")
st.session_state.setdefault("current_itin_items", [])
st.session_state.setdefault("tip_index", 0)
st.session_state.setdefault("last_tip_time", time.time())


# ------------------ Login ------------------ #
def render_login():
    st.title("🔐 Sign Up / Log In")
    email = st.text_input("Email")
    pwd   = st.text_input("Password", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔑 Log In"):
            user = st.session_state.users.get(email)
            if user and user["password"] == pwd:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.theme = user["theme"]
                st.session_state.page = "🏠 Home"
    with col2:
        if st.button("📝 Sign Up"):
            if email and pwd:
                st.session_state.users[email] = {
                    "email": email,
                    "password": pwd,
                    "username": "New User",
                    "theme": "Sunset Glow 🌅✨",
                    "saved_itineraries": []
                }
                st.session_state.authenticated = True
                st.session_state.user = st.session_state.users[email]
                st.session_state.theme = "Sunset Glow 🌅✨"
                st.session_state.page = "🏠 Home"

if not st.session_state.authenticated:
    render_login()
    st.stop()

# ------------------ CSS ------------------ #
current = themes[st.session_state.theme]
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
  background: linear-gradient(45deg, {current['bg']}, {current['accent']}, {current['bg']});
  background-size: 400% 400%;
  animation: gradientShift 12s ease infinite;
}}
@keyframes gradientShift {{
  0% {{ background-position: 0% 50%; }}
  50% {{ background-position: 100% 50%; }}
  100% {{ background-position: 0% 50%; }}
}}
@keyframes bob {{
  0%, 100% {{ transform: translateY(0); }}
  50% {{ transform: translateY(-10px); }}
}}
@keyframes bounce {{
  0% {{ transform: translateY(0); }}
  50% {{ transform: translateY(-6px); }}
  100% {{ transform: translateY(0); }}
}}
@keyframes pulseGlow {{
  0% {{ box-shadow: 0 0 4px {current['accent']}; }}
  50% {{ box-shadow: 0 0 12px {current['accent']}; }}
  100% {{ box-shadow: 0 0 4px {current['accent']}; }}
}}
section[data-testid="stSidebar"] {{
  background: linear-gradient(to bottom, {current['accent']}, {current['bg']});
  animation: pulseGlow 3s ease-in-out infinite;
}}
section[data-testid="stSidebar"] * {{
  color: white !important;
}}
#loading-overlay {{
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.6); display: flex;
  align-items: center; justify-content: center;
  z-index: 9999; color: white; font-size: 24px;
}}
#loading-overlay::before {{
  content: "⏳";
  font-size: 48px;
  animation: bob 1s infinite;
  margin-right: 12px;
}}
.home-card {{
  position: relative; border-radius: 12px; padding: 24px;
  min-height: 200px; margin-bottom: 24px;
  box-shadow: 0 6px 8px rgba(0,0,0,0.15);
  transition: transform 0.3s ease;
  background: white;
  display: flex; flex-direction: column; justify-content: space-between;
}}
.home-card:hover {{ animation: bounce 0.4s ease; }}
.card-icon {{ font-size: 32px; text-align: center; }}
.card-title {{ font-weight: bold; font-size: 20px; text-align: center; margin-top: 8px; }}
.card-desc {{ font-size: 14px; text-align: center; margin: 8px 0; color: #444; }}
.card-meta {{ font-size: 12px; text-align: center; color: #888; }}
.card-button .stButton > button {{
  width: 100%; background: linear-gradient(to right, #4facfe, #00f2fe);
  color: white; border: none; border-radius: 8px; padding: 8px;
  font-weight: bold; cursor: pointer;
}}
.cultural-spotlight {{
  animation: floatText 3s ease-in-out infinite;
  font-style: italic; color: #fff;
  background: rgba(0,0,0,0.2); padding: 8px 12px;
  border-radius: 8px; display: inline-block;
}}
@keyframes floatText {{
  0% {{ transform: translateY(0); }}
  50% {{ transform: translateY(-4px); }}
  100% {{ transform: translateY(0); }}
}}
#theme-modal {{
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.6); display: flex;
  align-items: center; justify-content: center;
  z-index: 9999;
}}
#theme-modal .modal-content {{
  background: white; padding: 24px; border-radius: 12px;
  width: 300px; text-align: center;
}}
.home-card {{
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    border-radius: 12px;
    padding: 24px;
    min-height: 250px;
    margin-bottom: 24px;
    box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    background: white;
}}
.home-card .card-icon {{
    font-size: 40px;
    text-align: center;
    margin-bottom: 12px;
}}
.home-card .card-title {{
    font-size: 20px;
    font-weight: bold;
    text-align: center;
    margin-bottom: 8px;
}}
.home-card .card-desc {{
    font-size: 14px;
    text-align: center;
    margin: 8px 0;
    color: #555;
}}
.home-card .card-meta {{
    font-size: 12px;
    text-align: center;
    color: #888;
    margin-bottom: 16px;
}}
  .home-card {{
    background: linear-gradient(
      135deg,
      {current['accent']},
      {current['bg']}
    ) !important;
    color: white !important;
  }}

  /* Optional: distinct colors per card
  .home-card:nth-child(1) {{ background: #FFDEE9; }}
  .home-card:nth-child(2) {{ background: #2C003E; }}
  .home-card:nth-child(3) {{ background: #FFA500; }}
  */

}}
/* make every content container transparent and drop no shadow */
section[data-testid="stAppViewContainer"] .block-container,
section[data-testid="stAppViewContainer"] .stMarkdownContainer,
section[data-testid="stAppViewContainer"] .css-1d391kg {{
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
}}
</style>
""", unsafe_allow_html=True)

def show_loading(msg="Loading…"):
    ph = st.empty()
    ph.markdown(f'<div id="loading-overlay">{msg}</div>', unsafe_allow_html=True)
    return ph

def hide_loading(ph):
    ph.empty()


# ------------------ Sidebar ------------------ #
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center;padding:12px 0;'>
      <div style='font-size:32px;'>🅱️</div>
      <h3 style='margin:0;'>B.R.O.A.D.</h3>
      <p style='font-size:12px;'>Welcome, {st.session_state.user['username']}</p>
      <p style='font-size:12px;'>Theme: <strong>{st.session_state.theme}</strong></p>
    </div>
    <hr style='border:none;height:1px;background:#fff3;margin:12px 0;'/>
    """, unsafe_allow_html=True)

    st.markdown("### 🧭 Navigation")
    nav_items = [
        ("🏠 Home", "nav_home"),
        ("👤 Profile Hub", "nav_profile"),
        ("📅 Itinerary Planner", "nav_itinerary"),
        ("🧠 Trip Guide", "nav_trip"),
        ("💬 Chatbot", "nav_chatbot"),
        ("🗂 Saved Itineraries", "nav_saved")
    ]
    for label, key in nav_items:
        if st.button(label, key=key):
            st.session_state.page = label

    st.markdown("### 🎭 Theme Selector")
    if st.button("Change Theme 🎨", key="open_theme_modal"):
        st.session_state.show_theme_modal = True

    st.markdown("### 💡 Tip of the Moment")
    if time.time() - st.session_state.last_tip_time > 10:
        st.session_state.tip_index = (st.session_state.tip_index + 1) % len(tips)
        st.session_state.last_tip_time = time.time()
    st.markdown(f"**{tips[st.session_state.tip_index]}**")

# ------------------ Page Functions ------------------ #
def render_home():
    from datetime import datetime
    import time

    # 1. Hero banner with dynamic greeting
    hour = datetime.now().hour
    greeting = (
        "Good morning" if hour < 12
        else "Good afternoon" if hour < 18
        else "Good evening"
    )
    st.markdown(f"""
    <div style='
        background: linear-gradient(
            to right,
            {current['bg']},
            {current['accent']}
        );
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        color: white;
    '>
      <h1>Welcome to B.R.O.A.D. AI</h1>
      <h3>{greeting}, {st.session_state.user['username']} 🌴</h3>
      <p>Your guide to Saint Lucia’s culture, history & natural beauty</p>
    </div>
    """, unsafe_allow_html=True)

    # 2. Floating cultural spotlight
    spotlights = [
        "🎶 La Marguerite is celebrated with purple flowers and Creole songs.",
        "🍲 Try green fig and saltfish — Saint Lucia’s national dish.",
        "🗣 Kwéyòl is spoken widely and celebrated during Jounen Kwéyòl in October."
    ]
    idx = int(time.time() / 10) % len(spotlights)
    st.markdown(
        f"<div class='cultural-spotlight'>{spotlights[idx]}</div>",
        unsafe_allow_html=True
    )

    # 3. Explore cards
    st.markdown("### 🌟 Explore")
    cols = st.columns(3)
    cards = [
        {
            "icon": "👤",
            "title": "Profile Hub",
            "desc": "Customize your name, theme, and view activity.",
            "meta": "Category: Profile",
            "page": "👤 Profile Hub"
        },
        {
            "icon": "📅",
            "title": "Plan a Trip",
            "desc": "Generate smart itineraries with cultural insights.",
            "meta": "Category: Planner",
            "page": "📅 Itinerary Planner"
        },
        {
            "icon": "💬",
            "title": "Chat with B.R.O.A.D.",
            "desc": "Ask questions, get tips, and explore Saint Lucia.",
            "meta": "Category: Chat",
            "page": "💬 Chatbot"
        }
    ]

    for i, (col, card) in enumerate(zip(cols, cards)):
        with col:
            st.markdown('<div class="home-card">', unsafe_allow_html=True)

            st.markdown(
                f'<div class="card-icon">{card["icon"]}</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="card-title">{card["title"]}</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="card-desc">{card["desc"]}</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="card-meta">{card["meta"]}</div>',
                unsafe_allow_html=True
            )

            # Use a constant "Explore" label and unique key
            btn_key = f"home_{i}_{card['title'].replace(' ', '_')}"
            if st.button("Explore", key=btn_key):
                st.session_state.page = card["page"]

            st.markdown('</div>', unsafe_allow_html=True)
def render_profile_hub():
    st.subheader("👤 Profile")
    st.text_input("Username", value=st.session_state.user.get("username", ""), key="profile_username")
    theme_choice = st.selectbox("Choose Theme", list(themes.keys()), index=list(themes.keys()).index(st.session_state.theme), key="profile_theme")
    if st.button("Save Profile", key="save_profile"):
        st.session_state.user["username"] = st.session_state.profile_username
        st.session_state.user["theme"] = theme_choice
        st.session_state.theme = theme_choice
        st.success("Profile updated!")

    st.markdown("### ⚡ Quick Actions")
    c1, c2, c3 = st.columns(3)
    if c1.button("📅 Itinerary Planner", key="profile_itin"): st.session_state.page = "📅 Itinerary Planner"
    if c2.button("🧠 Trip Guide", key="profile_trip"): st.session_state.page = "🧠 Trip Guide"
    if c3.button("💬 Chatbot", key="profile_chat"): st.session_state.page = "💬 Chatbot"

    st.markdown("### 📊 Activity Summary")
    st.write(f"Saved trips: `{len(st.session_state.user['saved_itineraries'])}`")

def render_itinerary_planner():
    st.subheader("📅 Smart Itinerary Planner")
    prompt = st.text_area("Describe your ideal trip:", key="itin_prompt")
    if st.button("Generate Itinerary", key="gen_itin"):
        loader = show_loading("Planning your itinerary…")
        sample = combined_df.sample(min(len(combined_df),10), random_state=42)
        ctx = "\n".join(f"- {r['Name']} ({r['Source']})" for _, r in sample.iterrows())
        full = f"You are B.R.O.A.D st.lucian tourism heritage \n{ctx}\nUser request: {prompt}\nPlan a day-by-day itinerary, if you are missing info from the give info feel free to add relevant info."
        resp = model.generate_content(full)
        st.session_state.generated_itinerary = resp.text
        st.session_state.current_itin_items = sample.to_dict("records")
        hide_loading(loader)
        st.success("Itinerary generated!")

    if st.session_state.generated_itinerary:
        st.markdown("### ✨ Your AI-Enhanced Itinerary")
        st.markdown(st.session_state.generated_itinerary)
        items = st.session_state.current_itin_items
        lat_k = next((k for k in items[0] if k.lower().startswith("lat")), None)
        lon_k = next((k for k in items[0] if k.lower().startswith("lon")), None)
        if lat_k and lon_k:
            m = folium.Map(location=[items[0][lat_k], items[0][lon_k]], zoom_start=10)
            mc = MarkerCluster().add_to(m)
            for it in items:
                folium.Marker([it[lat_k], it[lon_k]], popup=it["Name"]).add_to(mc)
            st_folium(m, width=700, height=450)
        if st.button("💾 Save This Itinerary", key="save_itin"):
            itin = {
                "id": uuid.uuid4().hex[:8],
                "name": f"Trip {time.strftime('%Y-%m-%d %H:%M')}",
                "created_at": int(time.time()),
                "notes": prompt,
                "items": items,
                "generated_text": st.session_state.generated_itinerary
            }
            st.session_state.user["saved_itineraries"].append(itin)
            st.success("Itinerary saved!")

def render_chatbot():
    st.markdown("<h2>💬 Chat with B.R.O.A.D.</h2>", unsafe_allow_html=True)
    for msg in st.session_state.chat_messages[-10:]:
        tag = "🧑 You" if msg["role"] == "user" else "💬 B.R.O.A.D."
        st.markdown(f"**{tag}:** {msg['content']}")
    user = st.text_input("Your message:", key="chat_input")
    if user and st.button("Send", key="chat_send"):
        loader = show_loading("Thinking…")
        st.session_state.chat_messages.append({"role": "user", "content": user})
        resp = model.generate_content(f"You are B.R.O.A.D.…\nUser: {user}")
        st.session_state.chat_messages.append({"role": "assistant", "content": resp.text})
        hide_loading(loader)

def render_trip_guide():
    st.subheader("🧠 Trip Guide")
    itins = st.session_state.user["saved_itineraries"]
    if not itins:
        st.info("Save an itinerary first.")
        return
    names = [i["name"] for i in itins]
    sel = st.selectbox("Select a trip:", names, key="guide_select")
    if st.button("Generate Guide", key="gen_guide"):
        loader = show_loading("Building your guide…")
        itin = next(i for i in itins if i["name"] == sel)
        lines = "\n".join(f"- {item['Name']} ({item['Source']})" for item in itin["items"])
        full = f"You are B.R.O.A.D.…\nUser’s itinerary:\n{lines}\nProvide packing, customs, and culinary tips."
        resp = model.generate_content(full)
        hide_loading(loader)
        st.markdown("### 📖 Your Personalized Trip Guide")
        st.markdown(resp.text)
        lat_k = next((k for k in itin["items"][0] if k.lower().startswith("lat")), None)
        lon_k = next((k for k in itin["items"][0] if k.lower().startswith("lon")), None)
        if lat_k and lon_k:
            m = folium.Map(location=[itin["items"][0][lat_k], itin["items"][0][lon_k]], zoom_start=10)
            mc = MarkerCluster().add_to(m)
            for it in itin["items"]:
                folium.Marker([it[lat_k], it[lon_k]], popup=it["Name"]).add_to(mc)
            st_folium(m, width=700, height=450)

def render_saved_itineraries():
    st.subheader("🗂 Saved Itineraries")
    itins = st.session_state.user["saved_itineraries"]
    if not itins:
        st.info("No saved itineraries.")
        return
    for itin in itins:
        with st.expander(itin["name"]):
            st.write("Notes:", itin["notes"])
            st.write("Created:", time.strftime("%Y-%m-%d %H:%M", time.localtime(itin["created_at"])))
            st.markdown("### ✨ Itinerary Preview")
            st.markdown(itin.get("generated_text", "No itinerary text found."))
            lat_k = next((k for k in itin["items"][0] if k.lower().startswith("lat")), None)
            lon_k = next((k for k in itin["items"][0] if k.lower().startswith("lon")), None)
            if lat_k and lon_k:
                m = folium.Map(location=[itin["items"][0][lat_k], itin["items"][0][lon_k]], zoom_start=10)
                mc = MarkerCluster().add_to(m)
                for it in itin["items"]:
                    folium.Marker([it[lat_k], it[lon_k]], popup=it["Name"]).add_to(mc)
                st_folium(m, width=700, height=450)

# ------------------ Page Router ------------------ #
pages = {
    "🏠 Home":               render_home,
    "👤 Profile Hub":        render_profile_hub,
    "📅 Itinerary Planner":  render_itinerary_planner,
    "🧠 Trip Guide":         render_trip_guide,
    "💬 Chatbot":            render_chatbot,
    "🗂 Saved Itineraries":  render_saved_itineraries
}
pages.get(st.session_state.page, render_home)()
