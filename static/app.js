const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];

const announcements = $$('.announcement-message');
let announcementIndex = 0;
let announcementTimer;
function showAnnouncement(index) {
  if (!announcements.length) return;
  announcementIndex = (index + announcements.length) % announcements.length;
  announcements.forEach((item, i) => item.classList.toggle('active', i === announcementIndex));
}
function restartAnnouncements() {
  clearInterval(announcementTimer);
  announcementTimer = setInterval(() => showAnnouncement(announcementIndex + 1), 5000);
}
$('#announcement-prev')?.addEventListener('click', () => { showAnnouncement(announcementIndex - 1); restartAnnouncements(); });
$('#announcement-next')?.addEventListener('click', () => { showAnnouncement(announcementIndex + 1); restartAnnouncements(); });
restartAnnouncements();

const drawer = $('#drawer');
const overlay = $('#drawer-overlay');
function setDrawer(open) {
  drawer?.classList.toggle('open', open);
  overlay?.classList.toggle('open', open);
  drawer?.setAttribute('aria-hidden', String(!open));
  document.body.classList.toggle('drawer-open', open);
}
$('#open-menu')?.addEventListener('click', () => setDrawer(true));
$('#close-menu')?.addEventListener('click', () => setDrawer(false));
overlay?.addEventListener('click', () => setDrawer(false));
$$('#drawer a[href^="#"]').forEach(link => link.addEventListener('click', () => setDrawer(false)));

// Bouquet carousels
$$('.product-carousel-shell').forEach(shell => {
  const carousel = shell.querySelector('.product-carousel');
  shell.querySelector('.products-prev')?.addEventListener('click', () => carousel?.scrollBy({left:-carousel.clientWidth * 0.8, behavior:'smooth'}));
  shell.querySelector('.products-next')?.addEventListener('click', () => carousel?.scrollBy({left:carousel.clientWidth * 0.8, behavior:'smooth'}));
});

const galleryItems = $$('.gallery-item');
const lightbox = $('#lightbox');
const lightboxImage = $('#lightbox-image');
const lightboxCounter = $('#lightbox-counter');
let galleryIndex = 0;
function showGalleryImage(index) {
  if (!galleryItems.length || !lightboxImage) return;
  galleryIndex = (index + galleryItems.length) % galleryItems.length;
  lightboxImage.src = galleryItems[galleryIndex].dataset.full;
  if (lightboxCounter) lightboxCounter.textContent = `${galleryIndex + 1} / ${galleryItems.length}`;
}
galleryItems.forEach((item, index) => item.addEventListener('click', () => {
  showGalleryImage(index);
  if (typeof lightbox?.showModal === 'function') lightbox.showModal();
}));
$('#lightbox-close')?.addEventListener('click', () => lightbox?.close());
$('#lightbox-prev')?.addEventListener('click', () => showGalleryImage(galleryIndex - 1));
$('#lightbox-next')?.addEventListener('click', () => showGalleryImage(galleryIndex + 1));
lightbox?.addEventListener('click', event => { if (event.target === lightbox) lightbox.close(); });
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') setDrawer(false);
  if (!lightbox?.open) return;
  if (event.key === 'ArrowLeft') showGalleryImage(galleryIndex - 1);
  if (event.key === 'ArrowRight') showGalleryImage(galleryIndex + 1);
});

// Owner controls - one login, then a 10-minute server-side session.
const adminModal=$('#admin-modal'),keyInput=$('#admin-key'),message=$('#admin-message'),imageSelect=$('#image-select'),loginPanel=$('#admin-login'),sessionPanel=$('#admin-session'),adminControls=$('#admin-controls');
let availableAdminImages=[];
function setMessage(text,error=false){if(message){message.textContent=text;message.style.color=error?'#9b3d32':'#536158'}}
function showLoggedIn(){if(loginPanel)loginPanel.hidden=true;if(sessionPanel)sessionPanel.hidden=false;if(adminControls)adminControls.hidden=false}
function showLoggedOut(){if(loginPanel)loginPanel.hidden=false;if(sessionPanel)sessionPanel.hidden=true;if(adminControls)adminControls.hidden=true;if(keyInput)keyInput.value=''}
async function apiRequest(url,options={}){const response=await fetch(url,{...options,credentials:'same-origin',headers:{'Content-Type':'application/json',...(options.headers||{})}});if(!response.ok){let detail=response.status===401?'Owner session expired. Please log in again.':`Request failed (${response.status})`;try{detail=(await response.json()).error||detail}catch(_){}if(response.status===401)showLoggedOut();throw new Error(detail)}return response}
function populateImageSelect(select,current=''){if(select)select.innerHTML='<option value="">No image / choose randomly when adding</option>'+availableAdminImages.map(image=>`<option value="${image}" ${image===current?'selected':''}>${image}</option>`).join('')}
async function loadImages(){availableAdminImages=await(await apiRequest('/api/images')).json();populateImageSelect(imageSelect);$$('.edit-image-select').forEach(select=>populateImageSelect(select,select.dataset.current||''))}
async function checkAdminSession(){try{const data=await(await fetch('/api/admin/status',{credentials:'same-origin'})).json();if(data.authenticated){showLoggedIn();await loadImages()}else showLoggedOut()}catch(_){showLoggedOut()}}
async function loginAdmin(){try{await apiRequest('/api/admin/login',{method:'POST',body:JSON.stringify({key:keyInput?.value||''})});showLoggedIn();setMessage('Logged in.');await loadImages()}catch(error){setMessage(error.message,true)}}
$('#open-admin')?.addEventListener('click',async()=>{adminModal?.showModal();await checkAdminSession()});
$$('[data-edit-bouquet]').forEach(button => button.addEventListener('click', async () => {
  if (typeof adminModal?.showModal === 'function' && !adminModal.open) adminModal.showModal();
  await checkAdminSession();
  if (!adminControls || adminControls.hidden) return;
  const editor = $(`#edit-bouquet-${button.dataset.editBouquet}`);
  editor?.scrollIntoView({behavior:'smooth', block:'center'});
  editor?.classList.add('editing-highlight');
  setTimeout(() => editor?.classList.remove('editing-highlight'), 1600);
}));

$('#close-admin')?.addEventListener('click',()=>adminModal?.close());
$('#admin-login-button')?.addEventListener('click',loginAdmin);
keyInput?.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();loginAdmin()}});
$('#admin-logout-button')?.addEventListener('click',async()=>{try{await fetch('/api/admin/logout',{method:'POST',credentials:'same-origin'})}finally{showLoggedOut();setMessage('Logged out.')}});
$('#add-bouquet-form')?.addEventListener('submit',async event=>{event.preventDefault();const form=new FormData(event.currentTarget),data=Object.fromEntries(form.entries());data.in_stock=form.get('in_stock')==='on';try{await apiRequest('/api/bouquets',{method:'POST',body:JSON.stringify(data)});location.reload()}catch(error){setMessage(error.message,true)}});
$$('.edit-bouquet-form').forEach(element=>element.addEventListener('submit',async event=>{event.preventDefault();const form=new FormData(element),data=Object.fromEntries(form.entries());data.in_stock=form.get('in_stock')==='on';try{await apiRequest(`/api/bouquets/${element.dataset.id}`,{method:'PATCH',body:JSON.stringify(data)});setMessage(`Saved ${data.name}. Refresh to see category-row changes.`)}catch(error){setMessage(error.message,true)}}));
$$('.delete-button').forEach(button=>button.addEventListener('click',async event=>{const row=event.target.closest('.edit-bouquet-form'),name=row?.querySelector('[name="name"]')?.value||'this bouquet';if(!row||!confirm(`Remove ${name}?`))return;try{await apiRequest(`/api/bouquets/${row.dataset.id}`,{method:'DELETE'});row.remove();setMessage(`Removed ${name}.`)}catch(error){setMessage(error.message,true)}}));
