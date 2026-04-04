export default function Problem() {
  return (
    <section className="panel split-left" id="problem">
      <div className="content-block">
        <h2 className="section-title">The current reality is broken.</h2>
        <div className="timeline-frustration">
           <div className="tl-step"><span className="tl-dot red"></span>Billing specialist receives rejection</div>
           <div className="tl-step"><span className="tl-dot red"></span>Searches thousands of lines of raw text</div>
           <div className="tl-step"><span className="tl-dot red"></span>2&ndash;3 hours spent debugging per error</div>
           <div className="tl-step"><span className="tl-dot orange"></span>Resubmits the next day</div>
        </div>
        <div className="metrics-grid">
          <div className="metric"><span className="stat">5B+</span><span className="label">Annual EDI Transactions</span></div>
          <div className="metric"><span className="stat">Weeks</span><span className="label">Delay caused by errors</span></div>
        </div>
      </div>
    </section>
  )
}
