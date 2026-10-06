import streamlit as st
import os
import io

import database as db
import ai_engine as ai
import utils

# Page Configuration
st.set_page_config(
    page_title="TrailTalk | Offline Open-Source AI Walk Journal",
    page_icon="🥾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize DB
db.init_db()

# Custom CSS for polished styling
st.markdown("""
<style>
    .stApp {
        background-color: #f7f9f6;
    }
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: #1e3a1e;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #4a6b4a;
        margin-bottom: 1.5rem;
    }
    .badge-offline {
        background-color: #2e7d32;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .card-box {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #e2e8e0;
        margin-bottom: 15px;
    }
    .fact-box {
        background-color: #eef7ed;
        border-left: 4px solid #388e3c;
        padding: 12px 16px;
        border-radius: 4px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown('<div class="main-title">🥾 TrailTalk</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Offline Nature Identifier & Outdoor Walk Journal powered by Open-Weight AI models</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🥾 TrailTalk Controls")
    
    # Check Ollama Status
    ollama_ready, available_models, active_url = ai.check_ollama_status()
    if ollama_ready:
        st.success(f"🟢 Local Ollama Active ({len(available_models)} model(s) found)")
        st.caption(f"Connected to: `{active_url}`")
        selected_model = st.selectbox("Vision Model", available_models if available_models else ["gemma3:4b"], index=0)
    else:
        st.error("🔴 Ollama Disconnected")
        st.caption("Ollama local service not detected. Connect local Ollama (`ollama run gemma3:4b`) for live local vision model inference.")
        selected_model = "gemma3:4b"
        
    st.divider()
    
    st.markdown("### 🏆 Hacktoberfest 2026")
    st.markdown("**Theme:** *Touch Grass* (Week 1)")
    st.caption("Build with open-weight AI that gets people off the screen and into the world.")
    
    st.divider()
    stats = db.get_stats()
    st.metric("Total Trail Sightings", stats["total"])
    st.metric("Unique Species Logged", stats["unique"])

# Main Navigation Tabs
tab_identify, tab_journal, tab_summary = st.tabs(["📷 Identify & Log", "📖 Walk Journal", "📊 Walk Summary & DEV Post"])

# TAB 1: IDENTIFY & LOG
with tab_identify:
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("1. Capture or Upload Trail Photo")
        img_source = st.radio("Photo Source", ["Upload File", "Take Photo with Camera"], horizontal=True)
        
        uploaded_file = None
        if img_source == "Upload File":
            uploaded_file = st.file_uploader("Choose a nature photo (Plant, Tree, Bird, Insect)", type=["jpg", "jpeg", "png", "webp"])
        else:
            uploaded_file = st.camera_input("Take a photo on the trail")
            
        user_hint = st.text_input("Optional Hint / Context", placeholder="e.g. Found on a tree branch near the lake, fast chirping sound")
        location_note = st.text_input("Location / Trail Note", placeholder="e.g. Barrackpore Park Trail, North Path")

    with col_right:
        st.subheader("2. AI Analysis & Identification")
        
        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()
            st.image(image_bytes, caption="Uploaded Trail Observation", width="stretch")
            
            if st.button("🌿 Identify Sighting with Open AI", type="primary", width="stretch"):
                with st.spinner("Analyzing with local open-weight vision model..."):
                    result = ai.identify_nature_element(image_bytes, user_hint=user_hint, preferred_model=selected_model)
                    
                    st.session_state['last_result'] = result
                    st.session_state['last_img_bytes'] = image_bytes
                    st.session_state['location_note'] = location_note
        else:
            st.info("👈 Upload or capture a photo on your trail walk to get started.")

    # Show Analysis Result & Save Button if available
    if 'last_result' in st.session_state and st.session_state['last_result']:
        res = st.session_state['last_result']
        st.divider()
        st.subheader("🎯 Identification Result")
        
        if res.get("success", True) is False:
            st.error(res.get("error", "An unknown error occurred during identification."))
        else:
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.markdown(f"### {res.get('species_name', 'Unknown Species')}")
                st.caption(f"**Category:** {res.get('category')} | **AI Engine:** `{res.get('ai_model_used')}`")
            with c2:
                st.metric("Confidence", res.get('confidence', 'High'))
            with c3:
                st.markdown(f"**Safety/Care Note:**\n{res.get('care_or_safety_note', 'N/A')}")
                
            st.markdown(f'<div class="fact-box"><b>💡 Ecological Fun Fact:</b> {res.get("fun_fact")}</div>', unsafe_allow_html=True)
            
            st.write("")
            if st.button("💾 Save Sighting to Walk Journal", type="secondary", width="stretch"):
                img_path = utils.save_uploaded_image(io.BytesIO(st.session_state['last_img_bytes']))
                
                db.add_sighting(
                    species_name=res.get("species_name"),
                    category=res.get("category"),
                    fun_fact=res.get("fun_fact"),
                    location_note=st.session_state.get('location_note', ''),
                    image_path=img_path,
                    confidence=res.get("confidence"),
                    ai_model_used=res.get("ai_model_used"),
                    notes=res.get("identification_traits", "")
                )
                st.success("✅ Saved to your TrailTalk Walk Journal!")
                st.session_state['last_result'] = None
                st.rerun()

# TAB 2: WALK JOURNAL
with tab_journal:
    st.subheader("📖 Your Outdoor Sightings Journal")
    sightings = db.get_all_sightings()
    
    if not sightings:
        st.info("No trail sightings logged yet. Go outside, capture plants or birds, and build your walk log!")
    else:
        categories = list(set(s['category'] for s in sightings))
        filter_cat = st.multiselect("Filter by Category", categories, default=categories)
        filtered_sightings = [s for s in sightings if s['category'] in filter_cat]
        
        for row in filtered_sightings:
            with st.container():
                st.markdown('<div class="card-box">', unsafe_allow_html=True)
                col_a, col_b = st.columns([1, 3])
                
                with col_a:
                    if row['image_path'] and os.path.exists(row['image_path']):
                        st.image(row['image_path'], width="stretch")
                    else:
                        st.markdown("📷 *No Image Saved*")
                        
                with col_b:
                    st.markdown(f"### {row['species_name']} <span class='badge-offline'>{row['category']}</span>", unsafe_allow_html=True)
                    st.caption(f"📅 Logged: {row['timestamp']} | 📍 {row['location_note'] or 'On Trail'}")
                    st.markdown(f"**Fun Fact:** {row['fun_fact']}")
                    st.markdown(f"**Traits:** {row['notes']}")
                    st.caption(f"Model used: `{row['ai_model_used']}` | Confidence: {row['confidence']}")
                    
                    if st.button(f"🗑️ Delete Entry #{row['id']}", key=f"del_{row['id']}"):
                        db.delete_sighting(row['id'])
                        st.success("Deleted entry.")
                        st.rerun()
                        
                st.markdown('</div>', unsafe_allow_html=True)

# TAB 3: WALK SUMMARY & DEV POST
with tab_summary:
    st.subheader("📊 Trail Walk Summary & DEV Submission Helper")
    
    sightings = db.get_all_sightings()
    
    if not sightings:
        st.warning("Log at least one sighting to generate your summary recap.")
    else:
        st.markdown(ai.generate_trail_summary(sightings))
        st.divider()
        
        st.subheader("📝 Export Formatted Markdown for DEV Community Post")
        st.caption("Copy this pre-formatted Markdown directly into your Hacktoberfest Week 1 DEV post submission!")
        
        md_content = utils.export_journal_markdown(sightings)
        st.code(md_content, language="markdown")
        
        st.download_button(
            label="📥 Download Journal Markdown",
            data=md_content,
            file_name="trailtalk_journal.md",
            mime="text/markdown"
        )
        
        st.divider()
        if st.button("⚠️ Clear Entire Journal Data"):
            db.clear_all_sightings()
            st.success("Journal cleared!")
            st.rerun()

# Final readability overrides
st.markdown("""
<style>
/* Main application text */
.stApp {
    color: #1f2937 !important;
}

/* Make normal Streamlit content readable */
.stApp p,
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4,
.stApp h5,
.stApp h6,
.stApp label {
    color: #1f2937 !important;
}

/* Main TrailTalk headings */
.main-title {
    color: #16351f !important;
}

.sub-title {
    color: #446b4a !important;
}

/* Tabs */
button[data-baseweb="tab"] {
    color: #374151 !important;
}

/* Input labels */
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stFileUploader label,
.stRadio label {
    color: #1f2937 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    color: #f9fafb !important;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label {
    color: #f9fafb !important;
}
</style>
""", unsafe_allow_html=True)

# Final sidebar readability fix
st.markdown("""
<style>
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
    color: #f9fafb !important;
}

section[data-testid="stSidebar"] .stMarkdown {
    color: #f9fafb !important;
}

section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
    color: #f9fafb !important;
}

section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)
