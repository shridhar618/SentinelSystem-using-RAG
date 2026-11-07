import { useEffect, useState } from 'react'

// Paper-and-sage (light) is the default look, matching ShareLock/Revelio.
export const THEME_KEY = 'secureai.theme'
const THEME_EVENT = 'secureai-theme'
const THEMES = ['light', 'dark']

export function getStoredTheme() {
  try {
    const stored = window.localStorage.getItem(THEME_KEY)
    return THEMES.includes(stored) ? stored : 'light'
  } catch {
    return 'light'
  }
}

let themeTimer = 0

export function applyTheme(theme) {
  const next = THEMES.includes(theme) ? theme : 'light'
  const root = document.documentElement
  if (root.dataset.theme && root.dataset.theme !== next
    && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    root.classList.add('theme-anim')
    clearTimeout(themeTimer)
    themeTimer = setTimeout(() => root.classList.remove('theme-anim'), 800)
  }
  root.dataset.theme = next
  root.style.colorScheme = next
  try {
    window.localStorage.setItem(THEME_KEY, next)
  } catch {
    // Theme still applies for this session.
  }
  window.dispatchEvent(new CustomEvent(THEME_EVENT, { detail: next }))
  return next
}

export function initializeTheme() {
  const theme = getStoredTheme()
  document.documentElement.dataset.theme = theme
  document.documentElement.style.colorScheme = theme
}

export function useTheme() {
  const [theme, setTheme] = useState(getStoredTheme)
  useEffect(() => {
    const sync = (e) => setTheme(e.detail)
    window.addEventListener(THEME_EVENT, sync)
    return () => window.removeEventListener(THEME_EVENT, sync)
  }, [])
  return [theme, applyTheme]
}

// Resolved colour for places that cannot use CSS variables (e.g. SVG chart attributes).
export function themeColor(name, alpha = 1) {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(`--${name}`).trim()
  return raw ? `rgb(${raw} / ${alpha})` : undefined
}
