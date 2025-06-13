import streamlit as st
from bs4 import BeautifulSoup
import requests
from googleapiclient.discovery import build
from googleapiclient import errors as googleapiclient_errors

# Move API keys to Streamlit secrets
if 'GOOGLE_API_KEYS' not in st.secrets:
    st.error("Missing API keys in secrets. Please add them in Streamlit Cloud.")
    GOOGLE_API_KEYS = []  # Empty list as fallback
else:
    GOOGLE_API_KEYS = st.secrets['GOOGLE_API_KEYS']

GOOGLE_CSE_ID = st.secrets.get('GOOGLE_CSE_ID', '310b42d4bee37464e')
current_key_index = 0

def get_next_api_key():
    global current_key_index
    if not GOOGLE_API_KEYS:
        return None
    key = GOOGLE_API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(GOOGLE_API_KEYS)
    return key

def search_google(query):
    try:
        api_key = get_next_api_key()
        if not api_key:
            return [{
                'quota_exceeded': True, 
                'snippet': 'API keys not configured or all keys exhausted'
            }]
        
        service = build('customsearch', 'v1', developerKey=api_key)
        result = service.cse().list(
            q=query,
            cx=GOOGLE_CSE_ID,
            num=10
        ).execute()
        
        return result.get('items', [])
        
    except googleapiclient_errors.HttpError as e:
        if 'quota' in str(e).lower():
            return [{
                'quota_exceeded': True,
                'snippet': 'Daily API quota exceeded'
            }]
        return [{
            'error': True,
            'snippet': f'API Error: {str(e)}'
        }]
    except Exception as e:
        return [{
            'error': True,
            'snippet': f'Unexpected error: {str(e)}'
        }]

@st.cache_data(ttl=3600)  # Cache results for 1 hour
def search_upcitemdb(barcode):
    try:
        url = f'https://www.upcitemdb.com/upc/{barcode}'
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        product_info = {}
        
        # Extract product details
        title = soup.find('h1', class_='product-name')
        if title:
            product_info['title'] = title.text.strip()
            
        brand = soup.find('span', class_='brand')
        if brand:
            product_info['brand'] = brand.text.strip()
            
        barcodes = soup.find_all('span', class_='upc-code')
        if barcodes:
            product_info['barcodes'] = [b.text.strip() for b in barcodes]
            
        variants = soup.find_all('div', class_='variant')
        if variants:
            product_info['variants'] = [v.text.strip() for v in variants]
            
        if product_info:
            results.append(product_info)
            
        return results
    except Exception as e:
        st.error(f"Error fetching UPC data: {str(e)}")
        return []

# Streamlit UI
st.set_page_config(page_title="Barcode Product Lookup", layout="wide")

st.title("Barcode Product Lookup")

# Input section with validation
barcode = st.text_input("Enter barcode number")
if barcode and not barcode.isdigit():
    st.warning("Please enter only numbers for the barcode")

if st.button("Search") and barcode and barcode.isdigit():
    if barcode:
        with st.spinner("Searching..."):
            # Search UPCItemDB
            upcitemdb_results = search_upcitemdb(barcode)
            
            # Create two columns for results
            col1, col2 = st.columns(2)
            
            # UPCItemDB Results
            with col1:
                st.subheader("UPCItemDB Results")
                if upcitemdb_results:
                    for product in upcitemdb_results:
                        if 'variants' in product:
                            st.markdown("**Product Variants:**")
                            for variant in product['variants']:
                                st.markdown(f"- {variant}")
                        
                        if 'brand' in product:
                            st.markdown(f"**Brand:** {product['brand']}")
                        
                        if 'barcodes' in product:
                            st.markdown("**Barcodes:**")
                            for barcode in product['barcodes']:
                                st.markdown(f"- {barcode}")
                        
                        st.markdown("---")
                else:
                    st.info("No results found in UPCItemDB")
            
            # Google Search Results
            with col2:
                st.subheader("Google Search Results")
                if upcitemdb_results:  # Only search Google if UPCItemDB has results
                    google_results = search_google(barcode)
                    if google_results:
                        for result in google_results:
                            if not result.get('quota_exceeded'):
                                domain = result['link'].split('/')[2].replace('www.', '')
                                st.markdown(f"**{domain}**")
                                st.markdown(f"[{result['title']}]({result['link']})")
                                st.markdown("---")
                            else:
                                st.warning(result['snippet'])
                    else:
                        st.info("No Google results found")
    else:
        st.error("Please enter a barcode")