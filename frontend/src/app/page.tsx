'use client'

import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

interface Message {
  id: string
  text: string
  sender: 'user' | 'robot'
  timestamp: Date
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date()
    }

    // Add user message
    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    try {
      // Prepare history from previous messages
      const history = messages.map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'model',
        content: msg.text
      }))

      // Send to backend
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.text,
          history: history
        })
      })

      if (!response.ok) throw new Error('Network response was not ok')
      if (!response.body) throw new Error('Response body is null')

      // Create a placeholder message for the robot's response
      const robotMessageId = (Date.now() + 1).toString()
      const robotMessage: Message = {
        id: robotMessageId,
        text: '',
        sender: 'robot',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, robotMessage])
      setIsTyping(false)

      // Read the stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        
        // Update the robot's message with the new chunk
        setMessages(prev => prev.map(msg => 
          msg.id === robotMessageId 
            ? { ...msg, text: msg.text + chunk }
            : msg
        ))
      }

    } catch (error) {
      console.error('Error sending message:', error)
      setIsTyping(false)
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: '❌ Connection error. Please ensure the backend server is running.',
        sender: 'robot',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col h-screen relative overflow-hidden">
      
      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6 scroll-smooth pb-4 w-3/4 mx-auto mb-32">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className="flex items-end space-x-3 max-w-xs lg:max-w-lg xl:max-w-xl">
              {message.sender === 'robot' && (
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-700 rounded-full flex items-center justify-center flex-shrink-0 shadow-xl ring-2 ring-white/60 ring-offset-1 ring-offset-slate-100/20 animate-pulse">
                  <span className="text-white text-sm drop-shadow-sm">🤖</span>
                </div>
              )}
              <div
                className={`px-5 py-4 rounded-2xl backdrop-blur-xl border transition-all duration-500 hover:scale-[1.02] hover:-translate-y-0.5 group max-w-full overflow-hidden ${
                  message.sender === 'user'
                    ? 'bg-gradient-to-br from-slate-900 via-gray-900 to-black text-white rounded-br-md border-slate-700/50 shadow-2xl shadow-slate-900/25'
                    : 'bg-gradient-to-br from-white/90 via-white/80 to-white/70 text-slate-800 border-white/60 rounded-bl-md shadow-xl shadow-blue-500/10 ring-1 ring-blue-500/20'
                }`}
              >
                <div className={`leading-relaxed font-medium tracking-wide break-words whitespace-pre-wrap ${
                  message.sender === 'user' ? 'text-sm' : 'text-sm'
                }`}>
                  <ReactMarkdown
                    components={{
                      p: ({children}) => <p className="mb-0.5 last:mb-0 leading-relaxed">{children}</p>,
                      code: ({children}) => <code className={`px-1 py-0.5 rounded text-xs font-mono ${
                        message.sender === 'user' ? 'bg-slate-700' : 'bg-slate-200'
                      }`}>{children}</code>,
                      pre: ({children}) => <pre className={`p-1.5 rounded-md overflow-x-auto text-xs font-mono mb-0.5 break-words ${
                        message.sender === 'user' ? 'bg-slate-800' : 'bg-slate-100'
                      }`}>{children}</pre>,
                      ul: ({children}) => <ul className="mb-0.5 last:mb-0 ml-2 list-disc space-y-0">{children}</ul>,
                      ol: ({children}) => <ol className="mb-0.5 last:mb-0 ml-2 list-decimal space-y-0">{children}</ol>,
                      li: ({children}) => <li>{children}</li>,
                      blockquote: ({children}) => <blockquote className={`border-l-2 pl-2 italic my-0.5 ${
                        message.sender === 'user' ? 'border-slate-600' : 'border-slate-300'
                      }`}>{children}</blockquote>,
                      h1: ({children}) => <h1 className="text-lg font-bold mb-0.5 mt-1 first:mt-0">{children}</h1>,
                      h2: ({children}) => <h2 className="text-base font-bold mb-0.5 mt-0.5 first:mt-0">{children}</h2>,
                      h3: ({children}) => <h3 className="text-sm font-bold mb-0 mt-0.5 first:mt-0">{children}</h3>,
                      h4: ({children}) => <h4 className="text-sm font-semibold mb-0 mt-0.5 first:mt-0">{children}</h4>,
                      h5: ({children}) => <h5 className="text-xs font-semibold mb-0 mt-0 first:mt-0">{children}</h5>,
                      h6: ({children}) => <h6 className="text-xs font-semibold mb-0 mt-0 first:mt-0">{children}</h6>,
                      strong: ({children}) => <strong className="font-bold">{children}</strong>,
                      em: ({children}) => <em className="italic">{children}</em>,
                      hr: () => <hr className={`my-1 border-t ${
                        message.sender === 'user' ? 'border-slate-600' : 'border-slate-300'
                      }`} />,
                      a: ({children, href}) => <a href={href} className="underline hover:no-underline" target="_blank" rel="noopener noreferrer">{children}</a>,
                    }}
                  >
                    {message.text}
                  </ReactMarkdown>
                </div>
              </div>
              {message.sender === 'user' && (
                <div className="w-10 h-10 bg-gradient-to-br from-slate-700 via-gray-800 to-black rounded-full flex items-center justify-center flex-shrink-0 shadow-xl ring-2 ring-white/60 ring-offset-1 ring-offset-slate-900/20">
                  <span className="text-white text-sm drop-shadow-sm">👤</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div key="typing-indicator" className="flex justify-start animate-fadeIn">
            <div className="flex items-end space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-700 rounded-full flex items-center justify-center flex-shrink-0 shadow-xl ring-2 ring-white/60 ring-offset-1 ring-offset-slate-100/20 animate-pulse">
                <span className="text-white text-sm drop-shadow-sm">🤖</span>
              </div>
              <div className="bg-gradient-to-br from-white/90 via-white/80 to-white/70 border border-white/60 px-5 py-4 rounded-2xl rounded-bl-md backdrop-blur-xl shadow-xl shadow-blue-500/10 ring-1 ring-blue-500/20">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Floating Input Bar */}
      <div className="fixed bottom-10 left-1/2 transform -translate-x-1/2 w-3/4 px-4 z-50">
        <div className="bg-white/30 backdrop-blur-3xl border border-white/40 shadow-[0_8px_32px_0_rgba(31,38,135,0.1)] rounded-[2rem] p-2.5 ring-1 ring-white/40 transition-all duration-500 hover:bg-white/40 hover:shadow-[0_8px_32px_0_rgba(31,38,135,0.15)] focus-within:ring-blue-400/50 focus-within:ring-2 focus-within:shadow-[0_0_50px_rgba(59,130,246,0.4)] focus-within:bg-white/40 focus-within:hover:shadow-[0_0_50px_rgba(59,130,246,0.4)] group">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Message robot..."
                className="w-full pl-6 pr-12 py-3.5 bg-transparent border-none focus:outline-none outline-none ring-0 text-gray-800 placeholder-gray-500/70 text-[15px] font-medium"
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim()}
              className="p-3.5 bg-black/90 text-white rounded-[1.5rem] hover:bg-black focus:outline-none transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0 active:scale-95"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                <path d="M3.478 2.404a.75.75 0 00-.926.941l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.404z" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
