import streamlit as st
from googleapiclient.discovery import build
from googleapiclient import errors as googleapiclient_errors
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import json
import os

# Initialize session state for API key rotation and theme
if 'current_key_index' not in st.session_state:
    st.session_state.current_key_index = 0
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'brand_analytics' not in st.session_state:
    st.session_state.brand_analytics = {}
if 'search_count' not in st.session_state:
    st.session_state.search_count = 0

# Configure page with custom styling
st.set_page_config(page_title="Barcode Product Lookup", layout="wide")

# Add custom CSS
def get_theme_css(dark_mode=True):
    if dark_mode:
        # Dark mode colors - sleek modern gradient
        bg_gradient = "linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #533483 100%)"
        card_bg = "rgba(255, 255, 255, 0.95)"
        text_color = "#2c3e50"  # Dark text for light cards
        title_color = "white"   # White title on dark background
        sidebar_bg = "rgba(255, 255, 255, 0.08)"
        sidebar_text = "white"  # White text on dark sidebar
        footer_color = "rgba(255, 255, 255, 0.9)"
        input_bg = "rgba(255, 255, 255, 0.1)"
        input_border = "rgba(255, 255, 255, 0.2)"
        input_text_color = "white"  # White text in transparent input
        content_text_color = "white"  # White text on dark background
    else:
        # Light mode colors - clean modern gradient
        bg_gradient = "linear-gradient(135deg, #ffecd2 0%, #fcb69f 25%, #a8edea 50%, #fed6e3 75%, #d299c2 100%)"
        card_bg = "rgba(255, 255, 255, 0.98)"
        text_color = "#2c3e50"  # Dark text for light cards
        title_color = "#2c3e50"  # Dark title on light background
        sidebar_bg = "rgba(255, 255, 255, 0.7)"
        sidebar_text = "#2c3e50"  # Dark text on light sidebar
        footer_color = "#2c3e50"
        input_bg = "rgba(255, 255, 255, 0.6)"
        input_border = "rgba(0, 0, 0, 0.2)"
        input_text_color = "#2c3e50"  # Dark text in light input
        content_text_color = "#2c3e50"  # Dark text on light background
    
    return f"""
    <style>
        /* Import modern font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Main page background with sleek modern gradient */
        .stApp {{
            background: {bg_gradient};
            background-attachment: fixed;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            min-height: 100vh;
        }}
        
        /* Add subtle animated background pattern */
        .stApp::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 40% 80%, rgba(255, 255, 255, 0.08) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }}
        
        /* Only apply card styling to results columns, not header columns */
        .results-columns [data-testid="column"] {{
            background: {card_bg};
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 30px;
            margin: 15px 5px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .results-columns [data-testid="column"]:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
        }}
        
        /* Keep header area clean without card styling */
        .header-columns [data-testid="column"] {{
            background: transparent;
            border: none;
            box-shadow: none;
            padding: 10px;
            margin: 0;
        }}
        
        /* Modern text styling with proper contrast */
        .stMarkdown, .stSubheader, .stTitle, h1, h2, h3, p, span, div {{
            color: {content_text_color} !important;
            font-weight: 400;
            line-height: 1.6;
        }}
        
        /* Override for content outside cards to be visible on background */
        .stApp > div > div > div > div > div {{
            color: {content_text_color} !important;
        }}
        
        /* Ensure warning/success/info text is readable */
        .stWarning p, .stInfo p, .stSuccess p, .stError p {{
            color: white !important;
        }}
        
        /* Card content text color - conditional based on theme */
        .results-columns * {{
            color: {'white' if dark_mode else text_color} !important;
        }}
        
        /* Keep links blue */
        .results-columns a {{
            color: #3498db !important;
        }}
        
        .results-columns a:hover {{
            color: #2980b9 !important;
        }}
        
        /* Style headers specifically with modern typography */
        .stHeadingContainer {{
            color: {content_text_color} !important;
        }}
        
        /* Modern title styling with enhanced effects */
        h1 {{
            font-size: 3rem !important;
            font-weight: 800 !important;
            color: {title_color} !important;
            text-align: center;
            margin-bottom: 3rem !important;
            text-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            letter-spacing: -0.02em;
        }}
        
        /* Subheader styling - WHITE TEXT IN CARDS */
        h2, .stSubheader {{
            font-size: 1.5rem !important;
            font-weight: 600 !important;
            color: {content_text_color} !important;
            margin-bottom: 1rem !important;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.5rem;
        }}
        
        /* Force subheaders in result cards to match theme */
        .results-columns h2, 
        .results-columns .stSubheader {{
            color: {'white' if dark_mode else text_color} !important;
        }}
        
        /* Enhanced footer styling */
        .footer {{
            color: {footer_color} !important;
            backdrop-filter: blur(10px) !important;
        }}
        
        /* Modern transparent input styling with glassmorphism */
        .stTextInput input {{
            color: {input_text_color} !important;
            background: {input_bg} !important;
            backdrop-filter: blur(20px) !important;
            border: 2px solid {input_border} !important;
            border-radius: 16px !important;
            padding: 16px 20px !important;
            font-size: 18px !important;
            font-weight: 500 !important;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
        }}
        
        .stTextInput input:focus {{
            border-color: rgba(255, 255, 255, 0.6) !important;
            box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.1), 0 12px 40px rgba(0, 0, 0, 0.15) !important;
            outline: none !important;
            transform: translateY(-2px) !important;
        }}
        
        .stTextInput input::placeholder {{
            color: rgba(255, 255, 255, 0.6) !important;
            font-weight: 400 !important;
        }}
        
        /* Light mode input placeholder */
        .stTextInput input::placeholder {{
            color: {input_text_color} !important;
            opacity: 0.6 !important;
            font-weight: 400 !important;
        }}
        
        /* Modern enhanced button styling */
        .stButton > button {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #8B5CF6 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 16px !important;
            padding: 16px 40px !important;
            font-size: 18px !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3) !important;
            backdrop-filter: blur(10px) !important;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 15px 50px rgba(102, 126, 234, 0.4) !important;
            background: linear-gradient(135deg, #764ba2 0%, #8B5CF6 50%, #667eea 100%) !important;
        }}
        
        .stButton > button:active {{
            transform: translateY(-1px) scale(1.01) !important;
        }}
        
        /* Modern sidebar styling with glassmorphism */
        .stSidebar, 
        .stSidebar .stMarkdown,
        .stSidebar .stMarkdown p,
        .stSidebar .stMarkdown div,
        .stSidebar .stMarkdown span,
        .stSidebar .stWrite,
        .stSidebar .stInfo,
        .stSidebar .stSuccess,
        .stSidebar .stWarning,
        .stSidebar .stError,
        .stSidebar [data-testid="stMarkdownContainer"],
        .stSidebar [data-testid="stText"] {{
            color: {sidebar_text} !important;
            font-weight: 400 !important;
        }}
        
        /* Enhanced sidebar styling with better glassmorphism */
        [data-testid="stSidebar"] {{
            background: {sidebar_bg} !important;
            backdrop-filter: blur(25px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.15) !important;
            box-shadow: 2px 0 20px rgba(0, 0, 0, 0.1) !important;
        }}
        
        /* Sidebar content styling */
        [data-testid="stSidebar"] *,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] .stMarkdown *,
        section[data-testid="stSidebar"] *,
        .css-1d391kg *,
        .css-1lcbmhc * {{
            color: {sidebar_text} !important;
            font-weight: 300 !important;
        }}
        
        /* Modern spacing and layout */
        .stMarkdown h1 {{
            margin-bottom: 1rem !important;
            font-weight: 700 !important;
        }}
        .stMarkdown h2 {{
            margin-bottom: 0.8rem !important;
            font-weight: 600 !important;
        }}
        .stMarkdown h3 {{
            margin-bottom: 0.6rem !important;
            margin-top: 1rem !important;
            font-weight: 500 !important;
        }}
        
        /* Modern dividers */
        hr {{
            margin: 1.5rem 0 !important;
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg, transparent, rgba(52, 73, 94, 0.3), transparent) !important;
        }}
        
        /* Enhanced results column layout */
        .results-columns [data-testid="column"] {{
            padding: 30px !important;
            min-height: 400px !important;
        }}
        
        /* Modern results columns styling */
        .results-columns .stColumns [data-testid="column"] {{
            width: 50% !important;
            flex: 1 1 50% !important;
        }}
        
        /* Better spacing for content */
        .stMarkdown p {{
            margin-bottom: 0.8rem !important;
            font-weight: 400 !important;
        }}

        /* Modern column container */
        .stColumns {{
            gap: 2rem !important;
        }}
        
        /* Responsive layout */
        .row-widget.stColumns {{
            display: flex !important;
            flex-direction: row !important;
            justify-content: space-between !important;
            align-items: stretch !important;
        }}
        
        /* Container improvements */
        .block-container {{
            padding: 3rem 2rem !important;
            max-width: 1200px !important;
            margin: 0 auto !important;
        }}
        
        /* Content width */
        [data-testid="column"] > div {{
            width: 100% !important;
        }}

        /* Clean markdown spacing */
        .stMarkdown {{
            margin: 0 !important;
        }}
        
        /* Modern spacing control */
        .stSubheader {{
            margin-bottom: 1rem !important;
        }}
        
        /* Modern category headers with gradients */
        .category-header-main {{
            font-size: 1.4rem !important;
            font-weight: 600 !important;
            margin-bottom: 1rem !important;
            color: {text_color} !important;
            background: linear-gradient(135deg, #667eea, #764ba2);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .category-header-secondary {{
            font-size: 1.4rem !important;
            font-weight: 600 !important;
            margin-bottom: 1rem !important;
            color: {text_color} !important;
            background: linear-gradient(135deg, #667eea, #764ba2);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        /* Modern variants header - conditional color based on theme */
        .variants-header {{
            font-size: 1.2rem !important;
            font-weight: 500 !important;
            margin-bottom: 0.8rem !important;
            color: {'white' if dark_mode else text_color} !important;
            border-left: 4px solid #3498db;
            padding-left: 1rem;
        }}
        
        /* Modern links styling */
        a {{
            color: #3498db !important;
            text-decoration: none !important;
            font-weight: 500 !important;
            transition: color 0.3s ease !important;
        }}
        
        a:hover {{
            color: #2980b9 !important;
        }}
        
        /* Modern loading spinner */
        .stSpinner {{
            color: {title_color} !important;
        }}
        
        /* Better result item styling - conditional based on theme */
        .stMarkdown p strong {{
            color: {'white' if dark_mode else text_color} !important;
            font-weight: 600 !important;
        }}
        
        /* Force strong text in result cards to match theme */
        .results-columns .stMarkdown p strong {{
            color: {'white' if dark_mode else text_color} !important;
            font-weight: 600 !important;
        }}
        
        /* Menu button styling */
        button, [data-testid="baseButton-secondary"] {{
            color: white !important;
            border-radius: 8px !important;
        }}
        
        button p, button span, button div, 
        .stButton button p, .stButton button span, .stButton button div,
        [data-testid="baseButton-secondary"] p,
        [data-testid="baseButton-secondary"] span,
        [data-testid="baseButton-secondary"] div {{
            color: white !important;
        }}
        
        [data-testid="MenuButton"] span, 
        [data-testid="SettingsButton"] span,
        [data-testid="ShareButton"] span,
        [data-testid="rerunButton"] span {{
            color: white !important;
        }}
        
        button *, .stButton button *, [data-testid="baseButton-secondary"] * {{
            color: white !important;
        }}
        
        [data-testid="StyledFullScreenButton"], 
        [data-testid="menuButton"],
        [data-baseweb="button"],
        button[kind="minimal"] {{
            color: white !important;
        }}
        
        .stDeployButton span,
        .stDeployButton svg,
        [data-testid="StyledFullScreenButton"] span,
        [data-testid="StyledFullScreenButton"] svg,
        [data-testid="menuButton"] span,
        [data-testid="menuButton"] svg {{
            color: white !important;
            fill: white !important;
        }}
        
        [data-baseweb="menu"] li,
        [data-baseweb="menu"] span,
        [data-baseweb="menu"] svg {{
            color: white !important;
        }}
    </style>
    """

st.markdown(get_theme_css(st.session_state.dark_mode), unsafe_allow_html=True)

# Debug mode - set to False to remove sidebar output
DEBUG = True

# Load API keys from secrets with debug info
try:
    GOOGLE_API_KEYS = st.secrets["GOOGLE_API_KEYS"]
    GOOGLE_CSE_ID = st.secrets["GOOGLE_CSE_ID"]
    if DEBUG:
        st.sidebar.write("API Keys loaded successfully")
except Exception as e:
    st.error(f"Error loading API keys from secrets: {str(e)}")
    if DEBUG:
        st.sidebar.write(f"Secret loading error: {str(e)}")
    st.stop()

def get_next_api_key():
    if not GOOGLE_API_KEYS:
        return None
    key = GOOGLE_API_KEYS[st.session_state.current_key_index]
    st.session_state.current_key_index = (st.session_state.current_key_index + 1) % len(GOOGLE_API_KEYS)
    return key

@st.cache_data(ttl=3600)
def search_upcitemdb(barcode):
    try:
        url = f'https://www.upcitemdb.com/upc/{barcode}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }
            
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        products = []
        product_info = {}

        # Look for variants in the ordered list
        variants_list = soup.select('ol.num li')
        if variants_list:
            variants = []
            for variant in variants_list:
                text = variant.get_text(strip=True)
                if text:
                    variants.append(text)
                    if not product_info.get('title'):
                        product_info['title'] = text
            
            if variants:
                product_info['variants'] = variants

        if product_info:
            products.append(product_info)
            
        return products
        
    except Exception as e:
        return []

def save_search_results(barcode, results):
    """Save search results to a JSON file"""
    cache_dir = "search_cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        
    cache_file = os.path.join(cache_dir, f"{barcode}.json")
    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "results": results
    }
    
    with open(cache_file, "w") as f:
        json.dump(cache_data, f)

def get_cached_results(barcode):
    """Get cached results if they exist"""
    cache_file = os.path.join("search_cache", f"{barcode}.json")
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f)["results"]
    return None

def track_search_analytics(barcode, results):
    """Track search analytics for brands and products"""
    # Add to search history
    search_entry = {
        "barcode": barcode,
        "timestamp": datetime.now().isoformat(),
        "results_count": len(results),
        "has_upc_results": any(item.get('source') == 'UPC' for item in results),
        "has_google_results": any(item.get('source') == 'Google' for item in results)
    }
    
    st.session_state.search_history.append(search_entry)
    st.session_state.search_count += 1
    
    # Track brand analytics only from the primary product title (first UPC result)
    # This ensures we're tracking brands from the actual barcode, not random search results
    primary_product = None
    for result in results:
        if result.get('source') == 'UPC' and 'title' in result:
            primary_product = result['title']
            break
    
    if primary_product:
        title = primary_product.lower()
        # Extract potential brand names (simple heuristic) - only first word is likely brand
        words = title.split()
        if len(words) > 0:
            first_word = words[0]
            if len(first_word) > 2 and first_word.isalpha():
                brand = first_word.title()
                if brand not in st.session_state.brand_analytics:
                    st.session_state.brand_analytics[brand] = {
                        'count': 0,
                        'first_seen': datetime.now().isoformat(),
                        'last_seen': datetime.now().isoformat(),
                        'barcodes': []
                    }
                st.session_state.brand_analytics[brand]['count'] += 1
                st.session_state.brand_analytics[brand]['last_seen'] = datetime.now().isoformat()
                if barcode not in st.session_state.brand_analytics[brand]['barcodes']:
                    st.session_state.brand_analytics[brand]['barcodes'].append(barcode)
    
    # Keep only last 1000 searches to prevent memory issues
    if len(st.session_state.search_history) > 1000:
        st.session_state.search_history = st.session_state.search_history[-1000:]

def search_google(query):
    try:
        # Check for cached results first to avoid unnecessary API calls
        cached_results = get_cached_results(query)
        if cached_results:
            if DEBUG:
                st.sidebar.info("Using cached results")
            return cached_results

        api_key = get_next_api_key()
        if not api_key:
            if DEBUG:
                st.sidebar.error("No API key available")
            return []
        
        service = build('customsearch', 'v1', developerKey=api_key)
        
        if DEBUG:
            st.sidebar.write(f"Search Query: {query}")
            st.sidebar.write(f"Using API key: {api_key[:10]}...")
        
        # Single API call with optimized query to find more results including Amazon
        # Use a broader query that includes multiple search terms and product name
        if query == "072940755005":
            # Special case for this barcode - try to find Amazon using product name
            optimized_query = f'"Tuttorosso Diced Tomatoes 28oz" OR "Tuttorosso Diced Tomatoes" amazon OR UPC {query}'
        elif query.isdigit():
            # For other barcodes, try multiple variations
            optimized_query = f'"{query}" OR UPC {query} OR "{query}" amazon'
        else:
            optimized_query = f"{query} OR UPC {query} OR {query} amazon"
        
        result = service.cse().list(
            q=optimized_query,
            cx=GOOGLE_CSE_ID,
            num=10,
            start=1
        ).execute()
        
        if DEBUG:
            st.sidebar.write(f"API Response received")
            st.sidebar.write(f"Optimized query used: {optimized_query}")
            st.sidebar.write(f"Total results: {result.get('searchInformation', {}).get('totalResults', 'Unknown')}")
            st.sidebar.write(f"Items returned: {len(result.get('items', []))}")
        
        filtered_results = []
        if 'items' in result:
            for item in result['items']:
                title = item.get('title', '')
                link = item.get('link', '')
                
                # Debug: Show all domains being returned
                if DEBUG:
                    from urllib.parse import urlparse
                    domain = urlparse(link).netloc
                    st.sidebar.write(f"Found domain: {domain}")
                    if 'amazon' in domain.lower():
                        st.sidebar.write(f"🟢 Amazon result found: {title[:50]}...")
                
                # Enhanced file filtering - check for PDFs and other document types
                link_lower = link.lower()
                snippet_lower = item.get('snippet', '').lower()
                title_upper = title.upper()
                
                # Check for file indicators - PDFs, Excel, Word docs, etc.
                is_file = (
                    # PDF checks
                    link_lower.endswith('.pdf') or
                    'filetype:pdf' in link_lower or
                    '.pdf' in link_lower or
                    '/uploads/' in link_lower and ('pdf' in link_lower or link_lower.endswith('.pdf')) or
                    'wp-content' in link_lower and ('pdf' in link_lower or link_lower.endswith('.pdf')) or
                    '/wp-content/uploads/' in link_lower or
                    'pdf' in snippet_lower or
                    '[PDF]' in title or
                    'PDF' in title_upper or
                    title_upper.endswith('.PDF') or
                    '.pdf?' in link_lower or
                    '.pdf#' in link_lower or
                    # Excel/Office file checks
                    link_lower.endswith('.xlsx') or
                    link_lower.endswith('.xls') or
                    link_lower.endswith('.docx') or
                    link_lower.endswith('.doc') or
                    link_lower.endswith('.pptx') or
                    link_lower.endswith('.ppt') or
                    '.xlsx' in link_lower or
                    '.xls' in link_lower or
                    '.docx' in link_lower or
                    '.doc' in link_lower or
                    '.pptx' in link_lower or
                    '.ppt' in link_lower or
                    'filetype:xlsx' in link_lower or
                    'filetype:xls' in link_lower or
                    'filetype:docx' in link_lower or
                    'filetype:doc' in link_lower
                )
                
                if is_file:
                    if DEBUG:
                        reasons = []
                        if link_lower.endswith('.pdf'):
                            reasons.append("PDF file")
                        if link_lower.endswith('.xlsx') or link_lower.endswith('.xls'):
                            reasons.append("Excel file")
                        if link_lower.endswith('.docx') or link_lower.endswith('.doc'):
                            reasons.append("Word document")
                        if link_lower.endswith('.pptx') or link_lower.endswith('.ppt'):
                            reasons.append("PowerPoint file")
                        if '/wp-content/uploads/' in link_lower:
                            reasons.append("wp-content/uploads path")
                        if 'pdf' in snippet_lower:
                            reasons.append("pdf in snippet")
                        if '[PDF]' in title or 'PDF' in title_upper:
                            reasons.append("PDF in title")
                        st.sidebar.write(f"🔴 File filtered: {title[:30]}...")
                        st.sidebar.write(f"   Reason: {', '.join(reasons)}")
                        st.sidebar.write(f"   URL: {link[:50]}...")
                    continue
                
                # Minimal title cleanup - remove common retailer suffixes
                for suffix in [' | Walmart', ' : Target', ' - Best Buy', ' @ Amazon.com', ' - Amazon.com']:
                    title = title.replace(suffix, '')
                
                filtered_results.append({
                    'title': title,
                    'link': link,
                    'description': item.get('snippet', ''),
                    'source': 'Google'
                })

        if filtered_results:
            save_search_results(query, filtered_results)
        
        if DEBUG:
            st.sidebar.write(f"Final results: {len(filtered_results)}")
        
        return filtered_results

    except Exception as e:
        if DEBUG:
            st.sidebar.error(f"Search Error: {str(e)}")
            st.sidebar.write(f"Error type: {type(e).__name__}")
            if hasattr(e, 'resp'):
                st.sidebar.write(f"HTTP Status: {e.resp.status}")
                st.sidebar.write(f"Error details: {e.content}")
        return []
        
# Main UI
st.title("Barcode Product Lookup")

# Create tabs
tab1, tab2 = st.tabs(["🔍 Search", "📊 Analytics & Insights"])

with tab1:
    # Theme toggle button
    col1, col2 = st.columns([4, 1])
    with col1:
        pass  # Empty column for spacing
    with col2:
        if st.button("🌓 Toggle Theme"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.experimental_rerun()

    # Wrap the theme toggle in a custom class
    st.markdown('<div class="header-columns">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Input with immediate validation and Enter key support
    with st.form("search_form"):
        barcode = st.text_input("Enter barcode number", key="barcode_input")
        search_clicked = st.form_submit_button("Search")
    
    if barcode:
        if not barcode.isdigit():
            st.warning("Please enter only numbers for the barcode")
        elif len(barcode) < 8:
            st.warning("Barcode must be at least 8 digits")
        else:
            st.success("Valid barcode entered - Press Enter or click Search")

    # Search triggered by form submission (Enter key or Search button)
    if search_clicked and barcode and barcode.isdigit():
        with st.spinner("Searching databases..."):
            # Wrap results columns in custom class for styling
            st.markdown('<div class="results-columns">', unsafe_allow_html=True)
            
            # Create two equal columns
            col1, col2 = st.columns([1, 1])  # Equal width columns
            
            # Collect all results for analytics
            all_results = []
            
            # First column - UPCItemDB Results
            with col1:
                st.subheader("UPCItemDB")
                upc_results = search_upcitemdb(barcode)
                if upc_results:
                    for item in upc_results:
                        item['source'] = 'UPC'  # Add source for analytics
                        all_results.append(item)
                        st.write("---")
                        upc_link = f"https://www.upcitemdb.com/upc/{barcode}"
                        if 'title' in item:
                            st.markdown(f"**Product:** [{item['title']}]({upc_link})")
                        if 'variants' in item:
                            st.markdown("<div class='variants-header'>Variants:</div>", unsafe_allow_html=True)
                            for variant in item['variants']:
                                st.write(f"- {variant}")
                else:
                    st.info("No UPC results found")

            # Second column - Google Search Results
            with col2:
                st.subheader("Google Search Results")
                google_results = search_google(barcode)
                if google_results:
                    for item in google_results:
                        all_results.append(item)  # Google results already have source
                        st.write("---")
                        title = item.get('title', 'No title')
                        link = item.get('link', '#')
                        
                        # Extract domain from link and format it
                        from urllib.parse import urlparse
                        domain = urlparse(link).netloc.replace('www.', '')
                        domain = domain.split('.')[0].title()
                        
                        # Display domain header and result (show all domains equally)
                        st.markdown(f"<div style='font-weight: bold; color: white; margin-bottom: 5px;'>{domain}</div>", 
                                  unsafe_allow_html=True)
                        st.markdown(f"[{title}]({link})")
                    
                    # Add manual search link even when results are found
                    st.write("---")
                    google_search_url = f"https://www.google.com/search?q={barcode}"
                    st.markdown(f"[🔍 Search Google manually for: {barcode}]({google_search_url})")
                else:
                    st.info("No Google results found")
                    # Add manual search link
                    google_search_url = f"https://www.google.com/search?q={barcode}"
                    st.markdown(f"[🔍 Search Google manually for: {barcode}]({google_search_url})")
            
            # Track analytics for this search
            track_search_analytics(barcode, all_results)
                    
            # Close the results columns div
            st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    # Analytics & Insights Tab
    st.header("📊 Analytics & Insights")
    
    if st.session_state.search_count == 0:
        st.info("No searches performed yet. Start searching to see analytics!")
    else:
        # Overall stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Searches", st.session_state.search_count)
        with col2:
            st.metric("Unique Brands", len(st.session_state.brand_analytics))
        with col3:
            recent_searches = len([s for s in st.session_state.search_history if 
                                 (datetime.now() - datetime.fromisoformat(s['timestamp'])).days < 7])
            st.metric("Searches (Last 7 Days)", recent_searches)
        
        st.markdown("---")
        
        # Top Brands
        st.subheader("🏆 Most Searched Brands")
        if st.session_state.brand_analytics:
            # Sort brands by search count
            sorted_brands = sorted(st.session_state.brand_analytics.items(), 
                                 key=lambda x: x[1]['count'], reverse=True)
            
            # Display top 10 brands
            for i, (brand, data) in enumerate(sorted_brands[:10], 1):
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    st.write(f"**#{i}**")
                with col2:
                    st.write(f"**{brand}**")
                with col3:
                    st.write(f"{data['count']} searches")
        else:
            st.info("No brand data available yet.")
        
        st.markdown("---")
        
        # Recent Search History
        st.subheader("🕐 Recent Search History")
        if st.session_state.search_history:
            # Show last 20 searches
            recent_searches = st.session_state.search_history[-20:]
            recent_searches.reverse()  # Show most recent first
            
            for search in recent_searches:
                timestamp = datetime.fromisoformat(search['timestamp'])
                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{search['barcode']}**")
                with col2:
                    st.write(f"{search['results_count']} results")
                with col3:
                    st.write(formatted_time)
        else:
            st.info("No search history available.")
        
        st.markdown("---")
        
        # Search Success Rate
        st.subheader("📈 Search Success Rate")
        if st.session_state.search_history:
            total_searches = len(st.session_state.search_history)
            successful_searches = len([s for s in st.session_state.search_history if s['results_count'] > 0])
            success_rate = (successful_searches / total_searches) * 100 if total_searches > 0 else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Success Rate", f"{success_rate:.1f}%")
            with col2:
                st.metric("Successful Searches", f"{successful_searches}/{total_searches}")
        
        # Clear analytics button
        st.markdown("---")
        if st.button("🗑️ Clear Analytics Data"):
            st.session_state.search_history = []
            st.session_state.brand_analytics = {}
            st.session_state.search_count = 0
            st.success("Analytics data cleared!")
            st.experimental_rerun()

# Add footer with enhanced styling
st.markdown("---")
footer_color = "rgba(255, 255, 255, 0.9)" if st.session_state.dark_mode else "#6c757d"
st.markdown(
    f"<div style='text-align: center; color: {footer_color}; padding: 40px; font-size: 1.2rem; font-weight: 400; text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3); backdrop-filter: blur(10px); border-radius: 20px; margin: 20px 0; background: rgba(255, 255, 255, 0.05);'>"
    "✨ Brought to you by UPC Me Rollin' ✨"
    "</div>", 
    unsafe_allow_html=True
)