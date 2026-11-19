Dill Flowers UI update

Replace these files in the existing Flask project:
- templates/index.html
- static/style.css
- static/app.js

No app.py/database changes are required. This expects the existing:
- bouquets Jinja variable
- gallery_images Jinja variable
- /api/images
- POST /api/bouquets
- PATCH /api/bouquets/<id>
- DELETE /api/bouquets/<id>

Features added:
- rotating Christmas announcement bar
- centred logo header with call link
- slide-out navigation drawer
- bouquet horizontal carousel while retaining dynamic database products
- automatic gallery with lightbox and keyboard navigation
- logo.png excluded from visible gallery and owner image picker
- improved contact section
- richer footer
- floating phone call button
- existing owner add/remove/in-stock functionality retained
