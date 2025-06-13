function lookupBarcode() {
    const barcode = document.getElementById('barcodeInput').value;
    
    fetch(`/lookup/${barcode}`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Clear previous results
        document.querySelector('#upcitemdb-results .result-content').innerHTML = '';
        document.querySelector('#google-results .result-content').innerHTML = '';
        document.getElementById('upcitemdb-results').style.display = 'none';
        document.getElementById('google-results').style.display = 'none';

        // Show UPCItemDB results section
        document.getElementById('upcitemdb-results').style.display = 'block';
        const upcContent = document.querySelector('#upcitemdb-results .result-content');
        
        // Handle UPCItemDB results
        if (data.upcitemdb && data.upcitemdb.length > 0) {
            data.upcitemdb.forEach(product => {
                const productInfo = document.createElement('div');
                productInfo.className = 'product-item';

                let variantsHtml = '';
                if (product.variants && product.variants.length > 0) {
                    variantsHtml = `<p><strong>Product Variants:</strong></p><ul>${product.variants.map(variant => `<li>${variant}</li>`).join('')}</ul>`;
                }
                
                const upcLink = `<p class="upc-link"><a href="https://www.upcitemdb.com/upc/${barcode}" target="_blank">View on UPCItemDB</a></p>`;
                
                productInfo.innerHTML = `<div class="product-details">${variantsHtml}${upcLink}</div>`;
                
                upcContent.appendChild(productInfo);
            });
        } else {
            upcContent.innerHTML = '<div class="no-results"><p>No results found for this barcode</p></div>';
        }

        // Show Google results section
        document.getElementById('google-results').style.display = 'block';
        const googleContent = document.querySelector('#google-results .result-content');
        
        // Handle Google results
        if (data.google && data.google.length > 0) {
            if (data.google[0].quota_exceeded) {
                googleContent.innerHTML = `<div class="quota-exceeded"><p>${data.google[0].snippet}</p></div>`;
            } else {
                data.google.forEach(result => {
                    const resultInfo = document.createElement('div');
                    resultInfo.className = 'search-result';
                    const domain = new URL(result.link).hostname.replace('www.', '');
                    resultInfo.innerHTML = `<p><strong>${domain}:</strong> <a href="${result.link}" target="_blank">${result.title}</a></p>`;
                    googleContent.appendChild(resultInfo);
                });
            }
        } else {
            googleContent.innerHTML = '<div class="no-results"><p>No results found for this barcode</p></div>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Show error in Google results section only
        const googleContent = document.querySelector('#google-results .result-content');
        googleContent.innerHTML = '<div class="error-message">Error searching for barcode</div>';
        document.getElementById('google-results').style.display = 'block';
    });
}
