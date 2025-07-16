#!/usr/bin/env python3

import streamlit as st
from googleapiclient.discovery import build
from googleapiclient import errors as googleapiclient_errors

# Test the Google API keys directly
def test_google_api():
    try:
        # Load from secrets
        GOOGLE_API_KEYS = st.secrets["GOOGLE_API_KEYS"]
        GOOGLE_CSE_ID = st.secrets["GOOGLE_CSE_ID"]
        
        print(f"Loaded {len(GOOGLE_API_KEYS)} API keys")
        print(f"CSE ID: {GOOGLE_CSE_ID}")
        
        # Test first API key
        api_key = GOOGLE_API_KEYS[0]
        print(f"Testing with API key: {api_key[:10]}...")
        
        service = build('customsearch', 'v1', developerKey=api_key)
        
        # Simple test search - no restrictions
        query = "072940758044"
        search_query = query
        
        print(f"Search query: {search_query}")
        
        result = service.cse().list(
            q=search_query,
            cx=GOOGLE_CSE_ID,
            num=10
        ).execute()
        
        print(f"Search successful!")
        print(f"Total results estimated: {result.get('searchInformation', {}).get('totalResults', 'Unknown')}")
        
        if 'items' in result:
            print(f"Returned {len(result['items'])} items:")
            for i, item in enumerate(result['items'][:3]):
                print(f"  {i+1}. {item['title']}")
                print(f"     {item['link']}")
        else:
            print("No items returned in result")
            print("Full result:", result)
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e)}")
        return False

if __name__ == "__main__":
    success = test_google_api()
    if success:
        print("\n✅ Google API test successful!")
    else:
        print("\n❌ Google API test failed!")
