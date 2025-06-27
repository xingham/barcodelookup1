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
        console.log('Received data:', data); // Debug log
        
        // Clear and hide all sections first
        ['upcitemdb', 'barcodelookup', 'google'].forEach(section => {
            const elem = document.getElementById(`${section}-results`);
            const content = elem.querySelector('.result-content');
            content.innerHTML = '';
            elem.style.display = 'none';
        });

        // Handle UPCItemDB results
        if (data.upcitemdb && data.upcitemdb.length > 0) {
            const upcSection = document.getElementById('upcitemdb-results');
            const upcContent = upcSection.querySelector('.result-content');
            upcSection.style.display = 'block';
            
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
        }

        // Handle Barcode Lookup results
        if (data.barcodelookup && data.barcodelookup.length > 0) {
            const barcodeSection = document.getElementById('barcodelookup-results');
            const barcodeContent = barcodeSection.querySelector('.result-content');
            barcodeSection.style.display = 'block';
            
            data.barcodelookup.forEach(result => {
                const resultHtml = `
                    <div class="product-item">
                        <div class="product-details">
                            <p><strong>${result.title || 'No title available'}</strong></p>
                            ${result.brand ? `<p>Brand: ${result.brand}</p>` : ''}
                            ${result.manufacturer ? `<p>Manufacturer: ${result.manufacturer}</p>` : ''}
                            ${result.category ? `<p>Category: ${result.category}</p>` : ''}
                            ${result.size ? `<p>Size: ${result.size}</p>` : ''}
                            ${result.description ? `<p>${result.description}</p>` : ''}
                        </div>
                        <p class="upc-link">
                            <a href="${result.link}" target="_blank">View on Barcode Lookup →</a>
                        </p>
                    </div>
                `;
                barcodeContent.innerHTML += resultHtml;
            });
        }

        // Handle Google results
        if (data.google && data.google.length > 0) {
            const googleSection = document.getElementById('google-results');
            const googleContent = googleSection.querySelector('.result-content');
            googleSection.style.display = 'block';
            
            data.google.forEach(result => {
                const resultInfo = document.createElement('div');
                resultInfo.className = 'search-result';
                const domain = new URL(result.link).hostname.replace('www.', '');
                resultInfo.innerHTML = `
                    <p><strong>${domain}:</strong> 
                    <a href="${result.link}" target="_blank">${result.title}</a></p>
                    ${result.description ? `<p>${result.description}</p>` : ''}
                `;
                googleContent.appendChild(resultInfo);
            });
        }

        // Show "No results" message if no results found
        ['upcitemdb', 'barcodelookup', 'google'].forEach(section => {
            const elem = document.getElementById(`${section}-results`);
            const content = elem.querySelector('.result-content');
            if (content.innerHTML === '') {
                content.innerHTML = '<div class="no-results"><p>No results found</p></div>';
                elem.style.display = 'block';
            }
        });
    })
    .catch(error => {
        console.error('Error:', error);
        // Show error in all sections
        ['upcitemdb', 'barcodelookup', 'google'].forEach(section => {
            const elem = document.getElementById(`${section}-results`);
            const content = elem.querySelector('.result-content');
            content.innerHTML = '<div class="error-message">Error searching for barcode</div>';
            elem.style.display = 'block';
        });
    });
}

function createSourceLink(source, url) {
    const arrow = ' →';  // Unicode right arrow
    return `<div class="upc-link">
        <a href="${url}" target="_blank">View on ${source}${arrow}</a>
    </div>`;
}

// Update how links are created for both sources
function displayResults(data) {
    // For UPCItemDB results
    if (data.upcitemdb && data.upcitemdb.length > 0) {
        const upcContent = document.querySelector('#upcitemdb-results .result-content');
        data.upcitemdb.forEach(result => {
            upcContent.innerHTML += createSourceLink('UPCItemDB', result.view_url);
        });
    }
    
    // For Barcode Lookup results
    if (data.barcodelookup && data.barcodelookup.length > 0) {
        const barcodeContent = document.querySelector('#barcodelookup-results .result-content');
        data.barcodelookup.forEach(result => {
            barcodeContent.innerHTML += createSourceLink('Barcode Lookup', result.view_url);
        });
    }
}
