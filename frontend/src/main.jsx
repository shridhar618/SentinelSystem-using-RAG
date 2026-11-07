import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { MotionConfig } from 'framer-motion'
import App from './App.jsx'
import { initializeTheme } from './utils/theme'
import './index.css'
import './styles/shell.css'

initializeTheme()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      {/* Default for every motion element without its own timing: slow, soft ease-out. */}
      <MotionConfig transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}>
        <App />
      </MotionConfig>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'rgb(var(--bg-800))',
            color: 'rgb(var(--ink))',
            border: '1px solid rgb(var(--line))',
            fontFamily: 'Inter, sans-serif',
            fontSize: '14px',
          },
          success: { iconTheme: { primary: 'rgb(var(--success))', secondary: 'rgb(var(--bg-800))' } },
          error: { iconTheme: { primary: 'rgb(var(--danger))', secondary: 'rgb(var(--bg-800))' } },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
