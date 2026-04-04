export default function UseCases() {
  return (
    <section className="panel split-right" id="use-cases">
      <div className="content-block right-aligned">
        <h2 className="section-title">Real problems.<br/>Solved instantly.</h2>
        
        <div className="cards-stack">
          <div className="case-card">
             <h4>The Missing NPI</h4>
             <p className="case-before">2 hours of research</p>
             <p className="case-after">&rarr; 5 seconds auto-fixed</p>
          </div>
          <div className="case-card mt-2">
             <h4>ICD-10 Code Mismatch</h4>
             <p className="case-reason">Explainer agent details the exact coding conflict instantly.</p>
          </div>
          <div className="case-card mt-2">
             <h4>834 Enrollment Issue</h4>
             <p className="case-reason">Prevents employees from accidentally losing coverage due to syntax bugs.</p>
          </div>
        </div>
      </div>
    </section>
  )
}
