from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import os
from collections import deque  # Add this import
from googleapiclient.discovery import build
from googleapiclient import errors as googleapiclient_errors
from concurrent.futures import ThreadPoolExecutor
from requests_html import HTMLSession
from fake_useragent import UserAgent
from functools import lru_cache  # Add this import
import requests
import random
import time
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import urllib3
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # Suppress SSL warnings 

app = Flask(__name__)

# Add multiple Google API credentials from different projects
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

# Update get_next_api_key to match Streamlit version
def get_next_api_key():
    global current_key_index
    if not GOOGLE_API_KEYS:
        return None
    key = GOOGLE_API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(GOOGLE_API_KEYS)
    return key

class RateLimiter:
    def __init__(self):
        self.requests = deque()
        self.window_size = 60  # 1 minute window
        self.max_requests = 10  # Max requests per window
        
    def can_request(self):
        now = datetime.now()
        while self.requests and self.requests[0] < now - timedelta(seconds=self.window_size):
            self.requests.popleft()
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False

class ProxyRotator:
    def __init__(self):
        self.proxies = []
        self.last_update = None
        self.update_interval = timedelta(minutes=30)
    
    def update_proxies(self):
        try:
            # Get free proxies from multiple sources
            sources = [
                'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
                'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt'
            ]
            
            new_proxies = set()
            for source in sources:
                try:
                    response = requests.get(source, timeout=10)
                    if response.status_code == 200:
                        proxies = response.text.strip().split('\n')
                        new_proxies.update(proxies)
                except Exception as e:
                    print(f"Error fetching proxies from {source}: {str(e)}")
                    continue
            
            self.proxies = list(new_proxies)
            self.last_update = datetime.now()
            print(f"Updated proxy list, found {len(self.proxies)} proxies")
            
        except Exception as e:
            print(f"Error updating proxies: {str(e)}")
    
    def get_proxy(self):
        if not self.last_update or datetime.now() - self.last_update > self.update_interval:
            self.update_proxies()
        
        if self.proxies:
            return random.choice(self.proxies)
        return None

class RequestManager:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0'
        ]
        self.session = HTMLSession()
        self.rate_limiter = RateLimiter()
        self.proxy_rotator = ProxyRotator()
    
    def get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

# Modify the search_google function
@lru_cache(maxsize=1000)
def search_google(barcode):
    try:
        print(f"\n--- Searching Google API ---")
        api_key = get_next_api_key()
        if not api_key:
            print("No API keys available")
            return []

        print(f"Using Google API to search for: {barcode}")
        
        # Build the service
        service = build("customsearch", "v1", developerKey=api_key)
        
        # Construct more flexible search query
        query = f"{barcode}"  # Start with just the barcode
        
        # Execute search with expanded parameters
        result = service.cse().list(
            q=query,
            cx=GOOGLE_CSE_ID,
            num=5,  # Limit to 5 results
            exactTerms=barcode,  # Ensure barcode is in results
            siteSearch="walmart.com,target.com,amazon.com",  # Major retailers
            siteSearchFilter="i"  # Include only these sites
        ).execute()

        print(f"Raw API response: {result}")  # Debug print
        
        results = []
        if 'items' in result:
            for item in result['items']:
                # Skip unwanted domains
                if any(x in item['link'].lower() for x in ['upcitemdb.com', 'barcodelookup.com']):
                    continue
                    
                # Extract and clean up the data
                title = item.get('title', '').replace(' | Walmart', '').replace(' : Target', '')
                snippet = item.get('snippet', '')
                
                results.append({
                    'title': title,
                    'link': item.get('link', ''),
                    'description': snippet,
                    'source': 'Google'
                })
                print(f"Found result: {title}")  # Debug print

        print(f"Found {len(results)} Google API results")
        if not results:
            print("No results found. Check if:")
            print("1. API key is valid")
            print("2. Custom Search Engine ID is correct")
            print("3. Daily quota is not exceeded")
            
        return results
            
    except googleapiclient_errors.HttpError as e:
        error_details = str(e)
        print(f"Google API error details: {error_details}")
        
        if 'quotaExceeded' in error_details:
            print(f"Google API quota exceeded for key: {api_key}")
            return [{
                'source': 'Google',
                'error': 'Daily quota exceeded',
                'quota_exceeded': True,
                'snippet': 'Google search results are unavailable due to API quota limits.'
            }]
        else:
            print(f"Google API error: {error_details}")
        return []
        
    except Exception as e:
        print(f"Google search error: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def search_upcitemdb(barcode):
    try:
        url = f'https://www.upcitemdb.com/upc/{barcode}'
        print(f"Fetching UPCItemDB URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"UPCItemDB response status: {response.status_code}")
        
        if response.status_code == 404:
            print(f"Product not found in UPCItemDB: {barcode}")
            return []
            
        response.raise_for_status()
        
        # Save response content for debugging
        with open('upcitemdb_response.html', 'w') as f:
            f.write(response.text)
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        products = []
        product_info = {}
        
        # Get all product variants from the ordered list
        variants_list = soup.select('div.cont ol.num li')
        if variants_list:
            variants = [variant.text.strip() for variant in variants_list]
            product_info['variants'] = variants
            product_info['title'] = variants[0]  # Main title is first variant
            product_info['description'] = variants[0]  # Main description is first variant
            print(f"Found variants: {variants}")  # Debug log
        
        # Get other details from the table
        details_table = soup.find('table', class_='detail-list')
        if details_table:
            rows = details_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()
                    
                    # Map common fields to product_info
                    if 'Brand' in key:
                        product_info['brand'] = value
                    elif 'Weight' in key:
                        product_info['weight'] = value
                    elif 'Dimension' in key:
                        product_info['dimensions'] = value
                    elif 'Model' in key:
                        product_info['model'] = value
                    elif 'UPC' in key or 'EAN' in key:
                        if 'barcodes' not in product_info:
                            product_info['barcodes'] = []
                        product_info['barcodes'].append(f"{key} {value}")
                    
                    print(f"Found detail: {key} -> {value}")
        
        if product_info:
            product_info['source'] = 'UPCItemDB'
            products.append(product_info)
            print(f"Final product info: {product_info}")
            
        return products
        
    except Exception as e:
        print(f"UPCItemDB scraping error: {str(e)}")
        return []

def search_smartlabel(barcode):
    try:
        search_url = f'https://smartlabel.org/product-search/?product={barcode}'
        print(f"Fetching SmartLabel search URL: {search_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"Search page status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all table rows
            rows = soup.find_all('tr')
            print(f"Found {len(rows)} table rows")
            
            for row in rows:
                # Find cells in the row
                cells = row.find_all('td')
                if len(cells) == 2:  # Should have brand and product cells
                    brand_cell = cells[0]
                    product_cell = cells[1]
                    
                    # Get the brand text
                    brand = brand_cell.get_text(strip=True)
                    
                    # Find product link
                    product_link = product_cell.find('a')
                    if product_link and 'coca-colaproductfacts.com' in product_link.get('href', ''):
                        product_url = product_link['href']
                        product_text = product_link.get_text(strip=True).replace('external', '').strip()
                        
                        print(f"Found product: {brand} - {product_text}")
                        print(f"Product URL: {product_url}")
                        
                        # Create initial product info
                        product_info = {
                            'title': product_text,
                            'link': product_url,
                            'brand': brand,
                            'source': 'SmartLabel'
                        }
                        
                        # Try to get additional details from product page
                        try:
                            print(f"Fetching product details from {product_url}")
                            product_response = requests.get(product_url, headers=headers, timeout=10)
                            
                            if product_response.status_code == 200:
                                product_soup = BeautifulSoup(product_response.text, 'html.parser')
                                product_section = product_soup.find('div', class_='product-sub-section')
                                
                                if product_section:
                                    name = product_section.find('h1', id='product_name')
                                    desc = product_section.find('h2', id='product_desc')
                                    size = product_section.find('h3', id='product_size')
                                    
                                    if name: product_info['name'] = name.text.strip()
                                    if desc: product_info['description'] = desc.text.strip()
                                    if size: product_info['size'] = size.text.strip()
                                    
                                    ingredients = product_soup.find('div', class_='ingredients-list')
                                    if ingredients:
                                        product_info['ingredients'] = ingredients.text.strip()
                        except Exception as e:
                            print(f"Error fetching product details: {str(e)}")
                        
                        print(f"Final SmartLabel product info: {product_info}")
                        return [product_info]
            
            print("No matching product found in search results")
            return []
            
        print(f"Search request failed with status {response.status_code}")
        return []
        
    except Exception as e:
        print(f"SmartLabel error: {str(e)}")
        traceback.print_exc()
        return []

def search_barcode_lookup(barcode):
    try:
        print(f"\n--- Searching BarcodeLookup ---")
        url = f'https://www.barcodelookup.com/{barcode}'
        print(f"Fetching URL: {url}")
        
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',  # Removed br compression
            'Connection': 'keep-alive'
        }
        
        # First visit homepage
        response = session.get(
            'https://www.barcodelookup.com/',
            headers=headers,
            timeout=15
        )
        time.sleep(2)
        
        if response.status_code == 200:
            # Add any cookies
            if session.cookies:
                headers['Cookie'] = '; '.join([f'{k}={v}' for k, v in session.cookies.items()])
            
            # Get product page
            response = session.get(url, headers=headers, timeout=15)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                # Save raw response for debugging
                with open('debug_response.txt', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                soup = BeautifulSoup(response.text, 'html.parser')
                print(f"HTML Length: {len(response.text)}")
                
                # Initialize product info
                product_info = {
                    'source': 'Barcode Lookup',
                    'link': url,
                    'view_url': url
                }
                
                # Debug: Print page structure
                print("\nPage Structure:")
                print("Title:", soup.title.string if soup.title else "No title")
                print("Meta Description:", soup.find('meta', {'name': 'description'}).get('content') if soup.find('meta', {'name': 'description'}) else "No meta description")
                
                # Try all possible product selectors
                selectors = [
                    ('h1.product-name', 'Product Name H1'),
                    ('div.product-main h1', 'Main Content H1'),
                    ('div.product-details h1', 'Product Details H1'),
                    ('#product-title', 'Product Title ID'),
                    ('.product-title', 'Product Title Class')
                ]
                
                for selector, desc in selectors:
                    element = soup.select_one(selector)
                    if element:
                        text = element.get_text(strip=True)
                        print(f"Found {desc}: {text}")
                        product_info['title'] = text
                        product_info['description'] = text
                        return [product_info]
                
                # If no structured data found, try meta description
                meta_desc = soup.find('meta', {'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    desc_content = meta_desc.get('content')
                    print(f"Found meta description: {desc_content}")
                    if ' - ' in desc_content:
                        product_name = desc_content.split(' - ', 1)[1].strip()
                        product_info['title'] = product_name
                        product_info['description'] = product_name
                        return [product_info]
                
                print("\nNo product information found. Debug info saved to debug_response.txt")
                return []
                
            elif response.status_code == 403:
                print("Access denied by BarcodeLookup")
                return []
                
        return []
        
    except Exception as e:
        print(f"BarcodeLookup error: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

@app.route('/')
def index():
    print("TEMPLATES DIR CONTENTS:", os.listdir("templates"))
    return render_template('index.html')

# Modify the lookup function to include SmartLabel results
@app.route('/lookup/<barcode>', methods=['GET'])
@app.route('/lookup', methods=['POST'])
def lookup(barcode=None):
    if request.method == 'POST':
        if not request.json or 'barcode' not in request.json:
            return jsonify({'success': False, 'error': 'No barcode provided'})
        barcode = request.json['barcode']
    elif not barcode:
        return jsonify({'success': False, 'error': 'No barcode provided'})

    print(f"\n=== Starting lookup for barcode: {barcode} ===")
    
    try:
        print("\n--- Searching UPCItemDB ---")
        upcitemdb_results = search_upcitemdb(barcode)
        print(f"UPCItemDB results: {len(upcitemdb_results)}")
        
        print("\n--- Searching BarcodeLookup ---")
        barcodelookup_results = search_barcode_lookup(barcode)
        print(f"BarcodeLookup results: {len(barcodelookup_results)}")
        
        print("\n--- Searching Google ---")
        google_results = search_google(barcode)
        print(f"Google results: {len(google_results)}")

        # Add no results flag
        no_results = not upcitemdb_results and not google_results and not barcodelookup_results
        print(f"\nNo results found: {no_results}")

        return jsonify({
            'success': True,
            'upcitemdb': upcitemdb_results,
            'barcodelookup': barcodelookup_results,
            'google': google_results,
            'no_results': no_results
        })

    except Exception as e:
        print(f"Lookup error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

def test_api_keys():
    print("Testing all API keys...")
    for i, key in enumerate(GOOGLE_API_KEYS):
        try:
            service = build("customsearch", "v1", developerKey=key)
            result = service.cse().list(q="test", cx=GOOGLE_CSE_ID, num=1).execute()
            print(f"✓ API key {i} is working")
        except googleapiclient_errors.HttpError as e:
            print(f"✗ API key {i} failed: {str(e)}")

# Modify the startup code
if __name__ == '__main__':
    import sys
    
    # Only test keys if --test-keys flag is provided
    if '--test-keys' in sys.argv:
        test_api_keys()
    
    # Disable SSL warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # Suppress SSL warnings
    
    print("Starting server on http://127.0.0.1:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
