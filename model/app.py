import streamlit as st
import requests
import pandas as pd
import time
import os
import json
import io
from datetime import datetime
from PIL import Image

# ──────────────────────────────────────────────
# 1. Configuration & Constants
# ──────────────────────────────────────────────
API_URL = os.environ.get("BACKEND_API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="CatalogStream-AI Portal",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# 2. Session State Initialization
# ──────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "api_status" not in st.session_state:
    st.session_state.api_status = "unknown"

# ──────────────────────────────────────────────
# 3. Enhanced CSS — Glassmorphism + Animations
# ──────────────────────────────────────────────
def get_css(theme):
    if theme == "dark":
        bg_gradient = "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)"
        card_bg = "rgba(255, 255, 255, 0.05)"
        card_border = "rgba(255, 255, 255, 0.1)"
        text_primary = "#ffffff"
        text_secondary = "#b8b8c8"
        accent = "#00d4ff"
    else:
        bg_gradient = "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 50%, #e8eaf6 100%)"
        card_bg = "rgba(255, 255, 255, 0.75)"
        card_border = "rgba(0, 0, 0, 0.08)"
        text_primary = "#1a1a2e"
        text_secondary = "#555566"
        accent = "#2563eb"

    return f"""
    <style>
        .stApp {{ background: {bg_gradient}; font-family: 'Segoe UI', system-ui, sans-serif; }}
        .animated-bg {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; }}
        .animated-bg::before, .animated-bg::after {{
            content: ''; position: absolute; border-radius: 50%;
            background: radial-gradient(circle, {accent}22 0%, transparent 70%);
            animation: floatOrb 20s infinite ease-in-out;
        }}
        .animated-bg::before {{ width: 300px; height: 300px; top: 10%; left: 5%; animation-duration: 25s; }}
        .animated-bg::after {{ width: 250px; height: 250px; bottom: 15%; right: 8%; animation-duration: 30s; animation-delay: 5s; }}
        @keyframes floatOrb {{ 0%,100% {{ transform: translate(0,0) scale(1); opacity: 0.3; }} 25% {{ transform: translate(20px,-15px) scale(1.05); opacity: 0.25; }} 50% {{ transform: translate(-10px,20px) scale(0.95); opacity: 0.3; }} 75% {{ transform: translate(15px,10px) scale(1.02); opacity: 0.28; }} }}
        .glass-card {{ background: {card_bg}; backdrop-filter: blur(20px) saturate(180%); -webkit-backdrop-filter: blur(20px) saturate(180%); border: 1px solid {card_border}; border-radius: 18px; padding: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.15); transition: all 0.3s cubic-bezier(0.4,0,0.2,1); }}
        .glass-card:hover {{ transform: translateY(-2px); box-shadow: 0 12px 40px rgba(0,0,0,0.25); border-color: {accent}44; }}
        .stat-card {{ background: {card_bg}; backdrop-filter: blur(15px); border: 1px solid {card_border}; border-radius: 14px; padding: 16px 20px; margin-bottom: 10px; transition: all 0.25s ease; }}
        .stat-card:hover {{ background: {accent}15; border-color: {accent}55; }}
        .stat-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: {text_secondary}; margin-bottom: 4px; }}
        .stat-value {{ font-size: 18px; font-weight: 700; color: {text_primary}; }}
        .product-card {{ background: {card_bg}; backdrop-filter: blur(20px) saturate(180%); border: 1px solid {card_border}; border-radius: 16px; padding: 22px; box-shadow: 0 8px 32px rgba(0,0,0,0.12); position: relative; overflow: hidden; }}
        .product-card::before {{ content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: linear-gradient(90deg, {accent}, #ff6b9d, #4ecdc4); }}
        .platform-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin: 2px; }}
        .badge-meesho {{ background: #ff6b35; color: #fff; }} .badge-amazon {{ background: #ff9900; color: #000; }} .badge-myntra {{ background: #262626; color: #fff; }}
        .keyword-tag {{ display: inline-block; background: {accent}22; color: {accent}; padding: 4px 12px; border-radius: 12px; font-size: 12px; margin: 2px; font-weight: 500; transition: all 0.2s ease; }}
        .keyword-tag:hover {{ background: {accent}44; transform: translateY(-1px); }}
        .bullet-list {{ list-style: none; padding: 0; }}
        .bullet-list li {{ padding: 8px 0; padding-left: 32px; position: relative; border-bottom: 1px solid {card_border}; color: {text_primary}; }}
        .bullet-list li:last-child {{ border-bottom: none; }}
        .bullet-list li::before {{ content: '✓'; position: absolute; left: 0; color: {accent}; font-weight: 700; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
        .stTabs [data-baseweb="tab"] {{ background: {card_bg}; border-radius: 12px 12px 0 0; padding: 10px 24px; border: 1px solid {card_border}; border-bottom: none; transition: all 0.2s ease; }}
        .stTabs [data-baseweb="tab"]:hover {{ background: {accent}15; }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{ background: {accent}; color: #fff; }}
        .stProgress > div > div {{ background: {accent}; border-radius: 10px; }}
        ::-webkit-scrollbar {{ width: 8px; }} ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: {accent}44; border-radius: 4px; }} ::-webkit-scrollbar-thumb:hover {{ background: {accent}66; }}
        h1 {{ background: linear-gradient(90deg, {accent}, #ff6b9d, #4ecdc4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; letter-spacing: -0.5px; }}
        h2, h3, h4 {{ color: {text_primary}; }} .subtitle {{ color: {text_secondary}; font-size: 15px; font-weight: 400; }}
        .stTextArea textarea {{ background: {card_bg} !important; border: 1px solid {card_border} !important; border-radius: 12px !important; color: {text_primary} !important; padding: 14px !important; }}
        .stTextInput input {{ background: {card_bg} !important; border: 1px solid {card_border} !important; border-radius: 10px !important; color: {text_primary} !important; }}
        .stButton > button {{ border-radius: 12px !important; font-weight: 600 !important; transition: all 0.2s ease !important; border: none !important; }}
        .stButton > button[type="primary"] {{ background: linear-gradient(135deg, {accent}, #7b2cbf) !important; box-shadow: 0 4px 15px rgba(0,212,255,0.3) !important; }}
        .stButton > button[type="primary"]:hover {{ transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(0,212,255,0.4) !important; }}
        .history-item {{ background: {card_bg}; border: 1px solid {card_border}; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px; transition: all 0.2s ease; cursor: pointer; }}
        .history-item:hover {{ background: {accent}15; border-color: {accent}55; }}
        .history-title {{ font-size: 13px; font-weight: 600; color: {text_primary}; margin-bottom: 4px; }}
        .history-date {{ font-size: 11px; color: {text_secondary}; }}
    </style>
    <div class="animated-bg"></div>
    """

st.markdown(get_css(st.session_state.theme), unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 4. Utility Functions
# ──────────────────────────────────────────────
def check_api_status():
    try:
        resp = requests.get(f"{API_URL}/status", timeout=5)
        if resp.status_code == 200:
            st.session_state.api_status = "online"
            return True, resp.json()
        st.session_state.api_status = "degraded"
        return False, None
    except Exception:
        st.session_state.api_status = "offline"
        return False, None

def save_to_history(title, data, source="single"):
    st.session_state.history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": source, "title": title, "data": data,
    })

def render_listing_card(data, platform=None):
    title = data.get("product_title", "")
    bullets = data.get("description_bullets", data.get("product_description", []))
    keywords = data.get("seo_keywords", [])
    with st.container():
        st.markdown('<div class="product-card">', unsafe_allow_html=True)
        col_t, col_b = st.columns([4, 1])
        with col_t:
            st.markdown(f"### 📌 {title}")
        with col_b:
            if platform:
                st.markdown(f'<span class="platform-badge badge-{platform}">{platform.title()}</span>', unsafe_allow_html=True)
        st.markdown("**📝 Description Highlights:**")
        if bullets:
            bullet_html = "<ul class='bullet-list'>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>"
            st.markdown(bullet_html, unsafe_allow_html=True)
        else:
            st.info("No description bullets available.")
        st.markdown("**🔍 SEO Keywords:**")
        if keywords:
            st.markdown(" ".join(f'<span class="keyword-tag">{kw}</span>' for kw in keywords), unsafe_allow_html=True)
        else:
            st.info("No SEO keywords available.")
        col_dl, col_hist = st.columns([1, 1])
        with col_dl:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            st.download_button(label="📥 Download JSON", data=json_str, file_name=f"listing_{int(time.time())}.json", mime="application/json", use_container_width=True)
        with col_hist:
            if st.button("⭐ Save to History", key=f"hist_{int(time.time()*1000)}", use_container_width=True):
                save_to_history(title, data)
                st.success("Saved to history!")
        st.markdown("</div>", unsafe_allow_html=True)

def render_platform_preview(data):
    title = data.get("product_title", "")
    bullets = data.get("description_bullets", data.get("product_description", []))
    keywords = data.get("seo_keywords", [])
    st.markdown("#### 🌐 Platform-Specific Previews")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<span class="platform-badge badge-meesho">Meesho Style</span>', unsafe_allow_html=True)
        st.markdown(f"**{title[:60]}...**")
        for b in bullets[:2]:
            st.markdown(f"- {b[:80]}...")
        st.markdown(f"Tags: {', '.join(keywords[:3])}")
        st.markdown("</div>", unsafe_allow_html=True)
    with p2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<span class="platform-badge badge-amazon">Amazon Style</span>', unsafe_allow_html=True)
        st.markdown(f"**{title}**")
        for b in bullets[:3]:
            st.markdown(f"• {b[:80]}...")
        st.markdown(f"Search: {', '.join(keywords[:4])}")
        st.markdown("</div>", unsafe_allow_html=True)
    with p3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<span class="platform-badge badge-myntra">Myntra Style</span>', unsafe_allow_html=True)
        st.markdown(f"**{title[:55]}...**")
        if bullets:
            st.markdown(f"• {bullets[0][:90]}...")
        st.markdown(f"Keywords: {', '.join(keywords[:5])}")
        st.markdown("</div>", unsafe_allow_html=True)

def render_seo_insights(data):
    title = data.get("product_title", "")
    bullets = data.get("description_bullets", data.get("product_description", []))
    keywords = data.get("seo_keywords", [])
    st.markdown("#### 📊 SEO Insights & Optimization")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-card"><div class="stat-label">Title Length</div><div class="stat-value">{len(title)} chars</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card"><div class="stat-label">Bullet Count</div><div class="stat-value">{len(bullets)}</div></div>', unsafe_allow_html=True)
    with c3:
        total_bullet_chars = sum(len(b) for b in bullets)
        st.markdown(f'<div class="stat-card"><div class="stat-label">Description Length</div><div class="stat-value">{total_bullet_chars} chars</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-card"><div class="stat-label">Keyword Count</div><div class="stat-value">{len(keywords)}</div></div>', unsafe_allow_html=True)
    score = 0
    if 40 <= len(title) <= 80:
        score += 25
    if len(bullets) >= 3:
        score += 25
    if total_bullet_chars >= 150:
        score += 25
    if len(keywords) >= 5:
        score += 25
    st.progress(score / 100)
    st.caption(f"SEO Optimization Score: {score}/100")

# ──────────────────────────────────────────────
# 5. Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🌙" if st.session_state.theme == "dark" else "☀️", key="theme_btn", help="Toggle theme"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
    with col2:
        st.markdown(f"**{st.session_state.theme.title()}**")
    st.markdown("---")
    st.header("⚙️ System Diagnostics")
    is_online, status_data = check_api_status()
    status_color = "🟢" if is_online else "🔴"
    st.markdown(f"<div class='stat-card'><div class='stat-label'>Backend API</div><div class='stat-value'>{status_color} {'Online' if is_online else 'Offline'}</div></div>", unsafe_allow_html=True)
    if status_data:
        st.markdown(f"<div class='stat-card'><div class='stat-label'>Model</div><div class='stat-value'>{status_data.get('model', 'N/A')}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='stat-card'><div class='stat-label'>Framework</div><div class='stat-value'>{status_data.get('framework', 'N/A')}</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📚 Quick Stats")
    st.markdown(f"<div class='stat-card'><div class='stat-label'>History Entries</div><div class='stat-value'>{len(st.session_state.history)}</div></div>", unsafe_allow_html=True)
    if st.session_state.history:
        st.markdown("---")
        st.markdown("### 📜 Listing History")
        for i, entry in enumerate(reversed(st.session_state.history[-10:])):
            with st.expander(f"{entry['title'][:40]}...", expanded=False):
                st.markdown(f"<div class='history-date'>{entry['timestamp']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='history-title'>{entry['title']}</div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 6. Main Header
# ──────────────────────────────────────────────
st.markdown("# 🛍️ CatalogStream-AI Optimization Hub")
st.markdown("<p class='subtitle'>Production-Ready Transformation Pipeline for High-Conversion Marketplace Listings</p>", unsafe_allow_html=True)
st.markdown("---")

# ──────────────────────────────────────────────
# 7. Navigation Tabs
# ──────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["✨ Single Product Listing", "📦 Batch Product Listings", "📸 Image-to-Listing Studio", "📊 Dashboard & Analytics"])

# TAB 1: SINGLE ITEM STUDIO
with tab1:
    st.subheader("Single Product Attribute Ingestion")
    st.caption("Convert fragmented vendor text specifications into clear retail copy fields.")
    left_input, right_preview = st.columns([1, 1.2], gap="large")
    with left_input:
        st.markdown("#### 📥 Source Attributes")
        raw_specs = st.text_area("Enter Raw Apparel Specifications:", height=180,
            placeholder="e.g., Fabric: Premium Cotton, Pattern: Striped, Style: Casual Dress Shirt, Indigo Blue wash...",
            help="Provide any messy product characteristics, fabrics, fits, or styling details.", key="single_specs")
        platform_choice = st.selectbox("🎯 Target Platform", ["All Platforms", "Meesho", "Amazon", "Myntra"],
            help="Select the marketplace for platform-specific optimization.")
        st.markdown(f"<p class='subtitle'>Characters: {len(raw_specs)} / 500</p>", unsafe_allow_html=True)
        generate_action = st.button("🚀 Generate Optimized Listing", type="primary", use_container_width=True)
    with right_preview:
        st.markdown("#### 🌟 Live Retail Preview Card")
        if generate_action:
            if not raw_specs.strip():
                st.warning("⚠️ Please specify input characteristics before submitting request payloads.")
            else:
                with st.spinner("🧠 Processing through structural parser variables..."):
                    start_latency = time.time()
                    try:
                        response = requests.post(f"{API_URL}/generate-single", json={"raw_attributes": raw_specs}, timeout=60)
                        if response.status_code == 200:
                            data = response.json()
                            latency_score = round(time.time() - start_latency, 2)
                            st.toast(f"✅ Synchronized compilation completed in {latency_score}s!", icon="✅")
                            render_listing_card(data, platform_choice.lower() if platform_choice != "All Platforms" else None)
                            st.markdown("---")
                            render_platform_preview(data)
                            st.markdown("---")
                            render_seo_insights(data)
                        else:
                            st.error(f"Backend Server Failure: {response.status_code} - {response.text}")
                    except requests.exceptions.Timeout:
                        st.error("⏰ Request timed out. The backend may be processing a large request.")
                    except Exception as e:
                        st.error(f"Network connection error: {e}")
        else:
            st.info("💡 Supply baseline attribute items on the left side to observe structural processing.")

# TAB 2: BATCH INGESTION PIPELINE
with tab2:
    st.subheader("Bulk Manifest Data Stream")
    st.caption("Upload binary spreadsheet models or generic text files to parse your entire inventory stack simultaneously.")
    uploaded_file = st.file_uploader("📁 Upload CSV or Excel file containing specifications:", type=["csv", "xlsx"], key="batch_uploader")
    if uploaded_file is not None:
        try:
            with st.spinner("📊 Parsing uploaded file..."):
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                else:
                    df = pd.read_excel(uploaded_file, engine='openpyxl')
            st.success(f"✅ Successfully staged '{uploaded_file.name}' with {len(df)} inventory entries.")
            with st.expander("🔍 View Raw Processing File Preview", expanded=False):
                st.dataframe(df, use_container_width=True)
            if "raw_attributes" not in df.columns:
                st.error("❌ Key Validation Mismatch: Processing sheet must include a column titled exactly 'raw_attributes'.")
            else:
                st.markdown("#### 📈 Data Summary")
                s1, s2, s3 = st.columns(3)
                with s1:
                    st.markdown(f'<div class="stat-card"><div class="stat-label">Total Rows</div><div class="stat-value">{len(df)}</div></div>', unsafe_allow_html=True)
                with s2:
                    st.markdown(f'<div class="stat-card"><div class="stat-label">Columns</div><div class="stat-value">{len(df.columns)}</div></div>', unsafe_allow_html=True)
                with s3:
                    st.markdown(f'<div class="stat-card"><div class="stat-label">File Size</div><div class="stat-value">{round(uploaded_file.size / 1024, 1)} KB</div></div>', unsafe_allow_html=True)
                if st.button("🚀 Execute Concurrency Ingestion Run", type="primary", use_container_width=True):
                    batch_input = df["raw_attributes"].astype(str).tolist()
                    run_progress = st.progress(0)
                    state_lbl = st.empty()
                    state_lbl.text("🔄 Routing arrays through LangChain batch worker pools...")
                    run_progress.progress(10)
                    start_batch_timer = time.time()
                    try:
                        response = requests.post(f"{API_URL}/generate-batch", json={"raw_specs_list": batch_input}, timeout=300)
                        if response.status_code == 200:
                            results = response.json()
                            run_progress.progress(75)
                            df["Generated_Title"] = [item.get("product_title", "") for item in results]
                            desc_keys = ["description_bullets", "product_description"]
                            df["Generated_Description"] = ["; ".join(item.get(next((k for k in desc_keys if k in item), []), [])) for item in results]
                            df["Generated_SEO_Keywords"] = [", ".join(item.get("seo_keywords", [])) for item in results]
                            run_progress.progress(100)
                            elapsed = round(time.time() - start_batch_timer, 2)
                            state_lbl.text(f"✅ Batch sequence fully cataloged in {elapsed}s!")
                            st.markdown("#### 📊 Optimized Catalog Matrix Summary")
                            st.dataframe(df, use_container_width=True)
                            st.markdown("---")
                            st.markdown("#### 📥 Export Options")
                            e1, e2, e3 = st.columns(3)
                            with e1:
                                processed_csv = df.to_csv(index=False).encode('utf-8-sig')
                                st.download_button(label="📥 Download CSV Manifest", data=processed_csv, file_name="optimized_catalog_manifest.csv", mime="text/csv", use_container_width=True)
                            with e2:
                                processed_json = json.dumps(results, indent=2, ensure_ascii=False).encode('utf-8')
                                st.download_button(label="📥 Download JSON Manifest", data=processed_json, file_name="optimized_catalog_manifest.json", mime="application/json", use_container_width=True)
                            with e3:
                                excel_buffer = io.BytesIO()
                                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                    df.to_excel(writer, index=False, sheet_name="Catalog")
                                excel_buffer.seek(0)
                                st.download_button(label="📥 Download Excel Manifest", data=excel_buffer, file_name="optimized_catalog_manifest.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                        else:
                            st.error(f"API Execution Failure: {response.status_code} - {response.text}")
                            run_progress.empty()
                            state_lbl.empty()
                    except requests.exceptions.Timeout:
                        st.error("⏰ Batch request timed out. Try reducing the batch size.")
                        run_progress.empty()
                        state_lbl.empty()
                    except Exception as e:
                        st.error(f"An unexpected failure interrupted execution operations: {e}")
                        run_progress.empty()
                        state_lbl.empty()
        except Exception as file_read_err:
            st.error(f"File ingestion halted due to systemic reading error: {file_read_err}")

# TAB 3: IMAGE-TO-LISTING STUDIO
with tab3:
    st.subheader("Visual Inventory Onboarding Studio")
    st.caption("Upload a product photo to automatically extract optimized marketplace metadata via cloud vision models.")
    img_left, preview_right = st.columns([1, 1.2], gap="large")
    with img_left:
        st.markdown("#### 📥 Image Ingestion")
        uploaded_image = st.file_uploader("📷 Drag and drop or browse product photo:", type=["jpg", "jpeg", "png"], key="image_uploader")
        if uploaded_image is not None:
            img = Image.open(uploaded_image)
            st.image(img, caption=f"Uploaded Preview ({img.size[0]}×{img.size[1]})", use_container_width="stretch")
            file_size = round(len(uploaded_image.getvalue()) / 1024, 1)
            st.markdown(f"<p class='subtitle'>File size: {file_size} KB</p>", unsafe_allow_html=True)
            analyze_action = st.button("🚀 Extract & Optimize Listing From Image", type="primary", use_container_width=True)
    with preview_right:
        st.markdown("#### 🌟 Live Retail Card Preview")
        if uploaded_image is not None and 'analyze_action' in locals() and analyze_action:
            with st.spinner("🕵️‍♂️ Processing image features through cloud vision models..."):
                try:
                    file_payload = {"file": (uploaded_image.name, uploaded_image.getvalue(), uploaded_image.type)}
                    response = requests.post(f"{API_URL}/generate-image", files=file_payload, timeout=120)
                    if response.status_code == 200:
                        data = response.json()
                        st.success("🎉 Listing compiled successfully from visual data!")
                        render_listing_card(data)
                        st.markdown("---")
                        render_platform_preview(data)
                        st.markdown("---")
                        render_seo_insights(data)
                    else:
                        st.error(f"Vision Endpoint Error: {response.status_code} - {response.text}")
                except requests.exceptions.Timeout:
                    st.error("⏰ Image processing timed out. Try a smaller or lower-resolution image.")
                except Exception as network_err:
                    st.error(f"Failed to communicate with processing server network layer: {network_err}")
        else:
            st.info("💡 Drop a product photograph on the left panel and hit execute to extract marketplace fields.")

# TAB 4: DASHBOARD & ANALYTICS
with tab4:
    st.subheader("📊 Catalog Analytics Dashboard")
    st.caption("Monitor your listing generation performance and historical data.")
    if not st.session_state.history:
        st.info("💡 Generate some listings first to see analytics here!")
        st.markdown("""
        <div class="glass-card">
            <h4>Getting Started</h4>
            <ul>
                <li>Use the <strong>Single Product Listing</strong> tab to generate individual listings</li>
                <li>Use the <strong>Batch Product Listings</strong> tab to process multiple items at once</li>
                <li>Use the <strong>Image-to-Listing Studio</strong> to extract listings from product photos</li>
            </ul>
            <p>All generated listings are automatically saved to your history and will appear here.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        total = len(st.session_state.history)
        sources = {}
        for h in st.session_state.history:
            src = h["source"]
            sources[src] = sources.get(src, 0) + 1
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f'<div class="stat-card"><div class="stat-label">Total Listings</div><div class="stat-value">{total}</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="stat-card"><div class="stat-label">From Text</div><div class="stat-value">{sources.get("single", 0)}</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="stat-card"><div class="stat-label">From Batch</div><div class="stat-value">{sources.get("batch", 0)}</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="stat-card"><div class="stat-label">From Image</div><div class="stat-value">{sources.get("image", 0)}</div></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("#### 📜 All Generated Listings")
        history_df = pd.DataFrame([{"Timestamp": h["timestamp"], "Source": h["source"].title(), "Title": h["title"]} for h in reversed(st.session_state.history)])
        st.dataframe(history_df, use_container_width=True)
        st.markdown("---")
        st.markdown("#### 🔍 Detailed Listing Viewer")
        selected_idx = st.selectbox("Select a listing to view details:", options=list(range(len(st.session_state.history))),
            format_func=lambda i: st.session_state.history[len(st.session_state.history) - 1 - i]["title"][:50])
        if selected_idx is not None:
            actual_idx = len(st.session_state.history) - 1 - selected_idx
            selected = st.session_state.history[actual_idx]
            st.markdown(f"**Timestamp:** {selected['timestamp']} | **Source:** {selected['source']}")
            render_listing_card(selected["data"])
        st.markdown("---")
        if st.button("🗑️ Clear All History", type="secondary"):
            st.session_state.history = []
            st.rerun()

# ──────────────────────────────────────────────
# 8. Footer
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888; font-size: 12px;'>© 2024 CatalogStream-AI • Powered by LangChain • Groq Cloud Vision • Qwen2.5-7B</p>", unsafe_allow_html=True)
