# Dill Flowers simple shop

Includes fixed everyday-flower and voucher products, product ordering pages, comments/preferences per basket item, basket, checkout/order submission, weddings consultation, newsletter and owner image/product editing.

Orders are requests, not card payments. After submission Dill Flowers confirms availability, fulfilment and payment separately. Order data, consultations and newsletter emails are stored in `data/site.db`.

Set `DILL_ADMIN_KEY`, `DILL_SECRET_KEY` and optionally `DILL_DATA_DIR` on the server. Copy `logo.png` to `static/imgs/`. Uploaded images are also saved there.
