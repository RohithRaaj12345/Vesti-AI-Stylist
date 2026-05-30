import { useRef, useState } from "react";

// Lets the user pick / drag a person photo, shows a preview, and triggers analysis.
export default function ImageUploader({ onAnalyze, loading, previewUrl }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  function pick(file) {
    if (file && file.type.startsWith("image/")) onAnalyze(file);
  }

  return (
    <div className="uploader">
      <div
        className={`dropzone ${dragOver ? "drag" : ""}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          pick(e.dataTransfer.files?.[0]);
        }}
      >
        {previewUrl ? (
          <img src={previewUrl} alt="Your photo" className="preview" />
        ) : (
          <div className="dropzone-hint">
            <span className="up-icon">⬆</span>
            <strong>Drag &amp; drop your photo</strong>
            <span>or click to browse — JPEG, PNG or WebP, up to 10 MB</span>
            <span className="pill-hint">Choose photo</span>
          </div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          hidden
          onChange={(e) => pick(e.target.files?.[0])}
        />
      </div>

      {loading && (
        <div className="loading-row">
          <span className="spinner" />
          <span>Analyzing your photo… this takes a few seconds.</span>
        </div>
      )}
    </div>
  );
}
