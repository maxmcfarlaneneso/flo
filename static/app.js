const modal = document.querySelector("#admin-modal");
const keyInput = document.querySelector("#admin-key");
const message = document.querySelector("#admin-message");
const imageSelect = document.querySelector("#image-select");

function adminHeaders() {
  return {"Content-Type": "application/json", "X-Admin-Key": keyInput.value};
}

async function request(url, options = {}) {
  const response = await fetch(url, {...options, headers: {...adminHeaders(), ...(options.headers || {})}});
  if (!response.ok) {
    let detail = "Request failed";
    try { detail = (await response.json()).error || detail; } catch (_) {}
    if (response.status === 401) detail = "Incorrect admin key";
    throw new Error(detail);
  }
  return response;
}

async function loadImages() {
  try {
    const response = await request("/api/images");
    const images = await response.json();
    imageSelect.innerHTML = '<option value="">Choose randomly</option>' + images.map(image => `<option value="${image}">${image}</option>`).join("");
    message.textContent = `${images.length} image${images.length === 1 ? "" : "s"} available.`;
  } catch (error) {
    message.textContent = error.message;
  }
}

document.querySelector("#open-admin").addEventListener("click", () => modal.showModal());
document.querySelector("#close-admin").addEventListener("click", () => modal.close());
keyInput.addEventListener("change", loadImages);

document.querySelector("#add-bouquet-form").addEventListener("submit", async event => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const data = Object.fromEntries(form.entries());
  data.in_stock = form.get("in_stock") === "on";
  try {
    await request("/api/bouquets", {method: "POST", body: JSON.stringify(data)});
    location.reload();
  } catch (error) { message.textContent = error.message; }
});

document.querySelectorAll(".stock-toggle").forEach(toggle => {
  toggle.addEventListener("change", async event => {
    const id = event.target.closest(".admin-product").dataset.id;
    try {
      await request(`/api/bouquets/${id}`, {method: "PATCH", body: JSON.stringify({in_stock: event.target.checked})});
      location.reload();
    } catch (error) {
      event.target.checked = !event.target.checked;
      message.textContent = error.message;
    }
  });
});

document.querySelectorAll(".delete-button").forEach(button => {
  button.addEventListener("click", async event => {
    const row = event.target.closest(".admin-product");
    if (!confirm(`Remove ${row.querySelector("strong").textContent}?`)) return;
    try {
      await request(`/api/bouquets/${row.dataset.id}`, {method: "DELETE"});
      location.reload();
    } catch (error) { message.textContent = error.message; }
  });
});
