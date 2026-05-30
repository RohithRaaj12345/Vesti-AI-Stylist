import { useState } from "react";
import ImageUploader from "./components/ImageUploader.jsx";
import BlueprintReport from "./components/BlueprintReport.jsx";
import { analyzePhoto, fileToBase64 } from "./api.js";

const STEPS = [
  { n: 1, title: "Upload a photo", text: "Drop in one clear, full-body photo of yourself standing." },
  { n: 2, title: "Get your AI blueprint", text: "Body shape, face analysis, your color palette and 16–20 outfit formulas." },
  { n: 3, title: "Shop & visualize", text: "Buy any item in one click, or generate a photo of you wearing the look." },
];

export default function App() {
  const [previewUrl, setPreviewUrl] = useState(null);
  const [imageB64, setImageB64] = useState(null);
  const [blueprint, setBlueprint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAnalyze(file) {
    setError("");
    setBlueprint(null);
    setLoading(true);
    setPreviewUrl(URL.createObjectURL(file));

    try {
      // Keep the original photo (base64) around for later outfit generation.
      const [bp, b64] = await Promise.all([analyzePhoto(file), fileToBase64(file)]);
      setBlueprint(bp);
      setImageB64(b64);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setPreviewUrl(null);
    setImageB64(null);
    setBlueprint(null);
    setError("");
  }

  return (
    <>
      {/* Sticky nav */}
      <nav className="nav">
        <div className="nav-inner">
          <a className="brand" href="#top">Vesti</a>
          <div className="nav-links">
            <a href="#how">How it works</a>
            <a href="#start">Try it</a>
            <a className="btn sm" href="#start">Get started</a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero" id="top">
        <div className="hero-inner">
          <div>
            <h1>Discover your signature style.</h1>
            <p>
              Upload one photo and let Vesti build your personal AI style blueprint —
              then shop every piece or see yourself in any look.
            </p>
            <div className="hero-cta">
              <a className="btn" href="#start">Get started</a>
              <a className="hero-link" href="#how">How it works →</a>
            </div>
          </div>
          <img className="hero-art" src="/hero.png" alt="A polished look styled with Vesti" />
        </div>
      </section>

      {/* How it works */}
      <section className="band alt" id="how">
        <div className="wrap">
          <div className="section-head">
            <h2>How it works</h2>
            <p className="sub">Three steps from a single photo to a complete, shoppable wardrobe.</p>
          </div>
          <div className="steps">
            {STEPS.map((s) => (
              <div className="step" key={s.n}>
                <span className="num">{s.n}</span>
                <h3>{s.title}</h3>
                <p>{s.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* The tool */}
      <section className="band" id="start">
        <div className="wrap">
          <div className="section-head" style={{ textAlign: "center" }}>
            <h2>{blueprint ? "Your photo" : "Start your blueprint"}</h2>
            <p className="sub">Use a clear, full-body photo for the best analysis.</p>
          </div>
          <ImageUploader onAnalyze={handleAnalyze} loading={loading} previewUrl={previewUrl} />
          {error && <p className="error">{error}</p>}
        </div>
      </section>

      {/* Results */}
      {blueprint && (
        <div className="report" id="looks">
          <div className="wrap toolbar">
            <button className="btn ghost" onClick={reset}>↺ Start over with a new photo</button>
          </div>
          <BlueprintReport blueprint={blueprint} imageB64={imageB64} previewUrl={previewUrl} />
        </div>
      )}

      {/* Footer */}
      <footer className="footer">
        <div className="footer-inner">
          <a className="brand" href="#top">Vesti</a>
          <p className="f-tag">Your AI personal stylist.</p>
        </div>
        <div className="footer-legal">© 2026 Vesti</div>
      </footer>
    </>
  );
}
