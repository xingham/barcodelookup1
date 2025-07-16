#!/usr/bin/env python3
"""
Test script to check if Amazon results are being returned for barcode 072940755005
"""

from googleapiclient.discovery import build
import streamlit as st
from urllib.parse import urlparse

# Load secrets
try:
    GOOGLE_API_KEYS = st.secrets["GOOGLE_API_KEYS"]
    GOOGLE_CSE_ID = st.secrets["GOOGLE_CSE_ID"]
    print("✅ API Keys loaded successfully")
except Exception as e:
    print(f"❌ Error loading API keys: {e}")
    exit(1)

def test_search(barcode):
    api_key = GOOGLE_API_KEYS[0]  # Use first API key
    service = build('customsearch', 'v1', developerKey=api_key)
    
    print(f"\n🔍 Searching for: {barcode}")
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    # Search with the exact same parameters as the app
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
            
            is_amazon = 'amazon' in domain.lower()
            if is_amazon:
                amazon_count += 1
                print(f"  {i}. 🟢 AMAZON: {domain}")
                print(f"     Title: {title}")
                print(f"     Link: {link}")
            else:
                print(f"  {i}. {domain}")
    
    print(f"\n🎯 Amazon results found: {amazon_count}")
    
    return result

if __name__ == "__main__":
    # Test with the specific barcode
    test_search("072940755005")
    
    # Also test with a more general search that should definitely return Amazon
    print("\n" + "="*50)
    print("Testing with 'site:amazon.com 072940755005'")
    
    api_key = GOOGLE_API_KEYS[0]
    service = build('customsearch', 'v1', developerKey=api_key)
    
    result = service.cse().list(
        q="site:amazon.com 072940755005",
        cx=GOOGLE_CSE_ID,
        num=10,
        start=1
    ).execute()
    
    print(f"📊 Amazon-specific search results: {len(result.get('items', []))}")
    if 'items' in result:
        for i, item in enumerate(result['items'], 1):
            print(f"  {i}. {item.get('title', '')}")
