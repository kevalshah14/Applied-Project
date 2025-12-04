'use client'

import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import CameraStream from '../components/CameraStream'
import DepthResult from '../components/DepthResult'

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

  const [isDarkMode, setIsDarkMode] = useState(false)
  const [mounted, setMounted] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Initialize dark mode after mount to avoid SSR issues
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme')
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches

    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark')
    } else {
      setIsDarkMode(systemPrefersDark)
    }

    setMounted(true)
  }, [])

  // Apply dark mode class when mounted and isDarkMode changes
  useEffect(() => {
    if (mounted) {
      if (isDarkMode) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    }
  }, [isDarkMode, mounted])

  // Save preference when it changes (only after mount)
  useEffect(() => {
    if (mounted) {
      localStorage.setItem('theme', isDarkMode ? 'dark' : 'light')
    }
  }, [isDarkMode, mounted])

  // Listen for system preference changes (only after mount and if no manual preference set)
  useEffect(() => {
    if (!mounted) return

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e: MediaQueryListEvent) => {
      // Only update if user hasn't manually set a preference
      const hasManualPreference = localStorage.getItem('theme') !== null
      if (!hasManualPreference) {
        setIsDarkMode(e.matches)
      }
    }
    mediaQuery.addEventListener('change', handler)

    return () => mediaQuery.removeEventListener('change', handler)
  }, [mounted])

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode)
  }

  // Add isGenerating state
  const [isGenerating, setIsGenerating] = useState(false)

  // ... existing state ...

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
    setIsGenerating(true) // Start generating

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

      // Create a placeholder message for the robot's response, but don't add it yet
      const robotMessageId = (Date.now() + 1).toString()
      const robotMessage: Message = {
        id: robotMessageId,
        text: '',
        sender: 'robot',
        timestamp: new Date()
      }
      
      // setIsGenerating(false) will be called when we start streaming content
      // We'll add the robot message to state when we get the first chunk
      let isFirstChunk = true;

      // Read the stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          setIsGenerating(false) // Stop generating when done
          break
        }
        
        const chunk = decoder.decode(value, { stream: true })
        
        if (isFirstChunk) {
          setIsGenerating(false) // Hide loading indicator
          setMessages(prev => [...prev, { ...robotMessage, text: chunk }])
          isFirstChunk = false
        } else {
          // Update the robot's message with the new chunk
          setMessages(prev => prev.map(msg => 
            msg.id === robotMessageId 
              ? { ...msg, text: msg.text + chunk }
              : msg
          ))
        }
      }

    } catch (error) {
      console.error('Error sending message:', error)
      setIsTyping(false)
      setIsGenerating(false) // Stop generating on error
      
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

  const handleCloseStream = (messageId: string) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, text: msg.text.replace('![Camera Stream](stream)', '[CAMERA_CLOSED]') }
        : msg
    ))
  }

  return (
    <div className="flex flex-col h-screen relative overflow-hidden">
      
      {/* Dark Mode Toggle */}
      {mounted && (
        <button
          onClick={toggleDarkMode}
          className="fixed top-6 right-6 z-50 p-3 rounded-full bg-white/50 dark:bg-slate-800/50 backdrop-blur-md border border-white/60 dark:border-slate-700 shadow-lg hover:scale-105 transition-all duration-300 text-slate-700 dark:text-slate-200"
          aria-label="Toggle Dark Mode"
        >
        {isDarkMode ? (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
            <path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z" />
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
            <path fillRule="evenodd" d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.7-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z" clipRule="evenodd" />
          </svg>
        )}
        </button>
      )}

      {/* Welcome Message */}
      <div 
        className={`fixed left-1/2 transform -translate-x-1/2 transition-all duration-700 ease-out z-40 ${
          messages.length === 0 
            ? 'top-[40%] opacity-100 -translate-y-1/2' 
            : 'top-[35%] opacity-0 -translate-y-1/2 pointer-events-none'
        }`}
      >
        <div className="bg-white/60 dark:bg-slate-900/60 backdrop-blur-xl border border-white/60 dark:border-slate-700 shadow-[0_8px_32px_0_rgba(31,38,135,0.05)] px-10 py-8 rounded-[2rem] ring-1 ring-white/50 dark:ring-slate-700/50">
          <h1 className="text-3xl md:text-4xl font-light text-slate-600 dark:text-slate-300 tracking-tight text-center transition-colors duration-300">
            Hello Human, what can I help you with?
          </h1>
        </div>
      </div>

      {/* Chat Area */}
      <div className={`flex-1 overflow-y-auto px-6 py-4 space-y-6 scroll-smooth pb-4 w-3/4 mx-auto mb-32 transition-all duration-700 ${
        messages.length === 0 ? 'opacity-0 translate-y-10' : 'opacity-100 translate-y-0'
      }`}>
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className="flex items-end space-x-3 max-w-xs lg:max-w-lg xl:max-w-xl">
              {message.sender === 'robot' && (
                <div className="flex flex-col gap-2 w-full">
                  <div className="flex justify-start max-w-xs lg:max-w-lg xl:max-w-xl">
                    <div
                      className="px-5 py-4 rounded-2xl backdrop-blur-xl border transition-all duration-500 hover:scale-[1.02] hover:-translate-y-0.5 group max-w-full overflow-hidden bg-gradient-to-br from-white/90 via-white/80 to-white/70 dark:from-slate-800/90 dark:via-slate-800/80 dark:to-slate-800/70 text-slate-800 dark:text-slate-100 border-white/60 dark:border-slate-700 rounded-bl-md shadow-xl shadow-blue-500/10 ring-1 ring-blue-500/20"
                    >
                      <div className="leading-relaxed font-medium tracking-wide break-words whitespace-pre-wrap text-sm">
                        <ReactMarkdown
                          components={{
                            p: ({children}) => <p className="mb-0.5 last:mb-0 leading-relaxed">{children}</p>,
                            code: ({children}) => <code className="px-1 py-0.5 rounded text-xs font-mono bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200">{children}</code>,
                            pre: ({children}) => <pre className="p-1.5 rounded-md overflow-x-auto text-xs font-mono mb-0.5 break-words bg-slate-100 dark:bg-slate-900 text-slate-800 dark:text-slate-200">{children}</pre>,
                            ul: ({children}) => <ul className="mb-0.5 last:mb-0 ml-2 list-disc space-y-0">{children}</ul>,
                            ol: ({children}) => <ol className="mb-0.5 last:mb-0 ml-2 list-decimal space-y-0">{children}</ol>,
                            li: ({children}) => <li>{children}</li>,
                            blockquote: ({children}) => <blockquote className="border-l-2 pl-2 italic my-0.5 border-slate-300 dark:border-slate-600">{children}</blockquote>,
                            h1: ({children}) => <h1 className="text-lg font-bold mb-0.5 mt-1 first:mt-0">{children}</h1>,
                            h2: ({children}) => <h2 className="text-base font-bold mb-0.5 mt-0.5 first:mt-0">{children}</h2>,
                            h3: ({children}) => <h3 className="text-sm font-bold mb-0 mt-0.5 first:mt-0">{children}</h3>,
                            h4: ({children}) => <h4 className="text-sm font-semibold mb-0 mt-0.5 first:mt-0">{children}</h4>,
                            h5: ({children}) => <h5 className="text-xs font-semibold mb-0 mt-0 first:mt-0">{children}</h5>,
                            h6: ({children}) => <h6 className="text-xs font-semibold mb-0 mt-0 first:mt-0">{children}</h6>,
                            strong: ({children}) => <strong className="font-bold">{children}</strong>,
                            em: ({children}) => <em className="italic">{children}</em>,
                            hr: () => <hr className="my-1 border-t border-slate-300 dark:border-slate-600" />,
                            a: ({children, href}) => <a href={href} className="underline hover:no-underline text-blue-600 dark:text-blue-400" target="_blank" rel="noopener noreferrer">{children}</a>,
                          }}
                        >
                          {message.text.replace('![Camera Stream](stream)', '').replace('[CAMERA_CLOSED]', '').replace(/```json\s*\{[\s\S]*?"type": "depth_result"[\s\S]*?\}\s*```/g, '')}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                  
                  {/* Camera Stream Bubble */}
                  {message.text.includes('![Camera Stream](stream)') && (
                    <div className="mt-2">
                      <CameraStream onClose={() => handleCloseStream(message.id)} />
                    </div>
                  )}

                  {/* Depth Result Bubble */}
                  {message.text.includes('"type": "depth_result"') && (() => {
                    try {
                      const jsonMatch = message.text.match(/```json\s*({[\s\S]*?})\s*```/);
                      if (jsonMatch) {
                        const data = JSON.parse(jsonMatch[1]);
                        if (data.type === 'depth_result') {
                          return (
                            <div className="mt-2">
                              <DepthResult
                                imageUrl={data.image}
                                x={data.x}
                                y={data.y}
                                z={data.z}
                              />
                            </div>
                          );
                        }
                      }
                    } catch (e) {
                      console.error('Failed to parse depth result:', e);
                    }
                    return null;
                  })()}

                  {/* Closed Camera Bubble */}
                  {message.text.includes('[CAMERA_CLOSED]') && (
                     <div className="mt-2">
                        <div className="flex items-center gap-2 p-3 bg-slate-100 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 text-sm italic animate-fadeIn w-fit">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                                <path d="M3.28 2.22a.75.75 0 00-1.06 1.06l14.5 14.5a.75.75 0 101.06-1.06l-1.745-1.745a10.029 10.029 0 003.3-5.975 1 1 0 00-1.3-1.323.75.75 0 00-1.06 1.06 8.5 8.5 0 01-2.535 3.975L3.28 2.22z" />
                                <path d="M9.877 5.355a8.465 8.465 0 014.192 1.767.75.75 0 101.06-1.06A9.965 9.965 0 0010 4a9.962 9.962 0 00-8.096 4.23.75.75 0 101.293.755A8.462 8.462 0 019.877 5.355z" />
                                <path d="M7.354 6.293a.75.75 0 00-1.06 1.06l.565.566A2.5 2.5 0 009.34 10.4l.556.556a.75.75 0 001.06-1.06l-.555-.556a.75.75 0 00-1.06-1.06l-.556-.555a.75.75 0 00-1.06-1.06l-.566-.565z" />
                            </svg>
                            <span>Camera stream ended</span>
                        </div>
                     </div>
                  )}
                </div>
              )}

              {message.sender === 'user' && (
                <div className="flex items-end space-x-3 max-w-xs lg:max-w-lg xl:max-w-xl">
                  <div
                    className={`px-5 py-4 rounded-2xl backdrop-blur-xl border transition-all duration-500 hover:scale-[1.02] hover:-translate-y-0.5 group max-w-full overflow-hidden bg-gradient-to-br from-slate-900 via-gray-900 to-black dark:bg-none dark:bg-slate-800 text-white dark:text-slate-100 rounded-br-md border-slate-700/50 dark:border-slate-700/50 shadow-2xl shadow-slate-900/25 dark:shadow-slate-900/20`}
                  >
                    <div className={`leading-relaxed font-medium tracking-wide break-words whitespace-pre-wrap text-sm`}>
                      <ReactMarkdown
                        components={{
                          p: ({children}) => <p className="mb-0.5 last:mb-0 leading-relaxed">{children}</p>,
                          code: ({children}) => <code className={`px-1 py-0.5 rounded text-xs font-mono bg-slate-700 dark:bg-slate-300 text-slate-200 dark:text-slate-900`}>{children}</code>,
                          pre: ({children}) => <pre className={`p-1.5 rounded-md overflow-x-auto text-xs font-mono mb-0.5 break-words bg-slate-800 dark:bg-slate-400 text-slate-200 dark:text-slate-900`}>{children}</pre>,
                          a: ({children, href}) => <a href={href} className="underline hover:no-underline text-blue-400 dark:text-blue-600" target="_blank" rel="noopener noreferrer">{children}</a>,
                        }}
                      >
                        {message.text}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {isGenerating && (
          <div key="generating-indicator" className="flex justify-start animate-fadeIn">
            <div className="flex justify-start">
              <div className="bg-gradient-to-br from-white/90 via-white/80 to-white/70 dark:from-slate-800/90 dark:via-slate-800/80 dark:to-slate-800/70 border border-white/60 dark:border-slate-700 px-5 py-4 rounded-2xl rounded-bl-md backdrop-blur-xl shadow-xl shadow-blue-500/10 ring-1 ring-blue-500/20">
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
      <div className={`fixed left-1/2 transform -translate-x-1/2 w-3/4 px-4 z-50 transition-all duration-700 cubic-bezier(0.4, 0, 0.2, 1) ${
        messages.length === 0 ? 'bottom-[45%] translate-y-1/2' : 'bottom-10 translate-y-0'
      }`}>
        <div className="bg-white/30 dark:bg-slate-900/30 backdrop-blur-3xl border border-white/40 dark:border-slate-700/40 shadow-[0_8px_32px_0_rgba(31,38,135,0.1)] rounded-[2rem] p-2.5 ring-1 ring-white/40 dark:ring-slate-700/40 transition-all duration-500 hover:bg-white/40 dark:hover:bg-slate-900/40 hover:shadow-[0_8px_32px_0_rgba(31,38,135,0.15)] focus-within:ring-blue-400/50 focus-within:ring-2 focus-within:shadow-[0_0_50px_rgba(59,130,246,0.4)] focus-within:bg-white/40 dark:focus-within:bg-slate-900/40 focus-within:hover:shadow-[0_0_50px_rgba(59,130,246,0.4)] group">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Message robot..."
                className="w-full pl-6 pr-12 py-3.5 bg-transparent border-none focus:outline-none outline-none ring-0 text-gray-800 dark:text-slate-200 placeholder-gray-500/70 dark:placeholder-slate-400/70 text-[15px] font-medium"
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim()}
              className="p-3.5 bg-black/90 dark:bg-white/90 text-white dark:text-slate-900 rounded-[1.5rem] hover:bg-black dark:hover:bg-white focus:outline-none transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0 active:scale-95"
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
