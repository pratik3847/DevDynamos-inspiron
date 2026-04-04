export default function Structure() {
  return (
    <section className="panel full-center" id="structure">
      <div className="floating-card structure-card">
        <div className="card-header">
          <span className="dot blue"></span>
          837P Structured Data
        </div>
        <div className="card-body">
          <div className="hierarchy-item title"><span className="badge white">Loop 2000A</span> Billing Provider</div>
          <div className="hierarchy-item sub highlight"><span className="badge blue">NM1</span> PRV Info (NPI: 1234567890)</div>
          <div className="hierarchy-item title mt-2"><span className="badge white">Loop 2300</span> Claim Info</div>
          <div className="hierarchy-item sub"><span className="badge cyan">CLM</span> Health Claim (Amt: $150.00)</div>
          <div className="hierarchy-item sub"><span className="badge cyan">HI</span> Diagnosis (ICD-10: J01.90)</div>
        </div>
      </div>
      
      <div className="content-block bottom-center text-center">
        <h2 className="section-title">From Raw Text to<br/>Structured Data.</h2>
        <p className="section-desc">We convert confusing EDI strings into clean, readable hierarchies. See exactly where your claims, providers, and diagnoses map.</p>
      </div>
    </section>
  )
}
