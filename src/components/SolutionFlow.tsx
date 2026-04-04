export default function SolutionFlow() {
  return (
    <section className="panel full-center" id="solution">
      <div className="content-block text-center">
        <h2 className="section-title">The actual pipeline.</h2>
        <p className="section-desc">From raw upload to perfect submission.</p>
        
        <div className="flow-pipeline">
          <div className="flow-step">1. Upload File</div>
          <div className="flow-arrow">&rarr;</div>
          <div className="flow-step active">2. Parse to JSON</div>
          <div className="flow-arrow">&rarr;</div>
          <div className="flow-step">3. Validate Rules</div>
          <div className="flow-arrow">&rarr;</div>
          <div className="flow-step">4. Fix via AI</div>
          <div className="flow-arrow">&rarr;</div>
          <div className="flow-step">5. Download EDI</div>
        </div>
      </div>
    </section>
  )
}
