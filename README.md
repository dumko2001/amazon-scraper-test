
### 1. Create Virtual Environment
```bash
python3 -m venv venv_final
source venv_final/bin/activate  # On Windows: venv_final\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install playwright playwright-stealth
playwright install chromium
```

### 3. Run the Automation
```bash
python final.py
```

That's it! The script will:
- ✅ Create a new wishlist with timestamp
- ✅ Browse 3 random products naturally  
- ✅ Add a product to the created wishlist
- ✅ Save session for future runs
