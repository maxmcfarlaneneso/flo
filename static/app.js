// Announcement carousel
const announcements = [...document.querySelectorAll('.announcement-message')];
let announcementIndex = 0;
let announcementTimer;
function showAnnouncement(index) {
  if (!announcements.length) return;
  announcementIndex = (index + announcements.length) % announcements.length;
  announcements.forEach((item, i) => item.classList.toggle('active', i === announcementIndex));
}
function startAnnouncements() {
  clearInterval(announcementTimer);
  announcementTimer = setInterval(() => showAnnouncement(announcementIndex + 1), 5000);
}
document.querySelector('#announcement-prev')?.addEventListener('click', () => { showAnnouncement(announcementIndex - 1); startAnnouncements(); });
document.querySelector('#announcement-next')?.addEventListener('click', () => { showAnnouncement(announcementIndex + 1); startAnnouncements(); });
startAnnouncements();

// Drawer
const drawer = document.querySelector('#drawer');
const drawerOverlay = document.querySelector('#drawer-overlay');
function setDrawer(open) {
  drawer?.classList.toggle('open', open);
  drawerOverlay?.classList.toggle('open', open);
  drawer?.setAttribute('aria-hidden', String(!open));
  document.body.classList.toggle('drawer-open', open);
}
document.querySelector('#open-menu')?.addEventListener('click', () => setDrawer(true));
document.querySelector('#close-menu')?.addEventListener('click', () => setDrawer(false));
drawerOverlay?.addEventListener('click', () => setDrawer(false));
drawer?.querySelectorAll('a[href^="#"]').forEach(link => link.addEventListener('click', () => setDrawer(false)));

// Bouquet carousel
const productCarousel = document.querySelector('#product-carousel');
function scrollProducts(direction) {
  if (!productCarousel) return;
  productCarousel.scrollBy({ left: direction * productCarousel.clientWidth * 0.8, behavior: 'smooth' });
}
document.querySelector('.products-prev')?.addEventListener('click', () => scrollProducts(-1));
document.querySelector('.products-next')?.addEventListener('click', () => scrollProducts(1));

// Gallery lightbox
const galleryItems = [...document.querySelectorAll('.gallery-item')];
const lightbox = document.querySelector('#lightbox');
const lightboxImage = document.querySelector('#lightbox-image');
const lightboxCounter = document.querySelector('#lightbox-counter');
let galleryIndex = 0;
function showGalleryImage(index) {
  if (!galleryItems.length || !lightboxImage) return;
  galleryIndex = (index + galleryItems.length) % galleryItems.length;
  lightboxImage.src = galleryItems[galleryIndex].dataset.full;
  lightboxCounter.textContent = `${galleryIndex + 1} / ${galleryItems.length}`;
}
galleryItems.forEach((item, index) => item.addEventListener('click', () => { showGalleryImage(index); lightbox.showModal(); }));
document.querySelector('#lightbox-close')?.addEventListener('click', () => lightbox.close());
document.querySelector('#lightbox-prev')?.addEventListener('click', () => showGalleryImage(galleryIndex - 1));
document.querySelector('#lightbox-next')?.addEventListener('click', () => showGalleryImage(galleryIndex + 1));
lightbox?.addEventListener('click', event => { if (event.target === lightbox) lightbox.close(); });
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') setDrawer(false);
  if (!lightbox?.open) return;
  if (event.key === 'ArrowLeft') showGalleryImage(galleryIndex - 1);
  if (event.key === 'ArrowRight') showGalleryImage(galleryIndex + 1);
});

// Owner controls
const adminModal = document.querySelector('#admin-modal');
const keyInput = document.querySelector('#admin-key');
const message = document.querySelector('#admin-message');
const imageSelect = document.querySelector('#image-select');
function adminHeaders() { return {'Content-Type': 'application/json', 'X-Admin-Key': keyInput?.value || ''}; }
async function adminRequest(url, options = {}) {
  const response = await fetch(url, {...options, headers: {...adminHeaders(), ...(options.headers || {})}});
  if (!response.ok) {
    let detail = 'Request failed';
    try { detail = (await response.json()).error || detail; } catch (_) {}
    if (response.status === 401) detail = 'Incorrect admin key';
    throw new Error(detail);
  }
  return response;
}
async function loadImages() {
  try {
    const response = await adminRequest('/api/images');
    const images = (await response.json()).filter(image => image.toLowerCase() !== 'logo.png');
    imageSelect.innerHTML = '<option value="">Choose randomly</option>' + images.map(image => `<option value="${image}">${image}</option>`).join('');
    message.textContent = `${images.length} image${images.length === 1 ? '' : 's'} available.`;
  } catch (error) { message.textContent = error.message; }
}
document.querySelector('#open-admin')?.addEventListener('click', () => adminModal.showModal());
document.querySelector('#close-admin')?.addEventListener('click', () => adminModal.close());
keyInput?.addEventListener('change', loadImages);
document.querySelector('#add-bouquet-form')?.addEventListener('submit', async event => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const data = Object.fromEntries(form.entries());
  data.in_stock = form.get('in_stock') === 'on';
  try { await adminRequest('/api/bouquets', {method:'POST', body:JSON.stringify(data)}); location.reload(); }
  catch (error) { message.textContent = error.message; }
});
document.querySelectorAll('.stock-toggle').forEach(toggle => toggle.addEventListener('change', async event => {
  const id = event.target.closest('.admin-product').dataset.id;
  try { await adminRequest(`/api/bouquets/${id}`, {method:'PATCH', body:JSON.stringify({in_stock:event.target.checked})}); location.reload(); }
  catch (error) { event.target.checked = !event.target.checked; message.textContent = error.message; }
}));
document.querySelectorAll('.delete-button').forEach(button => button.addEventListener('click', async event => {
  const row = event.target.closest('.admin-product');
  if (!confirm(`Remove ${row.querySelector('strong').textContent}?`)) return;
  try { await adminRequest(`/api/bouquets/${row.dataset.id}`, {method:'DELETE'}); location.reload(); }
  catch (error) { message.textContent = error.message; }
}));
