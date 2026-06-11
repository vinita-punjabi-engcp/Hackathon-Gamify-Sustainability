import { useState, useEffect } from 'react'
import { RefreshCw, Zap, Leaf, BarChart2, SortAsc } from 'lucide-react'

interface HeaderProps {
  sortBy: 'efficiency' | 'carbon'
  onSortChange: (v: 'efficiency' | 'carbon') => void
  onSeed: () => void
  seeding: boolean
  lastUpdated: Date
  countdown: number
  totalCarbon: number
  onRefresh: () => void
}

function useLiveCarbonTick(totalCarbon: number) {
  const [display, setDisplay] = useState(totalCarbon)
  useEffect(() => {
    setDisplay(totalCarbon)
    const interval = setInterval(() => {
      // Simulate tiny real-time carbon accumulation (per second tick)
      setDisplay((v) => parseFloat((v + 0.000003).toFixed(6)))
    }, 1000)
    return () => clearInterval(interval)
  }, [totalCarbon])
  return display
}

export default function Header({
  sortBy,
  onSortChange,
  onSeed,
  seeding,
  lastUpdated,
  countdown,
  totalCarbon,
  onRefresh,
}: HeaderProps) {
  const liveCo2 = useLiveCarbonTick(totalCarbon)

  return (
    <header className="sticky top-0 z-30 bg-eco-bg/80 backdrop-blur-xl border-b border-eco-border/30">
      {/* Top accent line */}
      <div className="h-[2px] bg-gradient-to-r from-transparent via-eco-green to-transparent opacity-60" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Logo */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="relative">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-eco-green to-eco-teal flex items-center justify-center shadow-lg shadow-eco-green/20">
                <Leaf className="w-5 h-5 text-eco-bg" strokeWidth={2.5} />
              </div>
              <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-eco-green rounded-full live-dot border-2 border-eco-bg" />
            </div>
            <div>
              <span className="font-black text-lg tracking-tight text-gradient-green">
                EcoNode
              </span>
              <span className="hidden sm:inline text-eco-muted text-xs ml-2 font-mono">
                GreenOps
              </span>
            </div>
          </div>

          {/* Center: Live CO2 counter */}
          {totalCarbon > 0 && (
            <div className="hidden md:flex items-center gap-3 bg-eco-surface border border-eco-border/40 rounded-xl px-4 py-2">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-eco-green live-dot" />
                <span className="text-eco-muted text-xs font-medium uppercase tracking-wider">
                  Live CO₂e
                </span>
              </div>
              <span className="font-mono font-bold text-eco-green text-sm numeric-animate">
                {liveCo2.toFixed(4)} kg
              </span>
              <span className="text-eco-muted/50 text-xs">today</span>
            </div>
          )}

          {/* Right controls */}
          <div className="flex items-center gap-2">
            {/* Sort Toggle */}
            <div className="hidden sm:flex items-center gap-1 bg-eco-surface border border-eco-border/40 rounded-xl p-1">
              <button
                onClick={() => onSortChange('efficiency')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  sortBy === 'efficiency'
                    ? 'bg-eco-green text-eco-bg shadow-sm'
                    : 'text-eco-muted hover:text-white'
                }`}
              >
                <BarChart2 className="w-3.5 h-3.5" />
                Efficiency
              </button>
              <button
                onClick={() => onSortChange('carbon')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  sortBy === 'carbon'
                    ? 'bg-eco-blue text-white shadow-sm'
                    : 'text-eco-muted hover:text-white'
                }`}
              >
                <SortAsc className="w-3.5 h-3.5" />
                Carbon
              </button>
            </div>

            {/* Refresh with countdown */}
            <button
              onClick={onRefresh}
              title={`Next refresh in ${countdown}s`}
              className="relative flex items-center gap-1.5 px-3 py-2 bg-eco-surface border border-eco-border/40
                rounded-xl text-eco-muted hover:text-white hover:border-eco-border transition-all group"
            >
              <RefreshCw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" />
              <span className="text-xs font-mono hidden sm:inline">{countdown}s</span>
            </button>

            {/* Seed button */}
            <button
              onClick={onSeed}
              disabled={seeding}
              className="flex items-center gap-1.5 px-4 py-2 bg-eco-green text-eco-bg font-semibold text-sm
                rounded-xl hover:bg-eco-teal transition-all duration-200 disabled:opacity-60
                shadow-md hover:shadow-eco-green/30 hover:shadow-lg"
            >
              <Zap className={`w-4 h-4 ${seeding ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">{seeding ? 'Seeding…' : 'Seed Data'}</span>
            </button>
          </div>
        </div>

        {/* Sub-bar: last updated */}
        <div className="flex items-center gap-3 pb-2 text-xs text-eco-muted/60 font-mono">
          <span>
            Updated:{' '}
            {lastUpdated.toLocaleTimeString('en-US', {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            })}
          </span>
          <span className="text-eco-border">·</span>
          <span>Kubernetes Namespace GreenOps v2.0</span>
        </div>
      </div>
    </header>
  )
}
