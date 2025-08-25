# --------------------- IMPORTS --------------------- #
import streamlit as st
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import os, json, hashlib, uuid, time, pathlib
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# --------------------- CONFIG --------------------- #
load_dotenv()
genai.configure(api_key=os.getenv("SECRET_KEY"))
DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
ITINS_FILE = DATA_DIR / "itineraries.json"

# --------------------- DATA LOAD --------------------- #
def clean_columns(df): return df.columns.str.strip().str.title()
def load_df(path, source): 
    df = pd.read_csv(path)
    df.columns = clean_columns(df)
    df['Source'] = source
    for col, default in [("Latitude", 0.0), ("Longitude", 0.0), ("Rating", "N/A"), ("Type", "N/A"), ("Price", "N/A")]:
        if col not in df.columns: df[col] = default
        df[col] = df[col].fillna(default)
    return df

tourism_df = load_df("tourism.csv", "Tourism")
edu_df = load_df("edu.csv", "Education")
cultural_df = load_df("cultural.csv", "Cultural")
restaurant_df = load_df("resturant.csv", "Restaurant")

# --------------------- SESSION STATE --------------------- #
for k, v in {
    "page": "📜 Introduction",
    "active_button": "📜 Introduction",
    "chat_messages": [],
    "gemini_history": [],
    "user": None,
    "loading": False,
    "qa_idx": 0,
    "qa_last": 0.0
}.items():
    if k not in st.session_state: st.session_state[k] = v

# --------------------- AUTH --------------------- #
def _read_json(path, default): 
    try: return json.load(open(path, "r", encoding="utf-8"))
    except: return default
def _write_json(path, data): 
    json.dump(data, open(path, "w", encoding="utf-8"), indent=2)
def _hash_pw(pw, salt): return hashlib.sha256((salt + pw).encode()).hexdigest()
def signup(email, pw, name=""): 
    users = _read_json(USERS_FILE, {})
    if email in users: raise ValueError("Email exists")
    salt = uuid.uuid4().hex
    users[email] = {"email": email, "salt": salt, "hash": _hash_pw(pw, salt), "display_name": name}
    _write_json(USERS_FILE, users)
    return {"email": email, "display_name": name}
def login(email, pw): 
    users = _read_json(USERS_FILE, {})
    u = users.get(email)
    if not u or _hash_pw(pw, u["salt"]) != u["hash"]: raise ValueError("Invalid login")
    return {"email": u["email"], "display_name": u.get("display_name", "")}
def logout(): st.session_state.user = None

# --------------------- ITINERARY STORE --------------------- #
def list_itineraries(email): return _read_json(ITINS_FILE, {}).get(email, [])
def save_itinerary(email, itin): 
    store = _read_json(ITINS_FILE, {})
    arr = store.get(email, [])
    idx = next((i for i, x in enumerate(arr) if x["id"] == itin["id"]), None)
    if idx is None: arr.append(itin)
    else: arr[idx] = itin
    store[email] = arr
    _write_json(ITINS_FILE, store)
def delete_itinerary(email, id): 
    store = _read_json(ITINS_FILE, {})
    store[email] = [x for x in store.get(email, []) if x["id"] != id]
    _write_json(ITINS_FILE, store)
def merge_itineraries(a, b, name=None): 
    def key(i): return f"{i.get('Name','')}|{i.get('Latitude','')}|{i.get('Longitude','')}"
    seen, items = set(), []
    for src in (a["items"], b["items"]):
        for i in src:
            k = key(i)
            if k not in seen: seen.add(k); items.append(i)
    return {
        "id": uuid.uuid4().hex[:8],
        "name": name or f"{a['name']} + {b['name']}",
        "created_at": int(time.time()),
        "notes": "\n\n".join([a.get("notes",""), b.get("notes","")]).strip(),
        "items": items
    }

# --------------------- UTILITIES --------------------- #
def clamp_rating(s): return pd.to_numeric(s, errors="coerce").fillna(0).clip(0,5).round(1)
def parse_price(v): 
    try: return float(str(v).replace("XCD","").replace("$","").strip())
    except: return None
def price_tier(p): 
    if p is None: return "N/A"
    return "$" if p<25 else "$$" if p<75 else "$$$" if p<150 else "$$$$"
def df_to_items(df): 
    cols = ["Name","Latitude","Longitude","Rating","Type","Price","Source","Location"]
    return [{c: r.get(c, "") for c in cols} for _, r in df[cols].fillna("").iterrows()]
def build_trip_plan(df): 
    pre = [
        {"title": "Confirm bookings", "details": "Hotels, tours, transfers 48h before."},
        {"title": "Pack smart", "details": "Light clothes, sunscreen, bug spray, water shoes."},
        {"title": "Money & data", "details": "XCD cash, cards, local SIM or eSIM."},
        {"title": "Transport", "details": "Plan UVF/SLU transfer; drive left."},
    ]
    df["Rating"] = clamp_rating(df["Rating"])
    m = df.sort_values("Rating", ascending=False).head(1)
    a = df[~df.index.isin(m.index)].head(2)
    e = df[~df.index.isin(m.index.union(a.index))].head(1)
    day = []
    if not m.empty: day.append({"title": f"Morning: {m.iloc[0]['Name']}", "details": "Arrive early, hydrate."})
    for _, r in a.iterrows(): day.append({"title": f"Afternoon: {r['Name']}", "details": "Lunch nearby, pace yourself."})
    if not e.empty: day.append({"title": f"Evening: {e.iloc[0]['Name']}", "details": "Golden hour photos, dinner."})
    return {"pretrip": pre, "day": day}

# --------------------- SIDEBAR --------------------- #
st.sidebar.title("🌴 BROAD ISLAND INTEL")
pages = ["📜 Introduction", "🏠 Home", "📅 Itinerary Planner", "🗂 Saved Itineraries", "💬 Chatbot", "👤 Account"]
for p in pages:
    if st.sidebar.button(p): st.session_state.page = p; st.session_state.active_button = p
if st.session_state.user: st.sidebar.success(f"Signed in as {st.session_state.user['email']}")
else: st.sidebar.info("Not signed in")

# --------------------- LOADING OVERLAY --------------------- #
st.markdown("""
<style>
#overlay { position: fixed; inset: 0; z-index: 9999; display: none; align-items: center; justify-content: center;
  background: rgba(11,19,43,.85); color: #fff; font-family: system-ui; }
#overlay.show { display: flex; }
.loader { width: 48px; height: 48px; border: 4px solid #fff3; border-top-color:#4cc9f0; border-radius:50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg) } }
</style>
<div id="overlay" class="{klass}">
  <div style="text-align:center"><div class="loader"></div><div style="margin-top:12px">Loading your Saint Lucia journey…</div></div>
</div>
""".replace("{klass}", "show" if st.session_state.loading else ""), unsafe_allow_html=True)

# --------------------- INTRO PAGE --------------------- #
if st.session_state.page == "
