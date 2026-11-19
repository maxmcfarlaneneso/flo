# Dill Flowers
Complete Flask site. The gallery is now a separate `/gallery` page. Flower images in `static/imgs` are discovered automatically, `logo.png` is excluded, and gallery images lazy-load and reveal as they approach the viewport using IntersectionObserver. Existing bouquet image uploads automatically join the gallery.

Keep an existing live database at `data/bouquets.db` (or use `DILL_DATA_DIR`). Set `DILL_ADMIN_KEY` and `DILL_SECRET_KEY` privately on the server.
