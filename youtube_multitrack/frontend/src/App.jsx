import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import Hero from './components/Hero.jsx'
import UrlForm from './components/UrlForm.jsx'
import ProgressCard from './components/ProgressCard.jsx'
import ResultCard from './components/ResultCard.jsx'

const POLL_INTERVAL_MS = 2000

export default function App() {
  const [job, setJob] = useState(null)        // current job object
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const pollRef = useRef(null)

  // Start polling when a job is created
  useEffect(() => {
    if (!job || job.status === 'done' || job.status === 'error') {
      clearInterval(pollRef.current)
      return
    }
    clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const { data } = await axios.get(`/api/jobs/${job.id}`)
        setJob(data)
      } catch {
        clearInterval(pollRef.current)
      }
    }, POLL_INTERVAL_MS)

    return () => clearInterval(pollRef.current)
  }, [job?.id, job?.status])

  async function handleSubmit(url) {
    setError('')
    setLoading(true)
    setJob(null)
    try {
      const { data } = await axios.post('/api/jobs', { url })
      setJob(data)
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        'Error al conectar con el servidor. ¿Está corriendo el backend?'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  function handleReset() {
    clearInterval(pollRef.current)
    setJob(null)
    setError('')
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Background decoration */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-brand-600/20 blur-3xl" />
        <div className="absolute top-1/2 -left-40 w-80 h-80 rounded-full bg-brand-800/20 blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-64 h-64 rounded-full bg-brand-700/10 blur-3xl" />
      </div>

      <main className="flex-1 px-4 pb-16 max-w-2xl mx-auto w-full">
        <Hero />

        <div className="space-y-6 animate-slide-up">
          {!job && (
            <UrlForm onSubmit={handleSubmit} loading={loading} error={error} />
          )}

          {job && job.status !== 'done' && job.status !== 'error' && (
            <ProgressCard job={job} onCancel={handleReset} />
          )}

          {job && job.status === 'done' && (
            <ResultCard job={job} onReset={handleReset} />
          )}

          {job && job.status === 'error' && (
            <div className="glass rounded-2xl p-6 border-red-500/30 text-center space-y-4 animate-fade-in">
              <p className="text-red-400 font-semibold text-lg">❌ Error durante el procesamiento</p>
              <p className="text-white/60 text-sm font-mono break-all">{job.error}</p>
              <button
                onClick={handleReset}
                className="mt-2 px-6 py-2 rounded-xl bg-white/10 hover:bg-white/20 transition text-sm font-medium"
              >
                Intentar de nuevo
              </button>
            </div>
          )}
        </div>
      </main>

      <footer className="text-center pb-8 text-white/30 text-xs">
        YouTube Multitrack · IA generativa de acordes · powered by Demucs + Ollama
      </footer>
    </div>
  )
}
