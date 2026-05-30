import ColorPalette from "./ColorPalette.jsx";
import OutfitGallery from "./OutfitGallery.jsx";

function Tags({ items }) {
  return (
    <div className="tags">
      {items.map((t, i) => (
        <span className="tag" key={i}>
          {t}
        </span>
      ))}
    </div>
  );
}

// Renders the full Style Blueprint in Samsung-style bands.
export default function BlueprintReport({ blueprint, imageB64, measurementImage }) {
  const {
    overall_summary,
    silhouette_profile: sil,
    facial_architecture: face,
    chromatic_harmony: color,
    body_measurements: bm,
    outfit_formulas,
    concern_zone_solutions,
  } = blueprint;

  return (
    <>
      {/* Summary band — photo + summary + key stats */}
      <section className="band">
        <div className="wrap">
          <div className="summary-grid">
            <div className="summary-text">
              <h2>Your Style Summary</h2>
              <p>{overall_summary}</p>
              <div className="stat-row">
                <div className="stat">
                  <div className="k">Body shape</div>
                  <div className="v">{sil.body_shape}</div>
                </div>
                <div className="stat">
                  <div className="k">Face shape</div>
                  <div className="v">{face.face_shape}</div>
                </div>
                <div className="stat">
                  <div className="k">Undertone</div>
                  <div className="v">{color.skin_undertone}</div>
                </div>
                <div className="stat">
                  <div className="k">Season</div>
                  <div className="v">{color.season}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Body Measurements — generated overlay image */}
      {measurementImage && (
        <section className="band">
          <div className="wrap">
            <div className="section-head">
              <h2>Body Measurements</h2>
              <p className="sub">Approximate measurements read from your upload — in centimetres.</p>
            </div>
            <img
              className="measure-image"
              src={`data:image/jpeg;base64,${measurementImage}`}
              alt="Your measurements"
            />
            {bm && (
              <p className="muted measure-caption">
                Suggested sizes: Top <b>{bm.recommended_top_size}</b> · Bottom{" "}
                <b>{bm.recommended_bottom_size}</b>. {bm.note}
              </p>
            )}
          </div>
        </section>
      )}

      {/* Silhouette + Facial — 2-up grid */}
      <section className="band">
        <div className="wrap">
          <div className="section-head">
            <h2>Your shape &amp; features</h2>
            <p className="sub">What flatters your silhouette and face.</p>
          </div>
          <div className="two-up">
            <div className="card feature">
              <h3>Geometric Silhouette Profile</h3>
              <p><b>Body shape:</b> {sil.body_shape}</p>
              <p><b>Shoulder / hip:</b> {sil.shoulder_hip_read}</p>
              <p><b>Torso:</b> {sil.torso_length}</p>
              <p className="label">Flattering silhouettes</p>
              <Tags items={sil.flattering_silhouettes} />
              <p className="label">Silhouettes to avoid</p>
              <Tags items={sil.silhouettes_to_avoid} />
            </div>
            <div className="card feature">
              <h3>Facial Architecture Analysis</h3>
              <p><b>Face shape:</b> {face.face_shape}</p>
              <p className="label">Necklines</p>
              <Tags items={face.recommended_necklines} />
              <p className="label">Earrings</p>
              <Tags items={face.earring_shapes} />
              <p className="label">Eyewear</p>
              <Tags items={face.eyewear_shapes} />
            </div>
          </div>
        </div>
      </section>

      {/* Chromatic harmony */}
      <section className="band">
        <div className="wrap">
          <div className="section-head">
            <h2>Chromatic Harmony Map</h2>
            <p className="sub">
              Undertone: <b>{color.skin_undertone}</b> · Season: <b>{color.season}</b>
            </p>
          </div>
          <div className="card">
            <ColorPalette title="Colors that flatter you" colors={color.flattering_colors} />
            <ColorPalette title="Colors to avoid" colors={color.avoid_colors} />
          </div>
        </div>
      </section>

      {/* Outfit formulas — product grid */}
      <section className="band" id="looks-grid">
        <div className="wrap">
          <div className="section-head">
            <h2>Your Outfit Formulas</h2>
            <p className="sub">
              {outfit_formulas.length} looks. Tap <b>Buy</b> on any piece, or
              <b> Generate look</b> to see yourself wearing it.
            </p>
          </div>
          <OutfitGallery outfits={outfit_formulas} imageB64={imageB64} />
        </div>
      </section>

      {/* Concern zones */}
      <section className="band">
        <div className="wrap">
          <div className="section-head">
            <h2>Concern Zone Solutions</h2>
            <p className="sub">Targeted tips for the areas you care about.</p>
          </div>
          <div className="concern-grid">
            {concern_zone_solutions.map((c, i) => (
              <div className="concern-card" key={i}>
                <h4>{c.zone}</h4>
                <p>{c.advice}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
