import { useEffect } from 'react'
import { useReducedMotion } from 'framer-motion'

// Shared motion language for the paper-and-sage hero pages
// (landing, login, welcome, face unlock): slow, soft, blur-into-focus.
export const ease = [0.22, 1, 0.36, 1]
const lineEase = [0.16, 1, 0.3, 1]

// Fade + rise + un-blur. Spread onto a motion element: <motion.p {...fadeIn(0.6)} />
export const fadeIn = (delay = 0, { y = 18, blur = 6, duration = 1.3 } = {}) => ({
  initial: { opacity: 0, y, filter: `blur(${blur}px)` },
  animate: { opacity: 1, y: 0, filter: 'blur(0px)' },
  transition: { duration, delay, ease },
})

// Same, but plays when scrolled into view.
export const revealIn = (delay = 0, { y = 36, blur = 8, duration = 1.2 } = {}) => ({
  initial: { opacity: 0, y, scale: 0.98, filter: `blur(${blur}px)` },
  whileInView: { opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' },
  viewport: { once: true, amount: 0.2 },
  transition: { duration, delay, ease },
})

// One line of a masked hero headline rising into place.
export const heroLine = (i, reduce, base = 0.3) => ({
  initial: reduce ? false : { y: '105%', opacity: 0, rotate: 2, filter: 'blur(10px)' },
  animate: { y: 0, opacity: 1, rotate: 0, filter: 'blur(0px)' },
  transition: { duration: 1.4, delay: base + i * 0.18, ease: lineEase },
})

// The form/camera panel beside a hero.
export const panelIn = (delay = 0.5) => ({
  initial: { opacity: 0, y: 36, scale: 0.97, filter: 'blur(8px)' },
  animate: { opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' },
  transition: { duration: 1.3, delay, ease },
})

// Scroll + pointer parallax for a .sa-hero, eased toward its target each frame
// so the background art glides with a little inertia instead of jumping.
export function useHeroParallax(ref) {
  const reduce = useReducedMotion()
  useEffect(() => {
    const el = ref.current
    if (!el || reduce) return undefined
    const target = { sy: 0, mx: 0, my: 0 }
    const cur = { sy: 0, mx: 0, my: 0 }
    let raf = 0
    const tick = () => {
      let moving = false
      for (const k of ['sy', 'mx', 'my']) {
        cur[k] += (target[k] - cur[k]) * 0.08
        if (Math.abs(target[k] - cur[k]) > 0.001) moving = true
        else cur[k] = target[k]
      }
      el.style.setProperty('--sy', cur.sy.toFixed(2))
      el.style.setProperty('--shrink', Math.min(cur.sy / 560, 1).toFixed(3))
      el.style.setProperty('--mx', cur.mx.toFixed(4))
      el.style.setProperty('--my', cur.my.toFixed(4))
      raf = moving ? requestAnimationFrame(tick) : 0
    }
    const kick = () => { if (!raf) raf = requestAnimationFrame(tick) }
    const onScroll = () => { target.sy = Math.min(window.scrollY, 900); kick() }
    const onMove = (e) => {
      target.mx = e.clientX / window.innerWidth - 0.5
      target.my = e.clientY / window.innerHeight - 0.5
      kick()
    }
    const fine = window.matchMedia('(pointer: fine)').matches
    window.addEventListener('scroll', onScroll, { passive: true })
    if (fine) window.addEventListener('pointermove', onMove, { passive: true })
    onScroll()
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('pointermove', onMove)
    }
  }, [ref, reduce])
}
