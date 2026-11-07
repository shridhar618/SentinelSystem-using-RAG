import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../utils/theme'

export default function ThemeToggle({ className = '', size = 15 }) {
  const [theme, setTheme] = useTheme()
  const next = theme === 'dark' ? 'light' : 'dark'
  const label = `Switch to ${next} theme`
  return (
    <button type="button" className={className} onClick={() => setTheme(next)} aria-label={label} title={label}>
      {theme === 'dark' ? <Sun size={size} /> : <Moon size={size} />}
    </button>
  )
}
