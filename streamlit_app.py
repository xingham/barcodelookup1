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
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.upcitemdb.com/',
            'Connection': 'keep-alive'
        }
        
        if DEBUG:
            st.sidebar.write(f"Fetching UPC data for: {barcode}")
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        if DEBUG:
            st.sidebar.write(f"UPC Response Status: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        product_info = {}
        
        # Try multiple selectors for product title
        title = (
            soup.find('h1', class_='product-name') or 
            soup.find('h1', {'itemprop': 'name'}) or
            soup.find('div', class_='product-title')
        )
        
        if title:
            product_info['title'] = title.text.strip()
            if DEBUG:
                st.sidebar.write(f"Found title: {product_info['title']}")
        
        # Try to find product details table
        details_table = soup.find('table', class_='detail-table')
        if details_table:
            rows = details_table.find_all('tr')
            for row in rows:
                cols = row.find_all(['th', 'td'])
                if len(cols) == 2:
                    key = cols[0].text.strip().lower()
                    value = cols[1].text.strip()
                    product_info[key] = value
        
        # Look for description
        description = (
            soup.find('div', class_='detail-description') or
            soup.find('div', {'itemprop': 'description'}) or
            soup.find('div', class_='product-description')
        )
        
        if description:
            product_info['description'] = description.text.strip()
        
        if product_info:
            results.append(product_info)
            if DEBUG:
                st.sidebar.success("Product information found!")
                st.sidebar.write(product_info)
        else:
            if DEBUG:
                st.sidebar.warning("No product info found in HTML")
                # Save HTML for debugging
                with open('debug_response.html', 'w') as f:
                    f.write(response.text)
        
        return results
    except requests.RequestException as e:
        if DEBUG:
            st.sidebar.error(f"Request Error: {str(e)}")
        return []
    except Exception as e:
        if DEBUG:
            st.sidebar.error(f"General Error: {str(e)}")
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