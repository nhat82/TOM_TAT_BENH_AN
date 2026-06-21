import { useEffect, useRef, useState } from 'react'
import type { ChatMessage } from '../types'

interface MsgFeedback {
  val: 'up' | 'down' | null
  showReason: boolean
  reason: string
  sent: boolean
}

function blankFb(): MsgFeedback {
  return { val: null, showReason: false, reason: '', sent: false }
}

interface ChatMessageWithFb extends ChatMessage {
  fb: MsgFeedback
}

export default function ClinicalInsightsPanel({ patientId }: { patientId?: string }) {
  const [messages, setMessages] = useState<ChatMessageWithFb[]>([])
  const [history, setHistory] = useState<Array<{ role: string; content: string }>>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = scrollContainerRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages])

  async function handleSend() {
    const text = input.trim()
    if (!text || isLoading) return

    const userMsg: ChatMessageWithFb = {
      id: Date.now().toString(),
      sender: 'doctor',
      senderName: 'Bác sĩ',
      content: text,
      fb: blankFb(),
    }
    const assistantId = `${Date.now()}_ai`
    const placeholder: ChatMessageWithFb = {
      id: assistantId,
      sender: 'assistant',
      senderName: 'Trợ lý AI',
      content: '',
      fb: blankFb(),
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
    }
  }

  function setMsgFb(id: string, val: 'up' | 'down') {
    setMessages(prev => prev.map(m =>
      m.id === id ? { ...m, fb: { ...m.fb, val, showReason: val === 'down', sent: false } } : m
    ))
  }

  function setMsgReason(id: string, reason: string) {
    setMessages(prev => prev.map(m =>
      m.id === id ? { ...m, fb: { ...m.fb, reason } } : m
    ))
  }

  function sendMsgReason(id: string) {
    setMessages(prev => prev.map(m =>
      m.id === id ? { ...m, fb: { ...m.fb, sent: true, showReason: false } } : m
    ))
  }

  return (
    <div className="bg-white border border-outline-variant rounded-[14px] overflow-hidden shadow-card flex flex-col">
      <div className="flex items-center justify-between px-[18px] py-[14px] border-b border-outline-variant">
        <div className="flex items-center gap-[9px]">
          <span className="w-[26px] h-[26px] rounded-[7px] bg-primary-container text-primary flex items-center justify-center flex-none">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2z"/>
            </svg>
          </span>
          <h3 className="text-[14px] font-bold text-on-surface">Hỏi đáp lâm sàng</h3>
        </div>
        {history.length > 0 && (
          <button
            onClick={() => { setMessages([]); setHistory([]) }}
            className="text-[11px] font-semibold text-on-surface-variant hover:text-error transition-colors"
          >
            Xóa hội thoại
          </button>
        )}
      </div>

      <div
        ref={scrollContainerRef}
        className="min-h-[260px] max-h-[480px] overflow-y-auto px-[18px] py-4 flex flex-col gap-3"
      >
        {messages.length === 0 ? (
          <div className="m-auto text-center text-on-surface-variant py-6 opacity-70">
            <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" className="mx-auto opacity-70">
              <path d="M21 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2z"/>
            </svg>
            <div className="text-[13px] mt-[10px]">Đặt câu hỏi về bệnh nhân này</div>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.sender === 'doctor'
            const isAi = msg.sender === 'assistant'
            return (
              <div key={msg.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                <div className="flex flex-col gap-[6px] max-w-[86%]">
                  <div
                    className="text-[13px] leading-relaxed whitespace-pre-wrap px-[13px] py-[9px]"
                    style={{
                      background: isUser ? '#2f6fed' : '#f1f5fb',
                      color: isUser ? '#fff' : '#16263d',
                      borderRadius: isUser ? '13px 13px 4px 13px' : '13px 13px 13px 4px',
                    }}
                  >
                    {msg.content || (isAi ? (
                      <span className="flex gap-1">
                        {[0, 0.2, 0.4].map((delay, i) => (
                          <span
                            key={i}
                            className="w-[6px] h-[6px] rounded-full bg-[#9aa7ba] inline-block"
                            style={{ animation: `blink 1.2s infinite ${delay}s` }}
                          />
                        ))}
                      </span>
                    ) : null)}
                  </div>

                  {isAi && msg.content && (
                    <div className="flex items-center gap-[6px]">
                      <button
                        onClick={() => setMsgFb(msg.id, 'up')}
                        className="w-[24px] h-[24px] inline-flex items-center justify-center rounded-[7px] border transition-colors"
                        style={{
                          border: `1px solid ${msg.fb.val === 'up' ? '#cfe0fc' : '#e4eaf2'}`,
                          background: msg.fb.val === 'up' ? '#eef4fe' : '#fff',
                          color: msg.fb.val === 'up' ? '#2f6fed' : '#9aa7ba',
                        }}
                      >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M2 20h2.5V10H2v10zm20-9.2c0-.9-.8-1.6-1.7-1.6h-5.3l.8-3.9.1-.4c0-.4-.2-.8-.4-1L14.4 3 8.6 8.9c-.4.3-.6.8-.6 1.3V18c0 .9.7 1.6 1.7 1.6h7.5c.7 0 1.3-.4 1.5-1l2.5-5.9c.1-.2.1-.4.1-.6v-1.3z"/>
                        </svg>
                      </button>
                      <button
                        onClick={() => setMsgFb(msg.id, 'down')}
                        className="w-[24px] h-[24px] inline-flex items-center justify-center rounded-[7px] border transition-colors"
                        style={{
                          border: `1px solid ${msg.fb.val === 'down' ? '#f0c9c4' : '#e4eaf2'}`,
                          background: msg.fb.val === 'down' ? '#fdf0ee' : '#fff',
                          color: msg.fb.val === 'down' ? '#d8584f' : '#9aa7ba',
                        }}
                      >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" style={{ transform: 'scaleY(-1)' }}>
                          <path d="M2 20h2.5V10H2v10zm20-9.2c0-.9-.8-1.6-1.7-1.6h-5.3l.8-3.9.1-.4c0-.4-.2-.8-.4-1L14.4 3 8.6 8.9c-.4.3-.6.8-.6 1.3V18c0 .9.7 1.6 1.7 1.6h7.5c.7 0 1.3-.4 1.5-1l2.5-5.9c.1-.2.1-.4.1-.6v-1.3z"/>
                        </svg>
                      </button>
                      {msg.fb.sent && (
                        <span className="text-[11px] text-[#1d9a6c]">✓ Đã ghi nhận</span>
                      )}
                    </div>
                  )}

                  {isAi && msg.fb.showReason && !msg.fb.sent && (
                    <div className="bg-[#fdf3f1] border border-[#f3d9d4] rounded-[9px] p-2 animate-[fadeUp_.2s_ease]">
                      <textarea
                        value={msg.fb.reason}
                        onChange={(e) => setMsgReason(msg.id, e.target.value)}
                        placeholder="Câu trả lời chưa đúng ở đâu? (không bắt buộc)"
                        className="w-full h-[42px] text-[12px] border border-[#f0d3cd] rounded-lg p-[6px] resize-none outline-none font-[inherit] bg-white text-on-surface"
                      />
                      <button
                        onClick={() => sendMsgReason(msg.id)}
                        className="mt-[6px] px-3 py-[5px] bg-[#d8584f] text-white text-[11px] font-semibold rounded-md border-none cursor-pointer font-[inherit]"
                      >
                        Gửi
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>

      <div className="px-[18px] py-3 border-t border-outline-variant flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.nativeEvent.isComposing && handleSend()}
          placeholder="Hỏi về bệnh nhân…"
          className="flex-1 px-3 py-[10px] border border-outline-variant rounded-[9px] text-[13px] outline-none font-[inherit] text-on-surface bg-white focus:border-primary transition-colors"
        />
        <button
          onClick={handleSend}
          disabled={isLoading}
          className="w-[40px] flex-none flex items-center justify-center bg-primary text-white rounded-[9px] border-none cursor-pointer disabled:opacity-50"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 2 11 13"/>
            <path d="M22 2 15 22l-4-9-9-4 20-7z"/>
          </svg>
        </button>
      </div>

      <style>{`
        @keyframes blink {
          0%, 80%, 100% { opacity: .2; }
          40% { opacity: 1; }
        }
      `}</style>
    </div>
  )
}
