import streamlit as st
from bs4 import BeautifulSoup
import requests
from googleapiclient.discovery import build
from googleapiclient import errors as googleapiclient_errors

# Copy existing API configuration
GOOGLE_API_KEYS = [
    'AIzaSyDJw29dPJH7sioK4bqUo-g0VGlfVXeJHso',  # first project
    'AIzaSyCZf5f-9rIW0hm6BoykbHMo_0XkqCEp-jY',  # second project
    'AIzaSyBt-AH09r8dGcdWARB-u631khJXC8Cxvw4',  # third project
    'AIzaSyBGlB4Ro1uGyfIcE7Jg8AknfdDslf9Rung',  # fourth project
    'AIzaSyAJBtw7HcNUtmw6g3qql7g2EXkalq08hio',  # fifth project
    'AIzaSyAeUgJyVvzJCOyBlqIZi_Au56AYq3sTF_w',  # sixth project
    'AIzaSyBOqyxm-Uz6UxNdRf3pLAFEdo8p3a03uwc',  # seventh project
    'AIzaSyC6YWL2Fp7aRj47A3Id3582SjfiGupQl1M',  # eighth project
    'AIzaSyAa-17-N-baYH6c2twrasx4jRPkCOdx-Xo',  # ninth project
    'AIzaSyA7aeu4w3thBNcNJnOoXqC4771YOyISPgw'   # tenth project
]
GOOGLE_CSE_ID = '310b42d4bee37464e'
current_key_index = 0

# Copy existing functions
def get_next_api_key():
    # ...existing get_next_api_key function...

def search_google(query):
    # ...existing search_google function...

def search_upcitemdb(barcode):
    # ...existing search_upcitemdb function...

# Streamlit UI
st.set_page_config(page_title="Barcode Product Lookup", layout="wide")

st.title("Barcode Product Lookup")

# Input section
barcode = st.text_input("Enter barcode number")

if st.button("Search"):
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