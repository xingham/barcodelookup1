from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import os
from googleapiclient.discovery import build
from googleapiclient import errors as googleapiclient_errors
from concurrent.futures import ThreadPoolExecutor

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

def get_next_api_key():
    global current_key_index
    starting_index = current_key_index
    
    while True:
        key = GOOGLE_API_KEYS[current_key_index]
        current_key_index = (current_key_index + 1) % len(GOOGLE_API_KEYS)
        
        # Try to validate the key
        try:
            service = build("customsearch", "v1", developerKey=key)
            service.cse().list(q="test", cx=GOOGLE_CSE_ID, num=1).execute()
            print(f"Using API key {current_key_index}")
            return key
        except googleapiclient_errors.HttpError as e:
            if current_key_index == starting_index:
                # We've tried all keys
                raise Exception("All API keys are exhausted")
            continue

def search_google(query):
    try:
        search_query = f'{query} product details'
        
        # Try each API key until one works
        for _ in range(len(GOOGLE_API_KEYS)):
            try:
                current_key = get_next_api_key()
                print(f"Trying API key {current_key_index}")
                
                service = build("customsearch", "v1", developerKey=current_key)
                result = service.cse().list(
                    q=search_query,
                    cx=GOOGLE_CSE_ID,
                    num=10,
                    safe='active',
                    excludeTerms='wikipedia.org github.com'  # Add github.com to excluded sites
                ).execute()
                
                products = []
                if 'items' in result:
                    for item in result.get('items', []):
                        # Skip both Wikipedia and GitHub links
                        if 'wikipedia.org' in item.get('link', '') or 'github.com' in item.get('link', ''):
                            continue
                            
                        product = {
                            'title': item.get('title', ''),
                            'link': item.get('link', ''),
                            'source': 'Google'
                        }
                        
                        # Only add if we have title and link
                        if product['title'] and product['link']:
                            products.append(product)
                    
                    print(f"Successfully used API key {current_key_index}")
                    return products
                    
            except googleapiclient_errors.HttpError as e:
                if 'rateLimitExceeded' in str(e):
                    print(f"Quota exceeded for key {current_key_index}")
                    continue
                else:
                    raise e
        
        # If all keys are exhausted
        return [{
            'title': 'Google Search Unavailable',
            'link': '#',
            'snippet': 'All API keys have reached their daily limit. Please try again tomorrow.',
            'quota_exceeded': True
        }]
        
    except Exception as e:
        print(f"Unexpected error in Google search: {str(e)}")
        return []

def search_upcitemdb(barcode):
    try:
        url = f'https://www.upcitemdb.com/upc/{barcode}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        # Handle 404 more gracefully
        if response.status_code == 404:
            print(f"Product not found in UPCItemDB: {barcode}")
            return []
            
        response.raise_for_status()
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

@app.route('/')
def index():
    print("TEMPLATES DIR CONTENTS:", os.listdir("templates"))
    return render_template('index.html')

@app.route('/lookup/<barcode>', methods=['GET'])
@app.route('/lookup', methods=['POST'])
def lookup(barcode=None):
    if request.method == 'POST':
        if not request.json or 'barcode' not in request.json:
            return jsonify({'success': False, 'error': 'No barcode provided'})
        barcode = request.json['barcode']
    elif not barcode:
        return jsonify({'success': False, 'error': 'No barcode provided'})

    print(f"Looking up barcode: {barcode}")  # Debug log
    
    try:
        upcitemdb_results = search_upcitemdb(barcode)
        print(f"UPCItemDB results: {upcitemdb_results}")  # Debug log
        
        if upcitemdb_results:
            google_results = search_google(barcode)
        else:
            google_results = []

        # Add no results flag
        no_results = not upcitemdb_results and not google_results

        return jsonify({
            'success': True,
            'upcitemdb': upcitemdb_results,
            'google': google_results,
            'no_results': no_results
        })

    except Exception as e:
        print(f"Lookup error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("Starting server on http://127.0.0.1:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
