'use client'

interface DepthResultProps {
  imageUrl: string;
  x: number;
  y: number;
  z: number;
}

export default function DepthResult({ imageUrl, x, y, z }: DepthResultProps) {
  return (
    <div className="rounded-lg overflow-hidden shadow-lg border border-slate-200 bg-white max-w-md my-2 group">
      <div className="relative">
        {/* Main Image */}
        <img
          src={imageUrl}
          alt="Depth Analysis"
          className="w-full h-auto"
          style={{ minHeight: '200px', backgroundColor: '#000' }}
        />
        
        {/* Coordinates Overlay */}
        <div className="absolute bottom-2 left-2 right-2 bg-black/70 backdrop-blur-md rounded-lg p-2 text-white text-xs font-mono border border-white/10">
            <div className="grid grid-cols-3 gap-2 text-center">
                <div className="flex flex-col">
                    <span className="text-slate-400 text-[10px] uppercase tracking-wider">X-Axis</span>
                    <span className="font-bold text-blue-400">{x}mm</span>
                </div>
                <div className="flex flex-col border-l border-white/10">
                    <span className="text-slate-400 text-[10px] uppercase tracking-wider">Y-Axis</span>
                    <span className="font-bold text-green-400">{y}mm</span>
                </div>
                <div className="flex flex-col border-l border-white/10">
                    <span className="text-slate-400 text-[10px] uppercase tracking-wider">Depth (Z)</span>
                    <span className="font-bold text-red-400">{z}mm</span>
                </div>
            </div>
        </div>
      </div>
      
      <div className="bg-slate-50 px-3 py-2 flex justify-between items-center border-t border-slate-100">
        <div className="flex items-center gap-1.5">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5 text-slate-500">
            <path fillRule="evenodd" d="M1 8a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 018.007 3h3.985a2 2 0 011.602.89l.812 1.22A2 2 0 0016.07 6H17a2 2 0 012 2v7.757a.75.75 0 01-.22.53l-2.75 2.75a.75.75 0 01-.53.22H4a2 2 0 01-2-2V8zm1.5 7.5v-7h.93a2 2 0 001.664-.89l.812-1.22A.5.5 0 016.007 6h3.985a.5.5 0 01.401.19l.812 1.22a2 2 0 001.664.89h.93v4.44l-2.121 2.12h-9.12z" clipRule="evenodd" />
            <path d="M10 8a3 3 0 100 6 3 3 0 000-6z" />
          </svg>
          <span className="text-[10px] font-semibold text-slate-600 uppercase tracking-wide">Spatial Measurement</span>
        </div>
      </div>
    </div>
  )
}

