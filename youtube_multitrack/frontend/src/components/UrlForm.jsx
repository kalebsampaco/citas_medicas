import { useState } from 'react'
import { Link, Loader2 } from 'lucide-react'

export default function UrlForm({ onSubmit, loading, error }) {
  const [url, setUrl] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (url.trim()) onSubmit(url.trim())
  }

  const isYouTube = url.includes('youtube.com') || url.includes('youtu.be')

  return (
    <div className="glass rounded-2xl p-6 space-y-4 animate-fade-in">
      <h2 className="font-semibold text-white/80 text-sm uppercase tracking-widest">
        URL de YouTube
      </h2>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative">
          <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30 pointer-events-none" />
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=…"
            required
            disabled={loading}
            className={`
              w-full pl-10 pr-4 py-3.5 rounded-xl text-sm
              bg-white/5 border transition-all outline-none
              placeholder:text-white/25 text-white
              ${url && !isYouTube
                ? 'border-red-500/60 focus:border-red-400'
                : 'border-white/10 focus:border-brand-500'
              }
              disabled:opacity-50
            `}
          />
        </div>

        {url && !isYouTube && (
          <p className="text-red-400 text-xs">Ingresa un enlace válido de YouTube.</p>
        )}

        {error && (
          <p className="text-red-400 text-xs bg-red-500/10 rounded-lg px-3 py-2">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading || !url || !isYouTube}
          className={`
            w-full py-3.5 rounded-xl font-semibold text-sm transition-all flex items-center justify-center gap-2
            bg-gradient-to-r from-brand-500 to-brand-600
            hover:from-brand-400 hover:to-brand-500
            active:scale-[0.98]
            disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100
            shadow-lg shadow-brand-700/30
          `}
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Enviando…
            </>
          ) : (
            '🎵 Generar Multitrack'
          )}
        </button>
      </form>

      <p className="text-white/30 text-xs text-center">
        El proceso puede tardar 3–8 minutos según la duración de la canción.
      </p>
    </div>
  )
}
