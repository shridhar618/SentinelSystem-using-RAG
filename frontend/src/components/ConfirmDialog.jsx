import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle } from 'lucide-react'

/**
 * Reusable confirmation dialog for consequential actions (restrict a user,
 * delete a policy document, terminate a session...). Replaces native
 * window.confirm so confirmations match the rest of the UI and can explain
 * *what will happen*, not just ask "Are you sure?".
 */
export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  danger = false,
  onConfirm,
  onCancel,
}) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onCancel}
            className="fixed inset-0 bg-black/60 z-[60]"
          />
          <motion.div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="confirm-dialog-title"
            initial={{ opacity: 0, scale: 0.96, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={{ duration: 0.15 }}
            className="fixed z-[70] left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[92%] max-w-sm glass border border-white/10 rounded-2xl p-5 shadow-card"
          >
            <div className="flex items-start gap-3">
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${danger ? 'bg-danger/10 text-danger' : 'bg-accent/10 text-accent'}`}>
                <AlertTriangle size={16} />
              </div>
              <div>
                <h3 id="confirm-dialog-title" className="text-sm font-bold text-white">{title}</h3>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">{message}</p>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={onCancel} className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-300 hover:text-white">
                {cancelLabel}
              </button>
              <button
                onClick={onConfirm}
                className={`px-3 py-2 rounded-lg text-xs font-semibold border ${danger ? 'bg-danger/15 border-danger/30 text-danger hover:bg-danger/25' : 'bg-accent/15 border-accent/30 text-accent hover:bg-accent/25'}`}
              >
                {confirmLabel}
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
