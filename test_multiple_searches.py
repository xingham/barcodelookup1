#!/usr/bin/env python3

from googleapiclient.discovery import build
from googleapiclient import errors as googleapiclient_errors

def test_multiple_searches():
    try:
        # Direct API keys
        GOOGLE_API_KEYS = [
            "AIzaSyDJw29dPJH7sioK4bqUo-g0VGlfVXeJHso",
            "AIzaSyCZf5f-9rIW0hm6BoykbHMo_0XkqCEp-jY",
            "AIzaSyBt-AH09r8dGcdWARB-u631khJXC8Cxvw4",
        ]
        GOOGLE_CSE_ID = "310b42d4bee37464e"
        
        api_key = GOOGLE_API_KEYS[0]
        service = build('customsearch', 'v1', developerKey=api_key)
        
        query = "072940755043"
        
        # Try multiple search variations with specific sites
        search_variations = [
            f'{query} site:walmart.com OR site:target.com OR site:amazon.com',  # Shopping sites
            f'{query} site:barcodelookup.com OR site:upcindex.com',  # Barcode databases
            f'barcode {query} product',  # General product search
            f'UPC {query}',  # UPC search
            query,  # Plain barcode
        ]
        
        all_results = []
        
        for search_query in search_variations:
            try:
                print(f"\n--- Searching for: {search_query} ---")
                
                result = service.cse().list(
                    q=search_query,
                    cx=GOOGLE_CSE_ID,
                    num=10
                ).execute()
                
                total_results = result.get('searchInformation', {}).get('totalResults', '0')
                print(f"Total estimated results: {total_results}")
                
                if 'items' in result:
                    print(f"Returned {len(result['items'])} items:")
                    for i, item in enumerate(result['items']):
                        link = item.get('link', '')
                        title = item.get('title', '')
                        
                        # Skip if we already have this link
                        if any(existing['link'] == link for existing in all_results):
                            print(f"  {i+1}. [DUPLICATE] {title}")
                            continue
                        
                        all_results.append({
                            'title': title,
                            'link': link,
                            'description': item.get('snippet', ''),
                        })
                        
                        print(f"  {i+1}. [NEW] {title}")
                        print(f"     {link}")
                else:
                    print("No items returned")
                    
            except Exception as e:
                print(f"Error with search variation: {str(e)}")
                continue
        
        print(f"\n=== SUMMARY ===")
        print(f"Total unique results found: {len(all_results)}")
        print(f"Final unique results:")
        for i, result in enumerate(all_results):
            print(f"  {i+1}. {result['title']}")
            print(f"     {result['link']}")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_multiple_searches()
    if success:
        print("\n✅ Multiple search test completed!")
    else:
        print("\n❌ Multiple search test failed!")
