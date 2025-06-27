import streamlit as st
from googleapiclient.discovery import build
from googleapiclient import errors as googleapiclient_errors
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import json
import os

# Initialize session state for API key rotation
if 'current_key_index' not in st.session_state:
    st.session_state.current_key_index = 0

# Configure page with custom styling
st.set_page_config(page_title="Barcode Product Lookup", layout="wide")

# Add custom CSS
st.markdown("""
    <style>
        /* Main page background */
        .stApp {
            background-color: #ffffcc;  /* pastel yellow */
        }
        
        /* Purple background for results columns */
        [data-testid="column"] {
            background-color: #e6e6fa;  /* light purple */
            padding: 20px;
            border-radius: 10px;
            margin: 10px;
        }
        
        /* Make all text elements dark purple */
        .stMarkdown, .stSubheader, .stTitle, h1, h2, h3, p, span, div {
            color: #4B0082 !important;  /* indigo/dark purple */
        }
        
        /* Style headers specifically */
        .stHeadingContainer {
            color: #4B0082 !important;
        }
        
        /* Make warning and info messages dark purple */
        .stWarning, .stInfo, .stSuccess {
            color: #4B0082 !important;
        }
        
        /* Style footer text */
        .footer {
            color: #4B0082 !important;
        }
        
        /* Style input text to be white */
        .stTextInput input {
            color: white !important;
        }
        
        /* Make all button text white */
        button, .stButton > button, [data-testid="baseButton-secondary"] {
            color: white !important;
        }
        
        /* Style all button text elements to be white */
        button p, button span, button div, 
        .stButton button p, .stButton button span, .stButton button div,
        [data-testid="baseButton-secondary"] p,
        [data-testid="baseButton-secondary"] span,
        [data-testid="baseButton-secondary"] div {
            color: white !important;
        }
        
        /* Target menu buttons specifically */
        [data-testid="MenuButton"] span, 
        [data-testid="SettingsButton"] span,
        [data-testid="ShareButton"] span,
        [data-testid="rerunButton"] span {
            color: white !important;
        }
        
        /* Target any nested elements in buttons */
        button *, .stButton button *, [data-testid="baseButton-secondary"] * {
            color: white !important;
        }
        
        /* Make all menu button text white */
        [data-testid="StyledFullScreenButton"], 
        [data-testid="menuButton"],
        [data-baseweb="button"],
        button[kind="minimal"] {
            color: white !important;
        }
        
        /* Target the three dots menu button and its contents */
        .stDeployButton span,
        .stDeployButton svg,
        [data-testid="StyledFullScreenButton"] span,
        [data-testid="StyledFullScreenButton"] svg,
        [data-testid="menuButton"] span,
        [data-testid="menuButton"] svg {
            color: white !important;
            fill: white !important;
        }
        
        /* Target dropdown menu items */
        [data-baseweb="menu"] li,
        [data-baseweb="menu"] span,
        [data-baseweb="menu"] svg {
            color: white !important;
        }
        
        /* Reduce spacing between headers and content */
        .stMarkdown h1 {
            margin-bottom: 0.5rem !important;
        }
        .stMarkdown h2 {
            margin-bottom: 0.3rem !important;
        }
        .stMarkdown h3 {
            margin-bottom: 0.2rem !important;
            margin-top: 0.5rem !important;
        }
        
        /* Reduce spacing between dividers */
        hr {
            margin: 0.5rem 0 !important;
        }
        
        /* Adjust column padding */
        [data-testid="column"] {
            padding: 10px !important;
        }
        
        /* Make columns equal width and height */
        .stColumns [data-testid="column"] {
            width: 50% !important;
            flex: 1 1 50% !important;
        }
        
        /* Reduce spacing between items */
        .stMarkdown p {
            margin-bottom: 0.2rem !important;
        }

        /* Column styling */
        .stColumns {
            gap: 1rem !important;
        }
        
        [data-testid="column"] {
            background-color: #e6e6fa;
            border-radius: 10px;
            padding: 1rem !important;
            min-width: 45% !important;
            margin: 0 !important;
        }
        
        /* Force equal width columns */
        .row-widget.stColumns {
            display: flex !important;
            flex-direction: row !important;
            justify-content: space-between !important;
            align-items: stretch !important;
        }
        
        /* Remove any default margins that might cause spacing */
        .block-container {
            padding: 2rem 1rem !important;
            max-width: 100% !important;
        }
        
        /* Ensure content fills column width */
        [data-testid="column"] > div {
            width: 100% !important;
        }

        /* Remove extra spacing from markdown elements */
        .stMarkdown {
            margin: 0 !important;
        }
        
        /* Adjust subheader spacing */
        .stSubheader {
            margin-bottom: 0.5rem !important;
        }
        
        /* Category header styles */
        .category-header-main {
            font-size: 1.2em !important;
            font-weight: bold !important;
            margin-bottom: 0.3rem !important;
            color: #4B0082 !important;
        }
        
        .category-header-secondary {
            font-size: 1.2em !important;  /* Changed from 0.9em to match main */
            font-weight: bold !important;
            margin-bottom: 0.3rem !important;  /* Changed to match main */
            color: #4B0082 !important;
        }
        
        /* Add style for variants header */
        .variants-header {
            font-size: 1.2em !important;
            font-weight: bold !important;
            margin-bottom: 0.3rem !important;
            color: #4B0082 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Debug mode - set to False to remove sidebar output
DEBUG = False

# Load API keys from secrets with debug info
try:
    GOOGLE_API_KEYS = st.secrets["GOOGLE_API_KEYS"]
    GOOGLE_CSE_ID = st.secrets["GOOGLE_CSE_ID"]
    if DEBUG:
        st.sidebar.write("API Keys loaded successfully")
except Exception as e:
    st.error(f"Error loading API keys from secrets: {str(e)}")
    if DEBUG:
        st.sidebar.write(f"Secret loading error: {str(e)}")
    st.stop()

def get_next_api_key():
    if not GOOGLE_API_KEYS:
        return None
    key = GOOGLE_API_KEYS[st.session_state.current_key_index]
    st.session_state.current_key_index = (st.session_state.current_key_index + 1) % len(GOOGLE_API_KEYS)
    return key

@st.cache_data(ttl=3600)
def search_upcitemdb(barcode):
    try:
        url = f'https://www.upcitemdb.com/upc/{barcode}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }
            
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        products = []
        product_info = {}

        # Look for variants in the ordered list
        variants_list = soup.select('ol.num li')
        if variants_list:
            variants = []
            for variant in variants_list:
                text = variant.get_text(strip=True)
                if text:
                    variants.append(text)
                    if not product_info.get('title'):
                        product_info['title'] = text
            
            if variants:
                product_info['variants'] = variants

        if product_info:
            products.append(product_info)
            
        return products
        
    except Exception as e:
        return []

def save_search_results(barcode, results):
    """Save search results to a JSON file"""
    cache_dir = "search_cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        
    cache_file = os.path.join(cache_dir, f"{barcode}.json")
    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "results": results
    }
    
    with open(cache_file, "w") as f:
        json.dump(cache_data, f)

def get_cached_results(barcode):
    """Get cached results if they exist"""
    cache_file = os.path.join("search_cache", f"{barcode}.json")
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f)["results"]
    return None

def search_google(query):
    try:
        # Check cache first
        cached_results = get_cached_results(query)
        if cached_results:
            if DEBUG:
                st.sidebar.info("Using cached results")
            return [r for r in cached_results if not any(site in r.get('link', '').lower() 
                   for site in ['barcodespider.com', 'github.com'])]

        api_key = get_next_api_key()
        if not api_key:
            if DEBUG:
                st.sidebar.error("No API key available")
            return []
        
        service = build('customsearch', 'v1', developerKey=api_key)
        
        # Simple exact match query with exclusions
        search_query = f'"{query}" -site:barcodespider.com -site:github.com -site:gist.github.com'
        
        if DEBUG:
            st.sidebar.write(f"Search Query: {search_query}")
        
        # Make single API call
        result = service.cse().list(
            q=search_query,
            cx=GOOGLE_CSE_ID,
            num=20,
            cr="countryUS",
            exactTerms=query
        ).execute()
        
        filtered_results = []
        if 'items' in result:
            for item in result['items']:
                link = item.get('link', '').lower()
                title = item.get('title', '')
                
                # Only exclude barcodespider and github
                if any(site in link for site in ['barcodespider.com', 'github.com']):
                    continue
                
                # Clean up title
                for suffix in [' | Walmart', ' : Target', ' - Best Buy', ' @ Amazon.com']:
                    title = title.replace(suffix, '')
                
                filtered_results.append({
                    'title': title,
                    'link': item.get('link', ''),
                    'description': item.get('snippet', ''),
                    'source': 'Google'
                })

        if filtered_results:
            save_search_results(query, filtered_results)
        
        return filtered_results

    except Exception as e:
        if DEBUG:
            st.sidebar.error(f"Search Error: {str(e)}")
        return []

# Main UI
st.title("Barcode Product Lookup")

# Input with immediate validation
barcode = st.text_input("Enter barcode number")
if barcode:
    if not barcode.isdigit():
        st.warning("Please enter only numbers for the barcode")
    elif len(barcode) < 8:
        st.warning("Barcode must be at least 8 digits")
    else:
        st.success("Valid barcode entered")

# Search button with progress indicators
if st.button("Search") and barcode and barcode.isdigit():
    with st.spinner("Searching databases..."):
        # Create two equal columns
        col1, col2 = st.columns([1, 1])  # Equal width columns
        
        # First column - UPCItemDB Results
        with col1:
            st.subheader("UPCItemDB")
            upc_results = search_upcitemdb(barcode)
            if upc_results:
                for item in upc_results:
                    st.write("---")
                    upc_link = f"https://www.upcitemdb.com/upc/{barcode}"
                    if 'title' in item:
                        st.markdown(f"**Product:** [{item['title']}]({upc_link})")
                    if 'variants' in item:
                        st.markdown("<div class='variants-header'>Variants:</div>", unsafe_allow_html=True)
                        for variant in item['variants']:
                            st.write(f"- {variant}")
            else:
                st.info("No UPC results found")

        # Second column - Google Search Results
        with col2:
            st.subheader("Google Search Results")
            google_results = search_google(barcode)
            if google_results:
                for item in google_results:
                    st.write("---")
                    title = item.get('title', 'No title')
                    link = item.get('link', '#')
                    st.markdown(f"[{title}]({link})")
            else:
                st.info("No Google results found")

# Add footer with custom styling
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; padding: 20px;'>"
    "Brought to you by UPC Me Rollin'"
    "</div>", 
    unsafe_allow_html=True
)