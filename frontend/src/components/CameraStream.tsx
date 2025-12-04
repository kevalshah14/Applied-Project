'use client'

import { useEffect, useRef, useState } from 'react'

export default function CameraStream({ onClose }: { onClose?: () => void }) {
  const [error, setError] = useState<string | null>(null)
  const imgRef = useRef<HTMLImageElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // Connect to WebSocket
    const wsUrl = 'ws://localhost:8000/ws/camera'
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('Connected to camera stream')
      setError(null)
    }

    ws.onmessage = (event) => {
      if (imgRef.current) {
        // Revoke old URL before creating new one to prevent memory leak
        const oldUrl = imgRef.current.src
        
        const blob = new Blob([event.data], { type: 'image/jpeg' })
        const url = URL.createObjectURL(blob)
        imgRef.current.src = url

        if (oldUrl && oldUrl.startsWith('blob:')) {
          URL.revokeObjectURL(oldUrl)
        }
      }
    }

    ws.onerror = (e) => {
      console.error('WebSocket error:', e)
      setError('Failed to connect to camera stream')
    }

    ws.onclose = () => {
      console.log('Camera stream closed')
    }

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
      if (imgRef.current && imgRef.current.src) {
        URL.revokeObjectURL(imgRef.current.src)
      }
    }
  }, [])

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-600 rounded-lg border border-red-200">
        {error}
      </div>
    )
  }

    return (
    <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-slate-800 bg-black max-w-md my-2 group ring-1 ring-slate-700/50">
      {onClose && (
        <div className="absolute top-0 left-0 right-0 p-3 flex justify-between items-start bg-gradient-to-b from-black/60 to-transparent z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <div className="px-2 py-1 rounded-md bg-black/40 backdrop-blur-md border border-white/10 text-[10px] font-mono text-white/80 uppercase tracking-wider">
                Robot Vision
            </div>
            <button 
              onClick={onClose}
              className="p-1.5 bg-white/10 hover:bg-red-500/80 text-white rounded-full backdrop-blur-md transition-all duration-200 hover:scale-110 shadow-lg"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
              </svg>
            </button>
        </div>
      )}
      
      <div className="relative">
          <img
            ref={imgRef}
            alt="Camera Stream"
            className="w-full h-auto object-cover"
            style={{ minHeight: '240px', backgroundColor: '#1a1a1a' }}
          />
          
          {/* Scanning line effect */}
          <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-blue-500/5 to-transparent animate-scan"></div>
      </div>

      <div className="bg-slate-900/90 backdrop-blur-sm text-white text-xs px-4 py-2.5 flex justify-between items-center border-t border-slate-800">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
          </span>
          <span className="font-semibold tracking-wide text-red-500 text-[10px] uppercase">Live Feed</span>
        </div>
        <div className="flex items-center gap-2 opacity-60">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
            <span className="text-[10px] font-mono">1080p • 30fps</span>
        </div>
      </div>
    </div>
  )
}

