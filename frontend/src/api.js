// Fetch wrappers for the two backend endpoints.

async function readError(res) {
  try {
    const data = await res.json();
    return data.detail || res.statusText;
  } catch {
    return res.statusText;
  }
}

// Upload a person photo -> full StyleBlueprint JSON.
export async function analyzePhoto(file) {
  const form = new FormData();
  form.append("photo", file);

  const res = await fetch("/api/analyze", { method: "POST", body: form });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

// Generate one outfit image on demand.
// imageB64 is the original uploaded photo (base64, no data-URI prefix).
export async function generateOutfit(imageB64, imagePrompt) {
  const res = await fetch("/api/generate-outfit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_b64: imageB64, image_prompt: imagePrompt }),
  });
  if (!res.ok) throw new Error(await readError(res));
  const data = await res.json();
  return data.image_b64;
}

// Read a File into a bare base64 string (strips the "data:...;base64," prefix).
export function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
