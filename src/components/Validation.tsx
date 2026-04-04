export default function Validation() {
  return (
    <section className="panel split-right" id="validation">
      <div className="content-block right-aligned">
        <h2 className="section-title">Exact Error.<br/>Exact Location.<br/>Clear Explanation.</h2>
        
        <div className="error-toast enhanced">
          <div className="toast-header">
            <div className="icon-error">&#10005;</div>
            <span className="err-loc">Loop 2300 &rarr; NM109 &rarr; Invalid NPI</span>
          </div>
          <div className="toast-body">
            <span className="err-detail">This NPI fails checksum validation and will be rejected by all payers.</span>
          </div>
          <div className="toast-footer text-red">
             Severity: Critical Rejection
          </div>
        </div>
      </div>
    </section>
  )
}
