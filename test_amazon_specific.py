#!/usr/bin/env python3
"""
Test if Google Custom Search can find the specific Amazon page
"""

from googleapiclient.discovery import build
import streamlit as st
from urllib.parse import urlparse

# Load secrets
GOOGLE_API_KEYS = st.secrets["GOOGLE_API_KEYS"]
GOOGLE_CSE_ID = st.secrets["GOOGLE_CSE_ID"]

def test_amazon_specific():
    api_key = GOOGLE_API_KEYS[0]
    service = build('customsearch', 'v1', developerKey=api_key)
    
    barcode = "072940755005"
    
    # Test different search variations to find the Amazon page
    searches = [
        f"{barcode}",
        f"site:amazon.com {barcode}",
        f"site:amazon.com Tuttorosso Diced Tomatoes",
        f"site:amazon.com B00KAOWSB0",  # The specific Amazon ASIN
        f"Tuttorosso Tomates cortados cubitos",  # Spanish title from the URL
        f"amazon.com Tuttorosso {barcode}"
    ]
    
    target_url = "https://www.amazon.com/-/es/Tuttorosso-Tomates-cortados-cubitos-onzas/dp/B00KAOWSB0"
    
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
            found_target = False
            amazon_results = []
            
            print(f"  📊 Total results: {len(items)}")
            
            for item in items:
                link = item.get('link', '')
                title = item.get('title', '')
                
                if 'amazon.com' in link:
                    amazon_results.append({
                        'link': link,
                        'title': title
                    })
                    
                    if target_url in link or 'B00KAOWSB0' in link:
                        found_target = True
                        print(f"  ✅ FOUND TARGET: {title}")
                        print(f"     Link: {link}")
            
            if amazon_results and not found_target:
                print(f"  📦 Found {len(amazon_results)} other Amazon results:")
                for result in amazon_results:
                    print(f"     - {result['title'][:60]}...")
                    print(f"       {result['link']}")
            
            if not amazon_results:
                print(f"  ❌ No Amazon results found")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    test_amazon_specific()
