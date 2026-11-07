import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { motion, useReducedMotion } from 'framer-motion'
import { AlertCircle, LockKeyhole, ScanFace } from 'lucide-react'

import { useAuth } from '../context/AuthContext'
import api from '../utils/api'
import SiteHeader from '../components/SiteHeader'
import { fadeIn, heroLine, panelIn, useHeroParallax } from '../utils/motion'
import './landing.css'

export default function FaceUnlockPage() {
  const { faceVerified, markFaceVerified } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const reduce = useReducedMotion()
  const heroRef = useRef(null)
  useHeroParallax(heroRef)
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)

  const [cameraReady, setCameraReady] = useState(false)
  const [cameraError, setCameraError] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const targetPath = location.state?.from || '/welcome'

  useEffect(() => {
    if (faceVerified) navigate(targetPath, { replace: true })
  }, [faceVerified, navigate, targetPath])

  useEffect(() => {
    let mounted = true
    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
          audio: false,
        })
        streamRef.current = stream
        if (videoRef.current && mounted) {
          videoRef.current.srcObject = stream
          await videoRef.current.play()
          setCameraReady(true)
        }
      } catch (err) {
        setCameraError(
          err?.name === 'NotAllowedError'
            ? 'Camera permission denied. Please allow camera access and retry.'
            : 'Unable to access camera from this browser/device.'
        )
      }
    }

    startCamera()
    return () => {
      mounted = false
      if (streamRef.current) streamRef.current.getTracks().forEach(track => track.stop())
    }
  }, [])

  const captureFrame = () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas || !video.videoWidth || !video.videoHeight) return null

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    return canvas.toDataURL('image/jpeg', 0.9)
  }

  const verifyFace = async () => {
    setError('')
    const imageBase64 = captureFrame()
    if (!imageBase64) {
      setError('Could not capture your face. Please retry.')
      return
    }
    setLoading(true)
    try {
      await api.post('/auth/face-verify', { image_base64: imageBase64 })
      markFaceVerified()
      navigate(targetPath, { replace: true })
    } catch (err) {
      setError(err?.response?.data?.error || 'Face verification failed.')
    } finally {
      setLoading(false)
    }
  }

  const { logout } = useAuth()
  const lines = [['Verify', 'ink'], ['your', 'ink'], ['face.', 'green']]

  return (
    <div className="sa">
      <SiteHeader
        links={[
          { label: 'Face unlock', to: '/face-unlock', active: true },
          { label: 'Sign out', onClick: () => { logout(); navigate('/login', { replace: true }) }, tone: 'end' },
        ]}
      />
      <section ref={heroRef} className="sa-hero sa-login" aria-labelledby="unlock-title">
        <div className="sa-hero__art" aria-hidden="true"><LockKeyhole strokeWidth={0.75} /></div>
        <div className="sa-hero__inner sa-login__inner">
          <div className="sa-hero__copy">
            <motion.span className="sa-eyebrow" {...fadeIn(0.2, { y: 10, duration: 1.2 })}>
              Identity check
            </motion.span>
            <h1 id="unlock-title" className="sa-hero__title">
              {lines.map(([line, tone], i) => (
                <span className="sa-line" key={line}>
                  <motion.span
                    className={`sa-line__inner ${tone === 'green' ? 'is-green' : ''}`}
                    {...heroLine(i, reduce)}
                  >
                    {line}
                  </motion.span>
                </span>
              ))}
            </h1>
            <motion.p className="sa-hero__lead" {...fadeIn(0.9)}>
              Verify your face to access SecureAI. Face enrollment is completed by an admin when your account is created — if unlock fails because no face is enrolled, contact your admin.
            </motion.p>
          </div>

          <motion.div className="sa-panel sa-form" {...panelIn(0.55)}>
            <span className="sa-eyebrow">Camera</span>
            <div className="sa-camera">
              <video ref={videoRef} autoPlay playsInline muted />
              {!cameraReady && <span className="sa-camera__idle"><ScanFace size={34} strokeWidth={1.4} /></span>}
            </div>
            <canvas ref={canvasRef} className="hidden" />
            {cameraError && <div className="sa-form__error" role="alert"><AlertCircle size={14} /> {cameraError}</div>}
            {error && <div className="sa-form__error" role="alert"><AlertCircle size={14} /> {error}</div>}
            <button type="button" onClick={verifyFace} disabled={!cameraReady || loading} className="sa-btn sa-btn--primary sa-btn--lg sa-btn--block">
              {loading ? 'Verifying…' : 'Unlock with face'} <span className="sa-btn__badge"><ScanFace size={16} /></span>
            </button>
          </motion.div>
        </div>
      </section>
    </div>
  )
}
