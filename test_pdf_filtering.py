#!/usr/bin/env python3
"""
Test PDF filtering logic
"""

def test_pdf_filtering():
    test_urls = [
        "https://nyswicvendors.com/wp-content/uploads/2018/07/Canned-Vegetables-and-Fruits-Jul-12.pdf",
        "https://example.com/document.pdf",
        "https://example.com/uploads/file.pdf",
        "https://wordpress.com/wp-content/uploads/2023/document.pdf",
        "https://amazon.com/product/B123456",
        "https://walmart.com/product/item",
        "https://example.com/file.pdf?download=true",
        "https://example.com/file.pdf#page=1"
    ]
    
    for url in test_urls:
        link_lower = url.lower()
        
        # Same logic as in the app
        is_pdf = (
            link_lower.endswith('.pdf') or
            'filetype:pdf' in link_lower or
            '.pdf' in link_lower or  # This should catch the nyswicvendors example
            '/uploads/' in link_lower and ('pdf' in link_lower or link_lower.endswith('.pdf')) or
            'wp-content' in link_lower and ('pdf' in link_lower or link_lower.endswith('.pdf')) or
            '/wp-content/uploads/' in link_lower or  # Common WordPress PDF path
            '.pdf?' in link_lower or  # PDFs with query parameters
            '.pdf#' in link_lower    # PDFs with anchors
        )
        
        status = "🔴 FILTERED (PDF)" if is_pdf else "🟢 ALLOWED"
        print(f"{status}: {url}")

if __name__ == "__main__":
    test_pdf_filtering()
