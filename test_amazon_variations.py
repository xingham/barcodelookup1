#!/usr/bin/env python3
"""
Test different search variations to find Amazon product pages
"""

from googleapiclient.discovery import build
import streamlit as st

# Load secrets
GOOGLE_API_KEYS = st.secrets["GOOGLE_API_KEYS"]
GOOGLE_CSE_ID = st.secrets["GOOGLE_CSE_ID"]

def test_variations(barcode):
    api_key = GOOGLE_API_KEYS[0]
    service = build('customsearch', 'v1', developerKey=api_key)
    
    # Different search variations
    searches = [
        f"{barcode}",
        f"UPC {barcode}",
        f"{barcode} amazon",
        f"site:amazon.com {barcode}",
        f"{barcode} -filetype:pdf",
        f'"{barcode}" site:amazon.com'
    ]
    
    for search_query in searches:
        print(f"\n🔍 Testing: '{search_query}'")
        
        try:
            result = service.cse().list(
                q=search_query,
                cx=GOOGLE_CSE_ID,
                num=10,
                start=1
            ).execute()
            
            items = result.get('items', [])
            amazon_found = False
            
            for item in items:
                link = item.get('link', '')
                title = item.get('title', '')
                
                if 'amazon.com' in link and not link.lower().endswith('.pdf'):
                    amazon_found = True
                    print(f"  ✅ Amazon product: {title}")
                    print(f"     Link: {link}")
            
            if not amazon_found:
                print(f"  ❌ No Amazon product pages found ({len(items)} total results)")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    test_variations("072940755005")
