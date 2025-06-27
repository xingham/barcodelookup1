import streamlit as st
from googleapiclient.discovery import build
from googleapiclient import errors as googleapiclient_errors
from bs4 import BeautifulSoup
import requests

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

def search_google(query):
    try:
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
            for item in result['items']:
                link = item.get('link', '').lower()
                title = item.get('title', '')
                
                # Clean up title
                for suffix in [' | Walmart', ' : Target', ' - Best Buy', ' @ Amazon.com']:
                    title = title.replace(suffix, '')
                
                filtered_results.append({
                    'title': title,
                    'link': item.get('link', ''),
                    'description': item.get('snippet', '')
                })
            
            # Sort results
            filtered_results.sort(
                key=lambda x: next(
                    (i for i, site in enumerate(['walmart.com', 'target.com', 'bestbuy.com', 
                                                 'kroger.com', 'amazon.com', 'barcodespider.com']) 
                     if site in x['link'].lower()), 
                    999
                )
            )
            
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
        # Create container for results
        results_container = st.container()
        
        # Use columns inside the container
        with results_container:
            col1, col2 = st.columns(2)
            
            # First column - UPC Database Results
            with col1:
                st.subheader("UPC Database Results")
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
                                st.markdown(f"- {variant}")
                else:
                    st.info("No UPC results found")

            # Second column - Google Search Results
            with col2:
                st.subheader("Google Search Results")
                google_results = search_google(barcode)
                if google_results:
                    # Sort results by retailer priority
                    def get_retailer_priority(link):
                        """Return a tuple of (priority, retailer_name) for sorting"""
                        link = link.lower()
                        if 'walmart.com' in link:
                            return (1, "Walmart")
                        elif 'target.com' in link:
                            return (2, "Target")
                        elif 'bestbuy.com' in link:
                            return (3, "Best Buy")
                        elif 'kroger.com' in link:
                            return (4, "Kroger")  # Add Kroger
                        elif 'amazon.com' in link:
                            return (5, "Amazon")
                        elif 'barcodespider.com' in link:
                            return (6, "Barcode Spider")
                        else:
                            from urllib.parse import urlparse
                            domain = urlparse(link).netloc.replace('www.', '')
                            return (7, domain.split('.')[0].title())

                    sorted_results = sorted(google_results, 
                                          key=lambda x: get_retailer_priority(x.get('link', '')))
                    
                    for item in sorted_results:
                        st.write("---")
                        title = item.get('title', 'No title')
                        link = item.get('link', '#')
                        priority, retailer = get_retailer_priority(link)
                        
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