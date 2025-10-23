import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'

type Role = 'user' | 'assistant'

type Message = {
  id: string
  role: Role
  content: string
  pending?: boolean
  sources?: string[]
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000'

const INITIAL_ASSISTANT_MESSAGE =
  "Hi! I'm here to answer questions about the AWS Well-Architected Framework. Ask about pillars, best practices, or improvement plans to get started."

const generateId = () => crypto.randomUUID()

const formatSources = (sources: string[] | undefined) => {
  if (!sources || sources.length === 0) {
    return null
  }
  return (
    <ul className="mt-2 space-y-1 text-sm text-slate-500">
      {sources.map((source) => (
        <li key={source}>
          <span className="font-semibold text-slate-600">Source:</span>{' '}
          <a
            href={source}
            target="_blank"
            rel="noreferrer"
            className="text-wafr-blue hover:underline"
          >
            {source}
          </a>
        </li>
      ))}
    </ul>
  )
}

const ChatBubble = ({ message }: { message: Message }) => {
  const isUser = message.role === 'user'
  const bubbleClasses = useMemo(
    () =>
      [
        'max-w-[85%] rounded-2xl px-5 py-3 text-sm shadow-sm transition',
        isUser
          ? 'ml-auto bg-wafr-blue text-white'
          : 'bg-white text-slate-800 ring-1 ring-slate-200',
      ].join(' '),
    [isUser],
  )

  return (
    <div className="flex w-full flex-col gap-2">
      <div className={bubbleClasses}>
        <p className="whitespace-pre-line leading-relaxed">{message.content}</p>
        {message.pending && (
          <p className="mt-2 text-xs font-medium uppercase tracking-wide text-slate-400">
            Drafting response…
          </p>
        )}
        {formatSources(message.sources)}
      </div>
    </div>
  )
}

const PillarCard = ({
  title,
  description,
  accent,
}: {
  title: string
  description: string
  accent: string
}) => (
  <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
    <div className="flex items-center gap-3">
      <span className={`h-8 w-1.5 rounded-full ${accent}`}></span>
      <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
    </div>
    <p className="mt-2 text-sm text-slate-500">{description}</p>
  </div>
)

function App() {
  const [messages, setMessages] = useState<Message[]>([
    { id: generateId(), role: 'assistant', content: INITIAL_ASSISTANT_MESSAGE },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = input.trim()
    if (!trimmed) return

    setError(null)
    setIsLoading(true)

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: trimmed,
    }

    const pendingAssistant: Message = {
      id: generateId(),
      role: 'assistant',
      content: 'Thinking…',
      pending: true,
    }

    setMessages((prev) => [...prev, userMessage, pendingAssistant])
    setInput('')

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmed }),
      })

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
      }

      const data = (await response.json()) as {
        answer: string
        sources: string[]
      }

      setMessages((prev) =>
        prev.map((message) =>
          message.id === pendingAssistant.id
            ? {
                ...message,
                content: data.answer,
                pending: false,
                sources: data.sources,
              }
            : message,
        ),
      )
    } catch (err) {
      const fallback =
        err instanceof Error ? err.message : 'Unexpected error occurred.'
      setError(fallback)
      setMessages((prev) =>
        prev.map((message) =>
          message.id === pendingAssistant.id
            ? {
                ...message,
                content:
                  "I couldn't reach the backend service just yet. Please confirm the API is running on port 8000 and try again.",
                pending: false,
              }
            : message,
        ),
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-wafr-sand via-white to-wafr-sand">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-6 py-6 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-wafr-green">
              AWS Well-Architected
            </p>
            <h1 className="mt-2 text-2xl font-bold text-slate-900 md:text-3xl">
              WAFR Chatbot Studio
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Explore the six pillars, surface best practices, and prepare answers
              for architectural reviews on demand.
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs text-slate-500 shadow-sm">
            <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
            Prototype ready • Retrieval pipeline forthcoming
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-10 md:flex-row">
        <section className="flex h-full flex-1 flex-col rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 pb-4">
            <h2 className="text-lg font-semibold text-slate-800">Conversation</h2>
            <button
              type="button"
              className="text-xs font-semibold uppercase tracking-wide text-wafr-blue hover:text-wafr-green"
              onClick={() =>
                setMessages([
                  { id: generateId(), role: 'assistant', content: INITIAL_ASSISTANT_MESSAGE },
                ])
              }
            >
              Reset Thread
            </button>
          </div>

          <div className="mt-4 flex-1 space-y-4 overflow-y-auto pr-3">
            {messages.map((message) => (
              <ChatBubble key={message.id} message={message} />
            ))}
          </div>

          <form
            onSubmit={handleSubmit}
            className="mt-6 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 shadow-inner"
          >
            <label htmlFor="chat-input" className="text-xs font-semibold uppercase tracking-[0.25em] text-slate-400">
              Ask anything
            </label>
            <textarea
              id="chat-input"
              className="min-h-[100px] w-full resize-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 shadow-sm focus:border-wafr-blue focus:outline-none focus:ring-2 focus:ring-wafr-blue/30"
              placeholder="e.g. Summarize the Operational Excellence pillar and list two key design principles."
              value={input}
              onChange={(event) => setInput(event.target.value)}
              disabled={isLoading}
              required
            />
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs text-slate-500">
                Prototype uses a placeholder model response — backend integration coming next.
              </p>
              <button
                type="submit"
                disabled={isLoading}
                className="inline-flex items-center justify-center rounded-full bg-wafr-blue px-5 py-2 text-sm font-semibold text-white shadow hover:bg-wafr-green focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-wafr-blue disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isLoading ? 'Sending…' : 'Send'}
              </button>
            </div>
            {error && <p className="text-xs font-semibold text-rose-500">{error}</p>}
          </form>
        </section>

        <aside className="flex w-full flex-col gap-4 md:w-80">
          <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
            <h2 className="text-base font-semibold text-slate-800">
              AWS Well-Architected Pillars
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              Use these quick prompts to explore the guidance available in the framework.
            </p>
            <div className="mt-4 grid gap-3">
              <PillarCard
                title="Operational Excellence"
                description="Streamline operations with automation, observability, and continual improvement."
                accent="bg-amber-400"
              />
              <PillarCard
                title="Security"
                description="Protect data, systems, and assets through layered controls and automation."
                accent="bg-rose-400"
              />
              <PillarCard
                title="Reliability"
                description="Architect workloads to recover quickly and handle demand gracefully."
                accent="bg-sky-400"
              />
              <PillarCard
                title="Performance Efficiency"
                description="Use computing resources efficiently and keep adapting to changing requirements."
                accent="bg-emerald-400"
              />
              <PillarCard
                title="Cost Optimization"
                description="Eliminate un-needed cost, align spend with business goals, and measure returns."
                accent="bg-indigo-400"
              />
              <PillarCard
                title="Sustainability"
                description="Minimize environmental impact from your workloads across their lifecycle."
                accent="bg-lime-400"
              />
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-gradient-to-br from-wafr-blue to-wafr-green p-6 text-white shadow">
            <h3 className="text-base font-semibold">Next Steps</h3>
            <ul className="mt-3 space-y-2 text-sm">
              <li>• Hook into Elasticsearch retrieval for contextual answers.</li>
              <li>• Deploy FastAPI on Lambda with Mangum.</li>
              <li>• Ship this UI via S3 static hosting + CloudFront.</li>
            </ul>
          </div>
        </aside>
      </main>
    </div>
  )
}

export default App
