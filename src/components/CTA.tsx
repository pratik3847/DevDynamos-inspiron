import { Link } from 'react-router-dom'

export default function CTA() {
  return (
    <section className="panel cta-section" id="cta">
      <div className="content-centered">
        <h2 className="cta-title">Upload a file. Fix it today.</h2>
        <div className="btn-group" style={{ marginTop: '32px' }}>
          <Link to="/signup" className="btn btn-primary large">Sign Up</Link>
          <button className="btn btn-secondary large">View Documentation</button>
        </div>
      </div>
    </section>
  )
}
