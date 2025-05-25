import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import MCPFrontend from './MCPFrontend'

function App() {
  const [count, setCount] = useState(0)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([]) // stores conversation
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    if (!input.trim()) return
    const userMessage = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('https://remote-research-errs.onrender.com/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input }),
      })
      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }])
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: '❌ Error connecting to backend' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>Edit <code>src/App.jsx</code> and save to test HMR</p>
      </div>
      <p className="read-the-docs">Click on the Vite and React logos to learn more</p>

      {/* ✅ MCP Diagnostic */}
      <hr style={{ margin: '2rem 0' }} />
      <MCPFrontend />

      {/* ✅ MCP Chatbot UI */}
      <hr style={{ margin: '2rem 0' }} />
      <div className="chat-container">
        <h2>💬 MCP Chat Interface</h2>
        <div className="chat-box">
          {messages.map((msg, idx) => (
            <div key={idx} className={msg.role}>
              <strong>{msg.role === 'user' ? 'You' : 'Agent'}:</strong> {msg.content}
            </div>
          ))}
        </div>
        <div className="chat-input">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask something..."
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading || !input.trim()}>
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </>
  )
}

export default App
