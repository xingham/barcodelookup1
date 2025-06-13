import streamlit as st
from googleapiclient.discovery import build
from googleapiclient import errors as googleapiclient_errors
from bs4 import BeautifulSoup
import requests

# Initialize session state for API key rotation
if 'current_key_index' not in st.session_state:
    st.session_state.current_key_index = 0

# Configure page
st.set_page_config(page_title="Barcode Product Lookup", layout="wide")

# Debug mode
DEBUG = True

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
        
        if DEBUG:
            st.sidebar.write(f"Searching UPC: {barcode}")
            
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        products = []
        product_info = {}
        
        # Try to find product name
        title = soup.find('h1', class_='product-name')
        if title:
            product_info['title'] = title.text.strip()
            if DEBUG:
                st.sidebar.write(f"Found title: {product_info['title']}")
        
        # Try to find product details
        details = soup.find('div', class_='product-meta')
        if details:
            # Extract brand
            brand = details.find('span', class_='brand')
            if brand:
                product_info['brand'] = brand.text.strip()
            
            # Extract description
            desc = details.find('div', class_='note')
            if desc:
                product_info['description'] = desc.text.strip()
        
        # Extract product details from table
        details_table = soup.find('table', class_='detail-list')
        if details_table:
            rows = details_table.find_all('tr')
            for row in rows:
                cols = row.find_all(['th', 'td'])
                if len(cols) == 2:
                    key = cols[0].text.strip()
                    value = cols[1].text.strip()
                    if key and value:
                        product_info[key.lower()] = value
        
        if product_info:
            products.append(product_info)
            if DEBUG:
                st.sidebar.success("Found product information")
                st.sidebar.write(product_info)
        
        return products
        
    except requests.RequestException as e:
        if DEBUG:
            st.sidebar.error(f"Request failed: {str(e)}")
        return []
    except Exception as e:
        if DEBUG:
            st.sidebar.error(f"Error: {str(e)}")
        return []

def search_google(query):
    try:
        api_key = get_next_api_key()
        if not api_key:
            if DEBUG:
                st.sidebar.error("No API key available")
            return []
        
        service = build('customsearch', 'v1', developerKey=api_key)
        result = service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=10).execute()
        
        if DEBUG:
            st.sidebar.write(f"Google API Response: {len(result.get('items', []))} results")
        
        return result.get('items', [])
    except Exception as e:
        if DEBUG:
            st.sidebar.error(f"Google Search Error: {str(e)}")
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
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("UPC Database Results")
            upc_results = search_upcitemdb(barcode)
            if upc_results:
                for item in upc_results:
                    st.write("---")
                    if 'title' in item:
                        st.markdown(f"**Product:** {item['title']}")
                    if 'description' in item:
                        st.markdown(f"**Description:** {item['description']}")
            else:
                st.info("No UPC results found")
        
        with col2:
            st.subheader("Google Search Results")
            google_results = search_google(barcode)
            if google_results:
                for item in google_results:
                    st.write("---")
                    st.markdown(f"**[{item.get('title', 'No title')}]({item.get('link', '#')})**")
            else:
                st.info("No Google results found")