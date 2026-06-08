import { useRef, useState } from 'react'
import type { ChatMessage } from '../types'

export default function ClinicalInsightsPanel({ patientId }: { patientId?: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [history, setHistory] = useState<Array<{ role: string; content: string }>>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  async function handleSend() {
    const text = input.trim()
    if (!text || isLoading) return

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'doctor',
      senderName: 'Bác sĩ',
      content: text,
    }
    const assistantId = `${Date.now()}_ai`
    const placeholder: ChatMessage = {
      id: assistantId,
      sender: 'assistant',
      senderName: 'Trợ lý AI',
      content: '',
    }

    setMessages((prev) => [...prev, userMsg, placeholder])
    setInput('')
    setIsLoading(true)

    let accumulated = ''

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientId ?? '',
          query: text,
          chat_history: history,
        }),
      })

      if (!res.ok || !res.body) {
        const err = await res.json().catch(() => ({ detail: `Lỗi ${res.status}` }))
        throw new Error(err.detail ?? `Lỗi ${res.status}`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // SSE messages are separated by \n\n
        const parts = buffer.split('\n\n')
        buffer = parts.pop() ?? ''

        for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'token' && event.content) {
              accumulated += event.content
              const snapshot = accumulated
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, content: snapshot } : m))
              )
            } else if (event.type === 'error') {
              throw new Error(event.detail)
            }
          } catch {
            // ignore malformed SSE lines
          }
        }
      }

      setHistory((prev) => [
        ...prev,
        { role: 'user', content: text },
        { role: 'assistant', content: accumulated },
      ])
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Lỗi không xác định'
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, content: `Lỗi: ${msg}` } : m))
      )
    } finally {
      setIsLoading(false)
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    }
  }

  return (
    <div className="bg-surface-container border border-outline rounded-xl flex flex-col shadow-sm overflow-hidden mb-xl" style={{ minHeight: '500px' }}>
      <div className="px-lg py-md border-b border-outline flex items-center justify-between bg-white">
        <div className="flex items-center gap-md">
          <span className="material-symbols-outlined text-primary">auto_awesome</span>
          <h3 className="text-title-sm font-semibold text-on-surface">Hỏi đáp lâm sàng</h3>
        </div>
        {history.length > 0 && (
          <button
            onClick={() => { setMessages([]); setHistory([]) }}
            className="text-[11px] font-bold text-on-surface-variant hover:text-error uppercase tracking-wider transition-colors"
          >
            Xóa hội thoại
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-lg">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-xl space-y-md opacity-50">
            <span className="material-symbols-outlined text-[40px] text-on-surface-variant">forum</span>
            <p className="text-body-sm text-on-surface-variant">Đặt câu hỏi về bệnh nhân này</p>
          </div>
        ) : (
          <div className="space-y-lg">
            {messages.map((msg) =>
              msg.sender === 'doctor' ? (
                <div key={msg.id} className="bg-primary-container/40 p-md rounded-lg border border-primary/10">
                  <p className="text-[13px] font-medium mb-xs">{msg.senderName}</p>
                  <p className="text-[13px] text-on-surface-variant">{msg.content}</p>
                </div>
              ) : (
                <div key={msg.id} className="bg-white p-md rounded-lg border border-outline-variant shadow-sm">
                  <p className="text-[13px] font-bold text-primary mb-xs">{msg.senderName}</p>
                  {msg.content ? (
                    <p className="text-[13px] text-on-surface whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <p className="text-[13px] text-on-surface-variant animate-pulse">Đang phân tích…</p>
                  )}
                </div>
              )
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="p-md bg-white border-t border-outline">
        <div className="flex items-center gap-sm bg-surface-container px-md py-2 rounded-full border border-transparent focus-within:border-primary/20 transition-all">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Hỏi về bệnh nhân..."
            className="flex-1 bg-transparent border-none focus:ring-0 text-body-sm py-1 placeholder:text-on-surface-variant/50 outline-none"
          />
          <button
            onClick={handleSend}
            disabled={isLoading}
            className="text-primary hover:scale-110 transition-transform disabled:opacity-40"
          >
            <span className="material-symbols-outlined">send</span>
          </button>
        </div>
      </div>
    </div>
  )
}
