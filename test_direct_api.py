#!/usr/bin/env python3

from googleapiclient.discovery import build
from googleapiclient import errors as googleapiclient_errors

# Test the Google API keys directly (without Streamlit)
def test_google_api_direct():
    try:
        # Direct API keys (from your secrets file)
        GOOGLE_API_KEYS = [
            "AIzaSyDJw29dPJH7sioK4bqUo-g0VGlfVXeJHso",
            "AIzaSyCZf5f-9rIW0hm6BoykbHMo_0XkqCEp-jY",
            "AIzaSyBt-AH09r8dGcdWARB-u631khJXC8Cxvw4",
            "AIzaSyBGlB4Ro1uGyfIcE7Jg8AknfdDslf9Rung",
            "AIzaSyAJBtw7HcNUtmw6g3qql7g2EXkalq08hio",
            "AIzaSyAeUgJyVvzJCOyBlqIZi_Au56AYq3sTF_w",
            "AIzaSyBOqyxm-Uz6UxNdRf3pLAFEdo8p3a03uwc",
            "AIzaSyC6YWL2Fp7aRj47A3Id3582SjfiGupQl1M",
            "AIzaSyAa-17-N-baYH6c2twrasx4jRPkCOdx-Xo",
            "AIzaSyA7aeu4w3thBNcNJnOoXqC4771YOyISPgw"
        ]
        GOOGLE_CSE_ID = "310b42d4bee37464e"
        
        print(f"Loaded {len(GOOGLE_API_KEYS)} API keys")
        print(f"CSE ID: {GOOGLE_CSE_ID}")
        
        # Test first API key
        api_key = GOOGLE_API_KEYS[0]
        print(f"Testing with API key: {api_key[:10]}...")
        
        service = build('customsearch', 'v1', developerKey=api_key)
        
        # Single search call - test with a barcode that might have more results
        query = "012000073052"  # Coca-Cola barcode
        search_query = query
        
        print(f"Search query: {search_query}")
        
        result = service.cse().list(
            q=search_query,
            cx=GOOGLE_CSE_ID,
            num=10,
            start=1
        ).execute()
        
        print(f"Search successful!")
        print(f"Total results estimated: {result.get('searchInformation', {}).get('totalResults', 'Unknown')}")
        
        if 'items' in result:
            print(f"Returned {len(result['items'])} items:")
            for i, item in enumerate(result['items'][:5]):
                print(f"  {i+1}. {item['title']}")
                print(f"     {item['link']}")
        else:
            print("No items returned in result")
            print("Full result keys:", list(result.keys()))
            if 'searchInformation' in result:
                print("Search info:", result['searchInformation'])
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_google_api_direct()
    if success:
        print("\n✅ Google API test successful!")
    else:
        print("\n❌ Google API test failed!")
