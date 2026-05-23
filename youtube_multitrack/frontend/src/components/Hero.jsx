import { Music2, Zap } from 'lucide-react'

export default function Hero() {
  return (
    <header className="pt-12 pb-8 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 mb-6 shadow-lg shadow-brand-700/40">
        <Music2 className="w-8 h-8 text-white" />
      </div>

      <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-3">
        <span className="gradient-text">YouTube Multitrack</span>
      </h1>

      <p className="text-white/60 text-base sm:text-lg max-w-md mx-auto leading-relaxed">
        Pega un enlace de YouTube y obtén{' '}
        <span className="text-white font-medium">multitracks separados</span>,
        un <span className="text-white font-medium">click track</span>, voz guía
        y un <span className="text-white font-medium">PDF con acordes</span> generados por IA.
      </p>

      <div className="flex flex-wrap justify-center gap-2 mt-5">
        {['🥁 Drums', '🎸 Bass', '🎤 Vocals', '🎹 Other', '🔔 Click', '📄 Acordes PDF'].map((tag) => (
          <span
            key={tag}
            className="px-3 py-1 rounded-full text-xs font-medium glass text-white/70"
          >
            {tag}
          </span>
        ))}
      </div>

      <div className="mt-4 inline-flex items-center gap-1.5 text-xs text-brand-400 font-medium">
        <Zap className="w-3.5 h-3.5" />
        Demucs · librosa · OpenAI GPT-4o-mini · ReportLab
      </div>
    </header>
  )
}
