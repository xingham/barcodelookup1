#!/usr/bin/env python3
"""
Test with a barcode that should definitely have Amazon results
"""

from googleapiclient.discovery import build
import streamlit as st
from urllib.parse import urlparse

# Load secrets
GOOGLE_API_KEYS = st.secrets["GOOGLE_API_KEYS"]
GOOGLE_CSE_ID = st.secrets["GOOGLE_CSE_ID"]

def test_popular_barcode():
    api_key = GOOGLE_API_KEYS[0]
    service = build('customsearch', 'v1', developerKey=api_key)
    
    # Test with a popular product that should be on Amazon
    # Using Coca-Cola 12 pack - this should definitely be on Amazon
    barcode = "049000028911"  # Coca-Cola Classic 12 pack
    
    print(f"🔍 Testing with Coca-Cola barcode: {barcode}")
    
    result = service.cse().list(
        q=barcode,
        cx=GOOGLE_CSE_ID,
        num=10,
        start=1
    ).execute()
    
    print(f"📊 Total results: {result.get('searchInformation', {}).get('totalResults', 'Unknown')}")
    print(f"📦 Items returned: {len(result.get('items', []))}")
    
    amazon_count = 0
    
    if 'items' in result:
        print("\n📋 All domains found:")
        for i, item in enumerate(result['items'], 1):
            title = item.get('title', '')
            link = item.get('link', '')
            domain = urlparse(link).netloc
            
            is_amazon = 'amazon.com' in domain.lower()
            if is_amazon:
                amazon_count += 1
                print(f"  {i}. 🟢 AMAZON: {domain}")
                print(f"     Title: {title}")
                print(f"     Link: {link}")
            else:
                print(f"  {i}. {domain}")
    
    print(f"\n🎯 Amazon results found: {amazon_count}")

if __name__ == "__main__":
    test_popular_barcode()
