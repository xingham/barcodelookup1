# Barcode Product Lookup

A web application that looks up product information using barcodes from UPCItemDB and Google search results.

## Requirements
- Python 3.x installed on your computer (install from python.org if needed)
- Internet connection

## How to Use

### Windows Instructions
1. Unzip the project files to your Downloads folder

2. Open Command Prompt:
   - Press Windows + R
   - Type cmd and press Enter

3. Copy and paste these commands:
```cmd
cd %USERPROFILE%\Downloads\barcode_scraper
python -m pip install -r requirements.txt
python app.py
```

### Mac Instructions
1. Unzip the project files into your Downloads folder

2. Open Terminal:
   - Press Command + Space
   - Type Terminal and press Enter

3. Copy and paste these commands:
```bash
cd ~/Downloads/barcode_scraper
python3 -m pip install -r requirements.txt
python3 app.py
```

### For Both Operating Systems
4. Open your web browser and go to:
   http://127.0.0.1:5001

5. Enter a barcode number and click Search

## Troubleshooting

If you see command not found: python:
- Use python3 instead of python in all commands

If Python is not installed:
1. Download Python from https://www.python.org/downloads/
2. Run the installer
3. Restart your Terminal
4. Start again from step 3 above

If the URL doesn't work:
1. Check if the application is running - you should see this message in Terminal:
   * Running on http://0.0.0.0:5001
   * Press CTRL+C to quit
2. Try these alternative URLs in Chrome:
   - http://127.0.0.1:5001
   - http://localhost:5001
   - http://0.0.0.0:5001
3. Make sure no error messages appear in the Terminal
4. Check if any firewall settings are blocking port 5001

## Features
- Searches UPCItemDB for product details
- Shows Google search results
- Displays product variants if available
- Shows detailed product information including:
  - Brand
  - Weight
  - Dimensions
  - Model number