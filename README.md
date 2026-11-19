# Dill Flowers simple site

A deliberately minimal Flask site with:

- Everyday flowers
- Gift vouchers
- Weddings and events page
- Consultation form
- Consultation submissions stored in `data/consultations.db`

## Run

```bash
python -m venv .venv
pip install -r requirements.txt
python app.py
```

Copy the Dill Flowers `logo.png` into `static/imgs/`.

On PythonAnywhere, preserve the `data/` directory or set `DILL_DATA_DIR` to a persistent location. The consultation database is excluded from Git and from replacement ZIPs.


## Photo placeholders

The simple build now includes obvious placeholders in the homepage hero, everyday flowers section, vouchers section and weddings/events header. Replace a placeholder div with an `<img>` from `static/imgs/` when you choose the photos. The header is sticky and remains visible while scrolling.
