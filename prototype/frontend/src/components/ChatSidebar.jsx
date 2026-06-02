import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

function initials(name) {
  return name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
}

function Avatar({ user }) {
  return (
    <div className="chat-avatar">
      {user.photoUrl ? (
        <img className="avatar-img" src={`http://localhost:8000${user.photoUrl}`} alt="" />
      ) : (
        initials(user.displayName)
      )}
    </div>
  )
}

export default function ChatSidebar({ focusThreadId, incomingMessage, onClose }) {
  const { user } = useAuth()
  const [threads, setThreads] = useState([])
  const [activeId, setActiveId] = useState(focusThreadId || null)
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const scrollRef = useRef(null)

  const loadThreads = () => {
    api.getThreads().then((d) => setThreads(d?.threads || []))
  }

  useEffect(loadThreads, [])

  // Respond to an external request to focus a specific thread.
  useEffect(() => {
    if (focusThreadId) setActiveId(focusThreadId)
  }, [focusThreadId])

  // Load messages when a thread is opened.
  useEffect(() => {
    if (!activeId) {
      setMessages([])
      return
    }
    api.getMessages(activeId).then((d) => setMessages(d?.messages || []))
  }, [activeId])

  // Append a live message arriving over the WebSocket.
  useEffect(() => {
    if (!incomingMessage) return
    const { threadId, message } = incomingMessage
    if (threadId === activeId) {
      setMessages((prev) =>
        prev.some((m) => m.id === message.id) ? prev : [...prev, message]
      )
    }
    loadThreads()
  }, [incomingMessage]) // eslint-disable-line react-hooks/exhaustive-deps

  // Keep the message panel scrolled to the latest message.
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [messages])

  const send = async () => {
    const body = draft.trim()
    if (!body || !activeId) return
    setDraft('')
    const res = await api.sendMessage(activeId, body)
    if (!res.error) {
      setMessages((prev) => [...prev, res])
      loadThreads()
    }
  }

  const active = threads.find((t) => t.id === activeId)

  return (
    <div className="chat-sidebar">
      <div className="chat-header">
        {activeId ? (
          <>
            <button className="chat-back" onClick={() => setActiveId(null)}>
              ‹
            </button>
            <span className="chat-title">{active?.user.displayName || 'Chat'}</span>
          </>
        ) : (
          <span className="chat-title">Messages</span>
        )}
        <button className="modal-close" style={{ position: 'static' }} onClick={onClose}>
          ✕
        </button>
      </div>

      {activeId ? (
        <div className="chat-conversation">
          <div className="chat-messages" ref={scrollRef}>
            {messages.length === 0 ? (
              <div className="empty-tags" style={{ padding: 16 }}>
                Say hello 👋
              </div>
            ) : (
              messages.map((m) => (
                <div
                  key={m.id}
                  className={`chat-bubble ${m.fromId === user.id ? 'mine' : 'theirs'}`}
                >
                  {m.body}
                </div>
              ))
            )}
          </div>
          <div className="chat-input-row">
            <input
              className="chat-input"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send()}
              placeholder="Type a message…"
            />
            <button className="chat-send" onClick={send}>
              ➤
            </button>
          </div>
        </div>
      ) : (
        <div className="thread-list">
          {threads.length === 0 ? (
            <div className="empty-tags" style={{ padding: 16 }}>
              No conversations yet. Connect with someone on the map!
            </div>
          ) : (
            threads.map((t) => (
              <button key={t.id} className="thread-item" onClick={() => setActiveId(t.id)}>
                <Avatar user={t.user} />
                <div className="thread-text">
                  <div className="thread-name">{t.user.displayName}</div>
                  <div className="thread-preview">
                    {t.lastMessage || 'No messages yet'}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}
