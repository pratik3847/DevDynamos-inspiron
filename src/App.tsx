import { useEffect } from 'react'
import { Routes, Route, useLocation, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
// Dashboard routes
import DashboardLayout from './components/dashboard/DashboardLayout'
import ProtectedRoute from './components/dashboard/ProtectedRoute'
import DashboardHome from './pages/DashboardHome'
import Upload from './pages/Upload'
import ParserEngine from './pages/ParserEngine'
import ValidationEngine from './pages/ValidationEngine'
import FixAssistant from './pages/FixAssistant'
import Dashboard835 from './pages/Dashboard835.tsx'
import RuleBuilder from './pages/RuleBuilder'
import Parser835Dashboard from './pages/Parser835Dashboard.tsx'

// @ts-ignore
import Lenis from 'lenis'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

function App() {
  const location = useLocation()
  
  // Conditionally render main landing app vs dashboard
  const isDashboard = location.pathname.startsWith('/dashboard')

  useEffect(() => {
    if (isDashboard) return; // Don't run lenis inside dashboard

    const lenis = new Lenis({
      duration: 1.2,
      easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      syncTouch: false,
      touchMultiplier: 2,
    })

    lenis.on('scroll', ScrollTrigger.update)

    const ticker = (time: number) => {
      lenis.raf(time * 1000)
    }

    gsap.ticker.add(ticker)
    gsap.ticker.lagSmoothing(0, 0)

    // Ensure lenis styles are attached to html
    document.documentElement.classList.add('lenis')
    if (!document.documentElement.style.height) document.documentElement.style.height = 'auto'

    return () => {
      gsap.ticker.remove(ticker)
      lenis.destroy()
      document.documentElement.classList.remove('lenis')
    }
  }, [isDashboard])

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [location.pathname])

  if (isDashboard) {
    return (
      <Routes>
        <Route path="/dashboard" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
          <Route index element={<DashboardHome />} />
          <Route path="upload" element={<Upload />} />
          <Route path="parser" element={<ParserEngine />} />
          <Route path="validation" element={<ValidationEngine />} />
          <Route path="fix-assistant" element={<FixAssistant />} />
          <Route path="835" element={<Dashboard835 />} />
          <Route path="835-parser" element={<Parser835Dashboard />} />
          <Route path="834" element={<div style={{padding: '32px'}}>834 Dashboard (Module Loading...)</div>} />
          <Route path="rules" element={<RuleBuilder />} />
          <Route path="history" element={<div style={{padding: '40px'}}><h2 style={{color: 'white'}}>Processing History</h2><p style={{color: '#999'}}>Full archive would go here.</p></div>} />
          <Route path="chat" element={<div style={{padding: '40px'}}><h2 style={{color: 'white'}}>Global AI Assistant</h2><p style={{color: '#999'}}>Cross-session query interface would go here.</p></div>} />
          <Route path="settings" element={<div style={{padding: '40px'}}><h2 style={{color: 'white'}}>Settings</h2><p style={{color: '#999'}}>Payer configurations and rulesets would go here.</p></div>} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    )
  }

  return (
    <>
      <video 
        className="bg-video" 
        src="/start_and_end_202604012347.mp4" 
        autoPlay 
        muted 
        loop 
        playsInline
      ></video>
      
      <div className="bg-overlay base-dim"></div>
      <div className="bg-overlay validation-glow"></div>
      <div className="bg-overlay intelligence-glow"></div>
      <div className="bg-overlay fix-glow"></div>

      <Navbar />

      <main id="smooth-content">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
        </Routes>
      </main>
    </>
  )
}

export default App
