import { useRef, useState } from "react";

// Lets the user pick / drag a photo or video, shows a preview, triggers analysis.
export default function ImageUploader({ onAnalyze, loading, previewUrl, previewIsVideo }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  function pick(file) {
    if (file && (file.type.startsWith("image/") || file.type.startsWith("video/"))) {
      onAnalyze(file);
    }
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
          previewIsVideo ? (
            <video src={previewUrl} className="preview" muted autoPlay loop playsInline />
          ) : (
            <img src={previewUrl} alt="Your upload" className="preview" />
          )
        ) : (
          <div className="dropzone-hint">
            <span className="up-icon">⬆</span>
            <strong>Drag &amp; drop your photo or video</strong>
            <span>or click to browse — any image or video, up to 100 MB</span>
            <span className="pill-hint">Choose file</span>
          </div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/*,video/*"
          hidden
          onChange={(e) => pick(e.target.files?.[0])}
        />
      </div>

      {loading && (
        <div className="loading-row">
          <span className="spinner" />
          <span>Analyzing your upload… this can take a few seconds (longer for video).</span>
        </div>
      )}
    </div>
  );
}
