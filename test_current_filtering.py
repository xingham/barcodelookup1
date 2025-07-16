#!/usr/bin/env python3
"""
Test what URLs are actually being returned and check PDF filtering
"""

from googleapiclient.discovery import build
import streamlit as st
from urllib.parse import urlparse

# Load secrets
GOOGLE_API_KEYS = st.secrets["GOOGLE_API_KEYS"]
GOOGLE_CSE_ID = st.secrets["GOOGLE_CSE_ID"]

def test_current_search():
    api_key = GOOGLE_API_KEYS[0]
    service = build('customsearch', 'v1', developerKey=api_key)
    
    barcode = "072940755005"
    optimized_query = f"{barcode} OR UPC {barcode} OR {barcode} amazon"
    
    print(f"🔍 Testing current search query: '{optimized_query}'")
    
    result = service.cse().list(
        q=optimized_query,
        cx=GOOGLE_CSE_ID,
        num=10,
        start=1
    ).execute()
    
    print(f"📊 Total results returned: {len(result.get('items', []))}")
    
    if 'items' in result:
        print("\n📋 All URLs found:")
        for i, item in enumerate(result['items'], 1):
            title = item.get('title', '')
            link = item.get('link', '')
            
            # Test the PDF filtering logic
            link_lower = link.lower()
            snippet_lower = item.get('snippet', '').lower()
            title_upper = title.upper()
            
            # Same exact logic as in the app
            is_pdf = (
                link_lower.endswith('.pdf') or
                'filetype:pdf' in link_lower or
                '.pdf' in link_lower or  # This should catch the nyswicvendors example
                '/uploads/' in link_lower and ('pdf' in link_lower or link_lower.endswith('.pdf')) or
                'wp-content' in link_lower and ('pdf' in link_lower or link_lower.endswith('.pdf')) or
                '/wp-content/uploads/' in link_lower or  # Common WordPress PDF path
                'pdf' in snippet_lower or
                '[PDF]' in title or
                'PDF' in title_upper or
                title_upper.endswith('.PDF') or
                '.pdf?' in link_lower or  # PDFs with query parameters
                '.pdf#' in link_lower    # PDFs with anchors
            )
            
            status = "🔴 FILTERED (PDF)" if is_pdf else "🟢 ALLOWED"
            domain = urlparse(link).netloc
            
            print(f"  {i}. {status} - {domain}")
            print(f"     Title: {title}")
            print(f"     URL: {link}")
            
            # Show why it was filtered if it's a PDF
            if is_pdf:
                reasons = []
                if link_lower.endswith('.pdf'):
                    reasons.append("ends with .pdf")
                if '.pdf' in link_lower:
                    reasons.append("contains .pdf")
                if '/wp-content/uploads/' in link_lower:
                    reasons.append("wp-content/uploads path")
                if 'pdf' in snippet_lower:
                    reasons.append("pdf in snippet")
                if '[PDF]' in title or 'PDF' in title_upper:
                    reasons.append("PDF in title")
                print(f"     Filtered because: {', '.join(reasons)}")
            
            print()

if __name__ == "__main__":
    test_current_search()
