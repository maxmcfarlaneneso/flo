# Dill Flowers

A simple Flask storefront with an owner modal for adding/removing bouquets and changing stock status.

## Install and run

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
set DILL_ADMIN_KEY=choose-a-long-private-password
python app.py
```

For PowerShell, set the key with:

```powershell
$env:DILL_ADMIN_KEY = "choose-a-long-private-password"
python app.py
```

Open http://127.0.0.1:5000. Use the small **Owner** link in the Flowers section and enter the same admin key.

## Images

Copy PNG, JPG or WebP files into `static/imgs`. When a bouquet is added with **Choose randomly**, the server selects a random image from that folder. Existing seed products also receive random images when the database is first created.

Delete `bouquets.db` once if you want the three starter bouquets to be regenerated with fresh random images.

## Shopify

Paste the relevant Shopify product URL when adding a bouquet. Until then, the URL can be left blank.

## Before putting it online

Do not use the default `change-me` admin key in production. Set `DILL_ADMIN_KEY` in the hosting provider's environment-variable settings. The SQLite database is suitable for this small single-owner site, but your host must provide persistent storage or the catalogue will reset on redeployment.
