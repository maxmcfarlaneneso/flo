# Dill Flowers

Complete Flask site for dillflowers.com.

## Files

```text
dill-flowers/
├── app.py
├── requirements.txt
├── .gitignore
├── data/
├── templates/
│   └── index.html
└── static/
    ├── app.js
    ├── style.css
    └── imgs/
        ├── logo.png
        └── your flower images...
```

## Local run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Set an owner password:

PowerShell:
```powershell
$env:DILL_ADMIN_KEY = "choose-a-long-private-password"
python app.py
```

Bash:
```bash
export DILL_ADMIN_KEY="choose-a-long-private-password"
python app.py
```

Then open http://127.0.0.1:5000.

## Images

Copy `logo.png` and the flower photos into `static/imgs/`.

`logo.png` is deliberately excluded from the product image picker and public gallery. PNG, JPG, JPEG and WebP flower photos are supported.

## Persistent catalogue

The app stores bouquet names, prices, assigned images, Shopify URLs and stock status in:

```text
data/bouquets.db
```

The database is created automatically and is not committed to Git.

On PythonAnywhere, you can retain the default `data/` folder, or set a separate persistent directory before importing the app in the WSGI file:

```python
import os
os.environ["DILL_ADMIN_KEY"] = "your-private-password"
os.environ["DILL_DATA_DIR"] = "/home/YOUR_USERNAME/dillflowers-data"
```

Then import the Flask app:

```python
import sys
project_home = "/home/YOUR_USERNAME/YOUR_REPO"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import app as application
```

## Existing database

If you already have a working `bouquets.db`, copy it into `data/bouquets.db` before starting this version. Do not overwrite it if it contains the live catalogue.

## Owner controls

Click `Owner` beside the bouquet section, enter `DILL_ADMIN_KEY`, then you can:

- add bouquets
- choose an image or pick one randomly
- set the price
- add the Shopify product URL
- toggle in/out of stock
- remove bouquets

## Useful endpoints

- `/` site
- `/health` simple health check
- `/api/images` authenticated image list
- `/api/bouquets` authenticated create endpoint


## Editing from the storefront

While the owner session is active, public bouquet cards show an **Edit** button instead of the customer purchase action. Clicking it opens Owner controls and scrolls directly to that bouquet's editor. The admin header stays sticky so Close and Log out remain accessible while scrolling. Shopify URLs are optional; when blank, the public card simply has no View button.


## Owner image uploads

When adding a bouquet, the owner can upload a PNG, JPG/JPEG or WebP image directly from the modal. Uploads require an authenticated owner session, are limited to 10 MB, are saved into `static/imgs`, and are automatically given a collision-safe filename. The newly uploaded file is immediately assigned to the new bouquet and also becomes part of the public gallery. On PythonAnywhere, make sure `static/imgs` is writable by the web app user.
