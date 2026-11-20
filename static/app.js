const $ = (s) => document.querySelector(s),
  $$ = (s) => [...document.querySelectorAll(s)];
const modal = $("#admin-modal"),
  login = $("#admin-login"),
  statusPanel = $("#admin-session"),
  controls = $("#admin-controls"),
  message = $("#admin-message");
function state(on) {
  if (login) login.hidden = on;
  if (statusPanel) statusPanel.hidden = !on;
  if (controls) controls.hidden = !on;
}
async function api(url, options = {}) {
  const r = await fetch(url, {
    ...options,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (!r.ok) {
    let d = "Request failed";
    try {
      d = (await r.json()).error || d;
    } catch (_) {}
    if (r.status === 401) state(false);
    throw new Error(d);
  }
  return r;
}
async function check() {
  const d = await (await fetch("/api/admin/status")).json();
  state(d.authenticated);
}
$("#open-admin")?.addEventListener("click", async () => {
  modal.showModal();
  await check();
});
$("#close-admin")?.addEventListener("click", () => modal.close());
$("#admin-login-button")?.addEventListener("click", async () => {
  try {
    await api("/api/admin/login", {
      method: "POST",
      body: JSON.stringify({ key: $("#admin-key").value }),
    });
    state(true);
  } catch (e) {
    message.textContent = e.message;
  }
});
$("#admin-logout-button")?.addEventListener("click", async () => {
  await fetch("/api/admin/logout", { method: "POST" });
  state(false);
});
async function upload(input) {
  if (!input.files.length) return "";
  const body = new FormData();
  body.append("image", input.files[0]);
  const r = await fetch("/api/images/upload", {
    method: "POST",
    body,
    credentials: "same-origin",
  });
  if (!r.ok) throw new Error((await r.json()).error);
  return (await r.json()).filename;
}
$$(".image-editor").forEach((form) =>
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const image = await upload(form.querySelector("input[type=file]"));
      await api(`/api/content-image/${form.dataset.slot}`, {
        method: "PATCH",
        body: JSON.stringify({ image }),
      });
      location.reload();
    } catch (x) {
      message.textContent = x.message;
    }
  }),
);
$$(".product-editor").forEach((form) =>
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    data.active = form.querySelector("[name=active]").checked;
    try {
      const file = form.querySelector("[name=image_upload]");
      if (file.files.length) data.image = await upload(file);
      await api(`/api/products/${form.dataset.id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
      location.reload();
    } catch (x) {
      message.textContent = x.message;
    }
  }),
);
