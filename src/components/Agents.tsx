export default function Agents() {
  return (
    <section className="panel full-center" id="agents">
      <div className="content-block text-center" style={{ maxWidth: '900px' }}>
        <h2 className="section-title text-glow">Powered by<br/>Specialized AI Agents.</h2>
        <div className="agents-grid">
           <div className="agent-card">
             <h3>Parser Agent</h3>
             <p>Converts raw X12 EDI text into exact JSON structures.</p>
           </div>
           <div className="agent-card">
             <h3>Explainer Agent</h3>
             <p>Translates cryptic SNIP errors into plain English.</p>
           </div>
           <div className="agent-card">
             <h3>Validator Agent</h3>
             <p>Applies thousands of WEDI SNIP & HIPAA rules.</p>
           </div>
           <div className="agent-card">
             <h3>Fix Agent</h3>
             <p>Cross-references directories to suggest precise corrections.</p>
           </div>
        </div>
      </div>
    </section>
  )
}
