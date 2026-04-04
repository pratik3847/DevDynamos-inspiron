export default function FixSuggestions() {
  return (
    <section className="panel split-left" id="fix-suggestions">
      <div className="content-block">
        <h2 className="section-title">AI Suggests Fixes<br/>You Can Trust.</h2>
        <div className="fix-ui">
          <div className="fix-row">
            <div className="original">Original: <span className="strike">1234567890</span> <span className="text-secondary">(Invalid)</span></div>
            <div className="arrow">&darr;</div>
            <div className="suggested">Suggested: <span className="highlight-green">1245678901</span></div>
          </div>
          <div className="fix-meta">
            <span className="confidence high">High Confidence Validation</span>
            <button className="btn btn-accept">Accept Fix</button>
          </div>
        </div>
      </div>
    </section>
  )
}
