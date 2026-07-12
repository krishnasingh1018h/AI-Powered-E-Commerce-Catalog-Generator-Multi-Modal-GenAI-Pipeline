import streamlit as st
import requests
import pandas as pd
import time

# 1. Page Configuration & Elegant E-Commerce Styling Layouts
st.set_page_config(page_title="CatalogStream-AI Portal", page_icon="🛍️", layout="wide")

st.markdown("""
    <style>
    .metric-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 12px;
    }
    .product-preview-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #eaeaea;
    }
    </style>
""", unsafe_allow_html=True)

# Centralizing API Address Routing
API_URL = "http://127.0.0.1:8000"

st.markdown("# 🛍️ CatalogStream-AI Optimization Hub")
st.markdown("##### Production-Ready Transformation Pipeline for High-Conversion Marketplace Listings")
st.markdown("---")

# Left Structural Sidebar Status Counters
with st.sidebar:
    st.header("⚙️ System Diagnostics")
    st.markdown("<div class='metric-container'><strong>Core Model:</strong> Qwen2.5-7B-Instruct</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-container'><strong>API Channel:</strong> Active (Port 8000)</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-container'><strong>Optimization Targets:</strong> Meesho / Amazon / Myntra</div>", unsafe_allow_html=True)

# Instantiating Navigation Tabs
tab1, tab2, tab3 = st.tabs(["✨ Single Product Listing", "📦 Batch Product Listings", "📸 Image-to-Listing Studio"])# ==========================================
# TAB 1: SINGLE ITEM STUDIO
# ==========================================
with tab1:
    st.subheader("Single Product Attribute Ingestion")
    st.caption("Convert fragmented vendor text specifications into clear retail copy fields.")
    
    # 50/50 Screen Layout Distribution
    left_input, right_preview = st.columns([1, 1.2], gap="large")
    
    with left_input:
        st.markdown("#### 📥 Source Attributes")
        raw_specs = st.text_area(
            "Enter Raw Apparel Specifications:", 
            height=180, 
            placeholder="e.g., Fabric: Premium Cotton, Pattern: Striped, Style: Casual Dress Shirt, Indigo Blue wash...",
            help="Provide any messy product characteristics, fabrics, fits, or styling details."
        )
        
        generate_action = st.button("Generate Optimized Listing", type="primary", use_container_width=True)

    with right_preview:
        st.markdown("#### 🌟 Live Retail Preview Card")
        
        if generate_action:
            if not raw_specs.strip():
                st.error("⚠️ Please specify input characteristics before submitting request payloads.")
            else:
                with st.spinner("Processing through structural parser variables..."):
                    start_latency = time.time()
                    try:
                        response = requests.post(f"{API_URL}/generate-single", json={"raw_attributes": raw_specs})
                        
                        if response.status_code == 200:
                            data = response.json()
                            latency_score = round(time.time() - start_input, 2) if 'start_input' in locals() else round(time.time() - start_latency, 2)
                            
                            st.toast(f"Synchronized compilation completed in {latency_score}s!", icon="✅")
                            
                            # Interactive Card Container
                            with st.container():
                                st.markdown("<div class='product-preview-card'>", unsafe_allow_html=True)
                                
                                st.markdown("**📌 SEO Optimized Title:**")
                                st.text_input("Title Display", value=data.get("product_title", ""), label_visibility="collapsed")
                                
                                # Dynamic handling for alternate schema response key matches
                                bullets_list = data.get("description_bullets", data.get("product_description", []))
                                
                                st.markdown("**📝 Click-Ready Description Highlights:**")
                                for i, bullet in enumerate(bullets_list[:3]):
                                    st.text_input(f"Highlight Feature {i+1}", value=bullet)
                                    
                                st.markdown("**🔍 Top Indexing Keyword Targets:**")
                                st.write(" , ".join([f"`{kw}`" for kw in data.get("seo_keywords", [])]))
                                
                                st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.error(f"Backend Server Failure: {response.status_code} - {response.text}")
                    except Exception as e:
                        st.error(f"Network tracking link connection lost: {e}")
        else:
            st.info("💡 Supply baseline attribute items on the left side to observe structural processing.")

# ==========================================
# TAB 2: BATCH INGESTION PIPELINE
# ==========================================
with tab2:
    st.subheader("Bulk Manifest Data Stream")
    st.caption("Upload binary spreadsheet models or generic text files to parse your entire inventory stack simultaneously.")
    
    uploaded_file = st.file_uploader("Upload CSV or Excel file containing specifications:", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            else:
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            st.success(f"Successfully staged '{uploaded_file.name}' with {len(df)} inventory entries.")
            
            with st.expander("🔍 View Raw Processing File Preview", expanded=False):
                st.dataframe(df, use_container_width=True)
            
            if "raw_attributes" not in df.columns:
                st.error("❌ Key Validation Mismatch: Processing sheet must include a column titled exactly 'raw_attributes'.")
            else:
                if st.button("Execute Concurrency Ingestion Run", type="primary", use_container_width=True):
                    batch_input = df["raw_attributes"].astype(str).tolist()
                    
                    # Modern Progress Management Interface
                    run_progress = st.progress(0)
                    state_lbl = st.empty()
                    
                    state_lbl.text("Routing arrays through LangChain batch worker pools...")
                    run_progress.progress(25)
                    
                    start_batch_timer = time.time()
                    try:
                        # FIXED: This now maps exactly to the request schema payload key expected by your API
                        response = requests.post(f"{API_URL}/generate-batch", json={"raw_specs_list": batch_input})
                        
                        if response.status_code == 200:
                            results = response.json()
                            run_progress.progress(75)
                            
                            # Clean array unpacking matching either schema variant safely
                            df["Generated_Title"] = [item.get("product_title", "") for item in results]
                            
                            # Safely capture description arrays regardless of key variances
                            desc_keys = ["description_bullets", "product_description"]
                            df["Generated_Description"] = [
                                "; ".join(item.get(next((k for k in desc_keys if k in item), []), [])) 
                                for item in results
                            ]
                            
                            df["Generated_SEO_Keywords"] = [", ".join(item.get("seo_keywords", [])) for item in results]
                            
                            run_progress.progress(100)
                            state_lbl.text(f"Batch sequence fully cataloged in {round(time.time() - start_batch_timer, 2)}s!")
                            
                            st.markdown("#### 📊 Optimized Catalog Matrix Summary")
                            st.dataframe(df, use_container_width=True)
                            
                            # Clean UTF-8-sig export wrapper block
                            processed_file = df.to_csv(index=False).encode('utf-8-sig')
                            st.download_button(
                                label="📥 Download Compiled Catalog CSV Manifest",
                                data=processed_file,
                                file_name="optimized_catalog_manifest.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        else:
                            st.error(f"API Execution Failure: {response.status_code} - {response.text}")
                            run_progress.empty()
                            state_lbl.empty()
                    except Exception as e:
                        st.error(f"An unexpected failure interrupted execution operations: {e}")
                        run_progress.empty()
                        state_lbl.empty()
                        
        except Exception as file_read_err:
            st.error(f"File ingestion halted due to systemic reading error: {file_read_err}")

# ==========================================
# TAB 3: IMAGE-TO-LISTING STUDIO
# ==========================================
with tab3:
    st.header("Visual Inventory Onboarding Studio")
    st.caption("Upload a product photo to automatically extract optimized marketplace metadata via Hugging Face Inference.")
    
    img_left, preview_right = st.columns([1, 1.2], gap="large")
    
    with img_left:
        st.markdown("#### 📥 Image Ingestion")
        uploaded_image = st.file_uploader("Drag and drop or browse product photo:", type=["jpg", "jpeg", "png"])
        
        if uploaded_image is not None:
            st.image(uploaded_image, caption="Uploaded Sample Preview", width="stretch")
            analyze_action = st.button("Extract & Optimize Listing From Image", type="primary", width="stretch")            
    with preview_right:
        st.markdown("#### 🌟 Live Retail Card Preview")
        
        if uploaded_image is not None and 'analyze_action' in locals() and analyze_action:
            with st.spinner("🕵️‍♂️ Processing image features through cloud vision models..."):
                try:
                    # Package binary upload stream into multi-part payload format
                    file_payload = {
                        "file": (uploaded_image.name, uploaded_image.getvalue(), uploaded_image.type)
                    }
                    
                    # Point to your local network loopback address directly
                    response = requests.post(f"{API_URL}/generate-image", files=file_payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success("🎉 Listing compiled successfully from visual data!")
                        
                        with st.container():
                            st.markdown("<div class='product-preview-card'>", unsafe_allow_html=True)
                            
                            st.markdown("**📌 Vision-Derived Product Title:**")
                            st.text_input("Img Title Field", value=data.get("product_title", ""), label_visibility="collapsed")
                            
                            bullets_list = data.get("description_bullets", data.get("product_description", []))
                            
                            st.markdown("**📝 Material & Architectural Highlights:**")
                            for i, bullet in enumerate(bullets_list[:3]):
                                st.text_input(f"Image Aspect Highlight {i+1}", value=bullet)
                                
                            st.markdown("**🔍 High-Volume Search Keywords:**")
                            st.write(" , ".join([f"`{kw}`" for kw in data.get("seo_keywords", [])]))
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.error(f"Vision Endpoint Error: {response.status_code} - {response.text}")
                except Exception as network_err:
                    st.error(f"Failed to communicate with processing server network layer: {network_err}")
        else:
            st.info("💡 Drop a product photograph on the left panel and hit execute to extract marketplace fields.")