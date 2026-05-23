import { Download, RotateCcw, Music, FileText, Drumstick } from 'lucide-react'

export default function ResultCard({ job, onReset }) {
  const downloadUrl = `/api/jobs/${job.id}/download`

  return (
    <div className="glass rounded-2xl p-6 space-y-6 animate-slide-up border-brand-500/20">
      {/* Success header */}
      <div className="text-center space-y-2">
        <div className="text-4xl">🎉</div>
        <h2 className="text-xl font-bold">¡Multitrack listo!</h2>
        {job.title && (
          <p className="text-white/60 text-sm font-medium truncate">{job.title}</p>
        )}
      </div>

      {/* Thumbnail + BPM */}
      {job.thumbnail && (
        <div className="flex items-center gap-3 glass rounded-xl p-3">
          <img
            src={job.thumbnail}
            alt="thumbnail"
            className="w-16 h-16 rounded-lg object-cover flex-shrink-0"
          />
          <div>
            <p className="text-white/80 text-sm font-semibold">{job.title}</p>
            {job.bpm && (
              <p className="text-brand-400 text-sm font-mono font-semibold mt-0.5">
                {job.bpm} BPM
              </p>
            )}
          </div>
        </div>
      )}

      {/* What's inside */}
      <div className="space-y-2">
        <p className="text-white/40 text-xs uppercase tracking-widest font-medium">
          Contenido del ZIP
        </p>
        <ul className="space-y-2">
          {[
            { icon: '🥁', label: 'stems/drums.mp3', desc: 'Pista de batería' },
            { icon: '🎸', label: 'stems/bass.mp3',  desc: 'Pista de bajo' },
            { icon: '🎤', label: 'stems/vocals.mp3', desc: 'Pista de voz' },
            { icon: '🎹', label: 'stems/other.mp3',  desc: 'Resto de instrumentos' },
            { icon: '🔔', label: 'click.wav',         desc: 'Click track (metrónomo)' },
            { icon: '🗣️', label: 'guide_voice.wav',   desc: 'Voz guía + click' },
            { icon: '📄', label: 'chords.pdf',         desc: 'Acordes generados por IA' },
          ].map(({ icon, label, desc }) => (
            <li key={label} className="flex items-center gap-2.5 text-sm">
              <span className="text-lg w-7 flex-shrink-0 text-center">{icon}</span>
              <span className="font-mono text-white/70 text-xs flex-1">{label}</span>
              <span className="text-white/40 text-xs hidden sm:block">{desc}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Download button */}
      <a
        href={downloadUrl}
        download
        className="
          flex items-center justify-center gap-2.5
          w-full py-4 rounded-xl font-bold text-base
          bg-gradient-to-r from-brand-500 to-brand-600
          hover:from-brand-400 hover:to-brand-500
          active:scale-[0.98] transition-all
          shadow-xl shadow-brand-700/40
          no-underline text-white
        "
      >
        <Download className="w-5 h-5" />
        Descargar ZIP
      </a>

      <button
        onClick={onReset}
        className="w-full py-2.5 rounded-xl text-sm text-white/40 hover:text-white/70 hover:bg-white/5 transition flex items-center justify-center gap-1.5"
      >
        <RotateCcw className="w-3.5 h-3.5" />
        Procesar otra canción
      </button>
    </div>
  )
}
