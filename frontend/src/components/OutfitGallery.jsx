import { useState } from "react";
import { generateOutfit } from "../api.js";
import { googleShoppingUrl } from "../shopping.js";

// One outfit product card: image/preview area on top, details + Buy links below.
function OutfitCard({ outfit, imageB64 }) {
  const [status, setStatus] = useState("idle"); // idle | loading | done | error
  const [img, setImg] = useState(null);
  const [error, setError] = useState("");

  async function onGenerate() {
    setStatus("loading");
    setError("");
    try {
      const b64 = await generateOutfit(imageB64, outfit.image_prompt);
      setImg(`data:image/png;base64,${b64}`);
      setStatus("done");
    } catch (e) {
      setError(e.message);
      setStatus("error");
    }
  }

  return (
    <div className="outfit-card">
      <div className="outfit-visual">
        {status === "done" && img ? (
          <img src={img} alt={outfit.occasion} className="outfit-img" />
        ) : status === "loading" ? (
          <div className="spinner-box">
            <div className="spinner" />
            <span>Generating…</span>
          </div>
        ) : (
          <div className="spinner-box">
            <button className="btn" onClick={onGenerate}>✨ Generate look</button>
            {status === "error" && <p className="error small">{error}</p>}
          </div>
        )}
      </div>

      <div className="outfit-body">
        <h4>{outfit.occasion}</h4>
        <ul className="outfit-items">
          {outfit.items.map((item, i) => (
            <li key={i} className="outfit-item">
              <span className="desc">
                <b>{item.category}:</b> {item.description}
              </span>
              <a
                className="buy-link"
                href={googleShoppingUrl(item.shopping_query)}
                target="_blank"
                rel="noopener noreferrer"
              >
                🛒 Buy
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default function OutfitGallery({ outfits, imageB64 }) {
  return (
    <div className="outfit-grid">
      {outfits.map((o, i) => (
        <OutfitCard key={i} outfit={o} imageB64={imageB64} />
      ))}
    </div>
  );
}
