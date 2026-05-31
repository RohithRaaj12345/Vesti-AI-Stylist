// Fetch wrappers + auth. The session token is kept in localStorage and sent as
// `Authorization: Bearer <token>` on every request.

const TOKEN_KEY = "vesti_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

function authHeaders(extra = {}) {
  const t = getToken();
  return t ? { ...extra, Authorization: `Bearer ${t}` } : extra;
}

async function readError(res) {
  try {
    const data = await res.json();
    return data.detail || res.statusText;
  } catch {
    return res.statusText;
  }
}

// JSON request helper that surfaces 401 by clearing the stale token.
async function jsonFetch(url, body, method = "POST") {
  const res = await fetch(url, {
    method,
    headers: authHeaders(body ? { "Content-Type": "application/json" } : {}),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) {
    clearToken();
    throw new Error(await readError(res));
  }
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

// ---- Auth ----
export const register = (payload) => jsonFetch("/api/auth/register", payload);
export const verifyOtp = (email, channel, code) =>
  jsonFetch("/api/auth/verify", { email, channel, code });
export const resendOtp = (email, channel) =>
  jsonFetch("/api/auth/resend-otp", { email, channel });

export async function login(email, password) {
  const data = await jsonFetch("/api/auth/login", { email, password });
  setToken(data.token);
  return data;
}

export async function logout() {
  try {
    await fetch("/api/auth/logout", { method: "POST", headers: authHeaders() });
  } catch {
    /* ignore */
  }
  clearToken();
}

// Returns { name, email } if logged in, else null.
export async function me() {
  if (!getToken()) return null;
  const res = await fetch("/api/auth/me", { headers: authHeaders() });
  if (!res.ok) {
    if (res.status === 401) clearToken();
    return null;
  }
  return res.json();
}

// ---- Styling ----
// Upload a photo OR video -> { blueprint, base_image_b64, measurement_image_b64 }.
export async function analyzePhoto(file) {
  const form = new FormData();
  form.append("photo", file);
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: authHeaders(), // no Content-Type: browser sets the multipart boundary
    body: form,
  });
  if (res.status === 401) {
    clearToken();
    throw new Error(await readError(res));
  }
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

// Generate one outfit image on demand.
export async function generateOutfit(imageB64, imagePrompt) {
  const data = await jsonFetch("/api/generate-outfit", {
    image_b64: imageB64,
    image_prompt: imagePrompt,
  });
  return data.image_b64;
}
