import { X, Loader2 } from 'lucide-react'

const STATUS_LABELS = {
  pending:          '⏳ En cola…',
  downloading:      '⬇️ Descargando audio…',
  separating:       '🧠 Separando pistas con IA…',
  generating_click: '🔔 Generando click track…',
  detecting_chords: '🎸 Detectando acordes…',
  creating_pdf:     '📄 Creando PDF…',
  packaging:        '📦 Empaquetando ZIP…',
}

export default function ProgressCard({ job, onCancel }) {
  const label = STATUS_LABELS[job.status] ?? job.message

  return (
    <div className="glass rounded-2xl p-6 space-y-5 animate-fade-in">
      {/* Song info row */}
      {job.thumbnail && (
        <div className="flex items-center gap-3">
          <img
            src={job.thumbnail}
            alt="thumbnail"
            className="w-14 h-14 rounded-lg object-cover flex-shrink-0"
          />
          <div className="min-w-0">
            <p className="font-semibold text-sm truncate">{job.title ?? 'Procesando…'}</p>
            {job.bpm && (
              <p className="text-white/50 text-xs">{job.bpm} BPM detectados</p>
            )}
          </div>
        </div>
      )}

      {/* Status label */}
      <div className="flex items-center gap-2 text-white/70 text-sm font-medium">
        <Loader2 className="w-4 h-4 animate-spin text-brand-400 flex-shrink-0" />
        {label}
      </div>

      {/* Progress bar */}
      <div>
        <div className="flex justify-between text-xs text-white/40 mb-1.5">
          <span>{job.message}</span>
          <span>{job.progress}%</span>
        </div>
        <div className="w-full h-2.5 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-400 transition-all duration-700"
            style={{ width: `${job.progress}%` }}
          />
        </div>
      </div>

      {/* Steps timeline */}
      <ol className="space-y-1.5">
        {Object.entries(STATUS_LABELS).map(([key, stepLabel]) => {
          const statuses = Object.keys(STATUS_LABELS)
          const currentIdx = statuses.indexOf(job.status)
          const stepIdx = statuses.indexOf(key)
          const done = stepIdx < currentIdx
          const active = key === job.status
          return (
            <li key={key} className={`flex items-center gap-2 text-xs transition-colors ${
              done ? 'text-green-400' : active ? 'text-white' : 'text-white/30'
            }`}>
              <span className="w-4 text-center">
                {done ? '✓' : active ? '›' : '·'}
              </span>
              {stepLabel.replace(/^[^\s]+\s/, '')}
            </li>
          )
        })}
      </ol>

      <button
        onClick={onCancel}
        className="w-full py-2.5 rounded-xl text-sm text-white/50 hover:text-white/80 hover:bg-white/5 transition flex items-center justify-center gap-1.5"
      >
        <X className="w-3.5 h-3.5" />
        Cancelar
      </button>
    </div>
  )
}
