// Renders a row of color swatches with names + hex codes.
export default function ColorPalette({ title, colors }) {
  return (
    <div className="palette">
      <h4>{title}</h4>
      <div className="swatches">
        {colors.map((c, i) => (
          <div className="swatch" key={i}>
            <span className="chip" style={{ background: c.hex }} title={c.hex} />
            <span className="swatch-name">{c.name}</span>
            <span className="swatch-hex">{c.hex}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
