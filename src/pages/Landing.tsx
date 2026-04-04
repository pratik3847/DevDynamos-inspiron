import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'
import Hero from '../components/Hero'
import Problem from '../components/Problem'
import SolutionFlow from '../components/SolutionFlow'
import Structure from '../components/Structure'
import Validation from '../components/Validation'
import FixSuggestions from '../components/FixSuggestions'
import Agents from '../components/Agents'
import UseCases from '../components/UseCases'
import Output from '../components/Output'
import CTA from '../components/CTA'

gsap.registerPlugin(ScrollTrigger)

export default function Landing() {
  const comp = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const fadeUpConfig = { y: 0, opacity: 1, duration: 1, ease: 'power3.out' };

      // 1. Initial Hero Load Animation (fade in text elements)
      gsap.to('.hero .content-centered > *:not(.bg-overlay)', { 
        y: 0, 
        opacity: 1, 
        duration: 1, 
        ease: 'power3.out',
        stagger: 0.2,
        delay: 0.2 
      });

      // Navbar background fade in on scroll
      ScrollTrigger.create({
        trigger: '#hero',
        start: 'top -50px',
        toggleClass: {targets: '#navbar', className: 'scrolled'}
      });

      // 2. Hero exit fade
      gsap.to('.hero .content-centered', {
        scrollTrigger: {
          trigger: '#hero',
          start: 'top top',
          end: 'bottom top',
          scrub: true
        },
        opacity: 0,
        y: -50,
        scale: 0.95
      });

      // Helper function to create standard fade up triggers for section content blocks
      const sections = ['#problem', '#solution', '#structure', '#validation', '#fix-suggestions', '#agents', '#use-cases', '#output', '#cta'];
      
      sections.forEach(sec => {
        ScrollTrigger.create({
          trigger: sec,
          start: 'top 70%',
          animation: gsap.to(`${sec} .content-block > *:not(.bg-overlay)`, { ...fadeUpConfig, stagger: 0.15 }),
          toggleActions: 'play reverse play reverse'
        });
        // For sections with content-centered (like cta)
        if (document.querySelector(`${sec} .content-centered`)) {
           ScrollTrigger.create({
              trigger: sec,
              start: 'top 70%',
              animation: gsap.to(`${sec} .content-centered > *:not(.bg-overlay)`, { ...fadeUpConfig, stagger: 0.15 }),
              toggleActions: 'play reverse play reverse'
           });
        }
      });

      // --- Inter-Section Transitions ---

      // Structure Card & Text
      const structureTl = gsap.timeline({
        scrollTrigger: {
          trigger: '#structure',
          start: 'top center',
          end: 'bottom center',
          scrub: 1
        }
      });

      structureTl.to('.structure-card', {
        autoAlpha: 1,
        scale: 1,
        y: '-50%',
        duration: 1,
        ease: 'back.out(1.7)'
      })
      .to('.base-dim', { opacity: 1, duration: 0.5 }, '<');

      // Validation - Red highlight
      const validationTl = gsap.timeline({
        scrollTrigger: {
          trigger: '#validation',
          start: 'top 60%',
          end: 'bottom 40%',
          scrub: 1
        }
      });
      validationTl.to('.validation-glow', { opacity: 1, duration: 0.5 });
      
      // Fade out structure card
      gsap.to('.structure-card', {
          scrollTrigger: {
              trigger: '#validation',
              start: 'top bottom',
              end: 'top center',
              scrub: 1
          },
          autoAlpha: 0,
          scale: 0.9,
          y: '-80%'
      });

      // Fix Suggestions
      const fixTl = gsap.timeline({
        scrollTrigger: {
          trigger: '#fix-suggestions',
          start: 'top center',
          end: 'bottom center',
          scrub: 1
        }
      });
      fixTl.to('.validation-glow', { opacity: 0, duration: 0.5 })
           .to('.fix-glow', { opacity: 1, background: 'radial-gradient(circle at center, rgba(52, 199, 89, 0.15) 0%, transparent 60%)', mixBlendMode: 'screen', duration: 0.5 }, '<');

      // Intelligence (Multi-Agent AI)
      const intelligenceTl = gsap.timeline({
        scrollTrigger: {
          trigger: '#agents',
          start: 'top center',
          end: 'bottom center',
          scrub: 1
        }
      });
      
      intelligenceTl.to('.fix-glow', { opacity: 0, duration: 0.5 })
                    .to('.intelligence-glow', { opacity: 1, duration: 0.5 }, '<');

      // Clear glow at the end
      gsap.to('.intelligence-glow', {
        scrollTrigger: {
          trigger: '#use-cases', // clear a bit earlier as user scrolls to end
          start: 'top bottom',
          end: 'bottom bottom',
          scrub: true
        },
        opacity: 0,
        duration: 0.5
      });
    }, comp)

    return () => ctx.revert()
  }, [])

  return (
    <div ref={comp}>
      <Hero />
      <Problem />
      <SolutionFlow />
      <Structure />
      <Validation />
      <FixSuggestions />
      <Agents />
      <UseCases />
      <Output />
      <CTA />
    </div>
  )
}
