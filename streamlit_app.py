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
            return cached_results

        api_key = get_next_api_key()
        if not api_key:
            if DEBUG:
                st.sidebar.error("No API key available")
            return []
        
        service = build('customsearch', 'v1', developerKey=api_key)
        
        # Simplify search query first for debugging
        simple_query = f"{query}"
        
        if DEBUG:
            st.sidebar.write(f"Using API Key: {api_key[:5]}...")
            st.sidebar.write(f"Search Query: {simple_query}")
        
        try:
            # Test API with simple query first
            result = service.cse().list(
                q=simple_query,
                cx=GOOGLE_CSE_ID,
                num=10
            ).execute()
            
            if DEBUG:
                st.sidebar.write(f"Raw API Response Keys: {result.keys()}")
                st.sidebar.write(f"Total Results: {result.get('searchInformation', {}).get('totalResults', 0)}")
            
            # If simple query works, try full search
            priority_sites = [
                "site:walmart.com",
                "site:target.com",
                "site:bestbuy.com",
                "site:kroger.com",
                "site:amazon.com",
                "site:barcodespider.com"
            ]
            
            sites_query = " OR ".join(priority_sites)
            kroger_upc = '0' + query[:-1]
            full_query = f"({query} OR {kroger_upc}) ({sites_query})"
            
            if DEBUG:
                st.sidebar.write(f"Full Query: {full_query}")
            
            result = service.cse().list(
                q=full_query,
                cx=GOOGLE_CSE_ID,
                num=10,
                cr="countryUS"
            ).execute()
            
            if 'items' not in result:
                if DEBUG:
                    st.sidebar.warning("No items found in response")
                    st.sidebar.write("Response:", result)
                return []
            
            filtered_results = []
            if 'items' in result:
                for item in result['items']:
                    link = item.get('link', '').lower()
                    title = item.get('title', '')
                    
                    # Clean up title
                    for suffix in [' | Walmart', ' : Target', ' - Best Buy', ' @ Amazon.com']:
                        title = title.replace(suffix, '')
                    
                    filtered_results.append({
                        'title': title,
                        'link': item.get('link', ''),
                        'description': item.get('snippet', ''),
                        'source': 'Google'
                    })

            # Save all results before sorting
            if filtered_results:
                save_search_results(query, filtered_results)

            # Categorize results
            def categorize_result(link):
                link = link.lower()
                # Brick and mortar stores
                if any(store in link for store in ['walmart.com', 'target.com', 'bestbuy.com', 'kroger.com']):
                    return 1, "brick_and_mortar"
                # Online marketplaces
                elif 'amazon.com' in link:
                    return 2, "marketplace"
                # Barcode databases
                elif 'barcodespider.com' in link:
                    return 3, "database"
                # Other sites
                return 4, "other"

            # Sort results by category and then by specific retailer
            def get_sort_key(item):
                link = item.get('link', '').lower()
                category_priority, category = categorize_result(link)
                
                # Retailer-specific priority within categories
                retailer_priority = {
                    'walmart.com': 1,
                    'target.com': 2,
                    'bestbuy.com': 3,
                    'kroger.com': 4,
                    'amazon.com': 1,  # Top priority in marketplace category
                    'barcodespider.com': 1  # Top priority in database category
                }
                
                for retailer, priority in retailer_priority.items():
                    if retailer in link:
                        return category_priority, priority
                        
                return category_priority, 999

            # Sort the results
            filtered_results.sort(key=get_sort_key)
            return filtered_results

        except googleapiclient_errors.HttpError as api_error:
            if DEBUG:
                st.sidebar.error(f"API Error: {str(api_error)}")
            if 'quota' in str(api_error).lower():
                st.warning("Search quota exceeded. Please try again later.")
            return []
            
    except Exception as e:
        if DEBUG:
            st.sidebar.error(f"Search Error: {str(e)}")
            import traceback
            st.sidebar.code(traceback.format_exc())
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
        col1, col2 = st.columns(2, gap="small")
        
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
                        st.markdown("**Variants:**")
                        for variant in item['variants']:
                            st.write(f"- {variant}")
            else:
                st.info("No UPC results found")

        # Second column - Google Search Results
        with col2:
            st.subheader("Google Search Results")
            google_results = search_google(barcode)
            if google_results:
                current_category = None
                for item in google_results:
                    link = item.get('link', '').lower()
                    
                    # Determine category for display
                    if any(store in link for store in ['walmart.com', 'target.com', 'bestbuy.com', 'kroger.com']):
                        category = "Retail Stores"
                    elif 'amazon.com' in link:
                        category = "Online Marketplaces"
                    elif 'barcodespider.com' in link:
                        category = "Product Databases"
                    else:
                        category = "Other Sources"
                        
                    # Show category header if changed
                    if category != current_category:
                        if current_category is not None:
                            st.write("---")
                        st.markdown(f"### {category}")
                        current_category = category
                    
                    # Display result with minimal spacing
                    title = item.get('title', 'No title')
                    retailer = next(
                        (name.replace('.com', '').title() for name in 
                         ['walmart.com', 'target.com', 'bestbuy.com', 'kroger.com', 
                          'amazon.com', 'barcodespider.com'] 
                         if name in link.lower()),
                        "Other"
                    )
                    st.markdown(f"**{retailer}:** [{title}]({link})")
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