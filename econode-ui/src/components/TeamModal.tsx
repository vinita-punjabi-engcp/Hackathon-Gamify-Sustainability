import { useEffect, useState } from 'react'
import { X, Cpu, Database, Globe, Package, Lightbulb, AlertTriangle, CheckCircle } from 'lucide-react'
import type { TeamDetail } from '../App'

interface TeamModalProps {
  team: TeamDetail | null
  loading: boolean
  onClose: () => void
}

const CARBON_INTENSITY: Record<string, number> = {
  westus3: 0.35,
  westeurope: 0.22,
  default: 0.3,
}

const REGION_NAMES: Record<string, string> = {
  westus3: 'West US 3 (Azure)',
  westeurope: 'West Europe (Azure)',
  default: 'Unknown Region',
}

function CircularGauge({
  value,
  max,
  label,
  unit,
  color,
  delay = 0,
}: {
  value: number
  max: number
  label: string
  unit: string
  color: string
  delay?: number
}) {
  const [animated, setAnimated] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), delay + 200)
    return () => clearTimeout(t)
  }, [delay])

  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  const radius = 36
  const circumference = 2 * Math.PI * radius
  const offset = animated ? circumference * (1 - pct / 100) : circumference

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative w-24 h-24">
        <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r={radius}
            strokeWidth="8"
            fill="none"
            stroke="rgba(30,58,95,0.6)"
          />
          <circle
            cx="50"
            cy="50"
            r={radius}
            strokeWidth="8"
            fill="none"
            stroke={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 1.2s ease-out',
              filter: `drop-shadow(0 0 6px ${color}80)`,
            }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-base font-black font-mono" style={{ color }}>
            {pct.toFixed(0)}%
          </span>
        </div>
      </div>
      <div className="text-center">
        <div className="text-xs font-semibold text-white">{label}</div>
        <div className="text-xs font-mono text-eco-muted mt-0.5">
          {value.toFixed(2)}
          {unit} / {max.toFixed(2)}
          {unit}
        </div>
      </div>
    </div>
  )
}

function CarbonBar({
  used,
  wasted,
}: {
  used: number
  wasted: number
}) {
  const total = used + wasted
  const usedPct = total > 0 ? (used / total) * 100 : 0
  const wastedPct = total > 0 ? (wasted / total) * 100 : 0
  const [animated, setAnimated] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 400)
    return () => clearTimeout(t)
  }, [])

  return (
    <div className="space-y-3">
      <div>
        <div className="flex justify-between text-xs mb-1.5">
          <span className="text-eco-blue flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-eco-blue inline-block" />
            Active Compute
          </span>
          <span className="font-mono font-bold text-eco-blue">{used.toFixed(4)} kg</span>
        </div>
        <div className="h-3 bg-eco-bg rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-eco-blue to-blue-400 transition-all duration-1000 ease-out"
            style={{ width: animated ? `${usedPct}%` : '0%' }}
          />
        </div>
      </div>
      <div>
        <div className="flex justify-between text-xs mb-1.5">
          <span className="text-eco-red flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-eco-red inline-block" />
            Wasted (Over-provisioned)
          </span>
          <span className="font-mono font-bold text-eco-red">{wasted.toFixed(4)} kg</span>
        </div>
        <div className="h-3 bg-eco-bg rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-red-700 to-eco-red transition-all duration-1000 ease-out"
            style={{ width: animated ? `${wastedPct}%` : '0%', transitionDelay: '200ms' }}
          />
        </div>
      </div>
      <div className="flex items-center justify-between text-xs text-eco-muted pt-1 border-t border-eco-border/30">
        <span>Annualized waste potential</span>
        <span className="font-mono font-bold text-eco-warn">
          ~{(wasted * 365).toFixed(2)} kg CO₂e/yr
        </span>
      </div>
    </div>
  )
}

function ModalSkeleton() {
  return (
    <div className="p-6 space-y-6 animate-pulse">
      <div className="h-8 w-2/3 loading-shimmer rounded-lg" />
      <div className="h-4 w-1/2 loading-shimmer rounded" />
      <div className="grid grid-cols-2 gap-4">
        <div className="h-32 loading-shimmer rounded-xl" />
        <div className="h-32 loading-shimmer rounded-xl" />
      </div>
      <div className="h-24 loading-shimmer rounded-xl" />
      <div className="h-20 loading-shimmer rounded-xl" />
    </div>
  )
}

export default function TeamModal({ team, loading, onClose }: TeamModalProps) {
  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  const intensity = team
    ? CARBON_INTENSITY[team.region] ?? CARBON_INTENSITY.default
    : 0

  const effColor =
    team && team.efficiency_score_pct >= 70
      ? '#00ff87'
      : team && team.efficiency_score_pct >= 40
      ? '#f6ad55'
      : '#fc8181'

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 animate-fade-in"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="bg-eco-card border border-eco-border/50 rounded-2xl w-full max-w-2xl
            max-h-[90vh] overflow-y-auto shadow-2xl animate-slide-up"
          onClick={(e) => e.stopPropagation()}
        >
          {loading || !team ? (
            <>
              <div className="flex items-center justify-between p-5 border-b border-eco-border/30">
                <div className="h-6 w-48 loading-shimmer rounded" />
                <button onClick={onClose} className="text-eco-muted hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <ModalSkeleton />
            </>
          ) : (
            <>
              {/* Header */}
              <div className="flex items-start justify-between p-5 border-b border-eco-border/30">
                <div>
                  <h2 className="text-xl font-bold text-white">{team.team_name}</h2>
                  <div className="flex flex-wrap items-center gap-2 mt-2">
                    <span className="flex items-center gap-1 text-xs bg-eco-surface border border-eco-border/40 rounded-lg px-2 py-1 text-eco-muted">
                      <Package className="w-3.5 h-3.5" />
                      {team.namespace}
                    </span>
                    <span className="flex items-center gap-1 text-xs bg-eco-surface border border-eco-border/40 rounded-lg px-2 py-1 text-eco-muted">
                      <Globe className="w-3.5 h-3.5" />
                      {REGION_NAMES[team.region] ?? team.region}
                    </span>
                    <span className="text-xs bg-eco-surface border border-eco-border/40 rounded-lg px-2 py-1 text-eco-muted font-mono">
                      {team.service_name}
                    </span>
                    <span
                      className="text-xs px-2 py-1 rounded-lg border font-bold"
                      style={{ color: effColor, borderColor: `${effColor}50`, background: `${effColor}12` }}
                    >
                      {team.efficiency_score_pct.toFixed(1)}% efficient
                    </span>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="text-eco-muted hover:text-white hover:bg-eco-surface rounded-lg p-1.5 transition-colors ml-4 shrink-0"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Body */}
              <div className="p-5 space-y-6">
                {/* Resource Utilization */}
                <section>
                  <h3 className="text-sm font-semibold text-eco-muted uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Cpu className="w-4 h-4" />
                    Resource Utilization
                  </h3>
                  <div className="bg-eco-surface rounded-xl p-5 border border-eco-border/30">
                    <div className="grid grid-cols-2 gap-8 justify-items-center">
                      <CircularGauge
                        value={team.cpu_usage_cores}
                        max={team.resource_quota_cpu}
                        label="CPU Cores"
                        unit=" cores"
                        color={team.cpu_usage_cores / team.resource_quota_cpu >= 0.7 ? '#00ff87' : '#f6ad55'}
                        delay={0}
                      />
                      <CircularGauge
                        value={team.memory_usage_gb}
                        max={team.resource_quota_mem}
                        label="Memory"
                        unit=" GB"
                        color={team.memory_usage_gb / team.resource_quota_mem >= 0.7 ? '#00d4a0' : '#4299e1'}
                        delay={200}
                      />
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                      <div className="bg-eco-bg/50 rounded-lg p-3 border border-eco-border/20">
                        <div className="text-eco-muted mb-1">CPU Slack (wasted)</div>
                        <div className="font-mono font-bold text-eco-warn">
                          {Math.max(0, team.resource_quota_cpu - team.cpu_usage_cores).toFixed(2)} cores
                        </div>
                      </div>
                      <div className="bg-eco-bg/50 rounded-lg p-3 border border-eco-border/20">
                        <div className="text-eco-muted mb-1">Memory Slack (wasted)</div>
                        <div className="font-mono font-bold text-eco-warn">
                          {Math.max(0, team.resource_quota_mem - team.memory_usage_gb).toFixed(2)} GB
                        </div>
                      </div>
                    </div>
                  </div>
                </section>

                {/* Carbon Breakdown */}
                <section>
                  <h3 className="text-sm font-semibold text-eco-muted uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Database className="w-4 h-4" />
                    Carbon Breakdown
                  </h3>
                  <div className="bg-eco-surface rounded-xl p-5 border border-eco-border/30">
                    <CarbonBar used={team.yesterday_carbon_kg} wasted={team.wasted_carbon_kg} />
                    <div className="mt-4 pt-4 border-t border-eco-border/30 grid grid-cols-3 gap-3 text-xs">
                      <div className="text-center">
                        <div className="text-eco-muted mb-1">Grid Intensity</div>
                        <div className="font-mono font-bold text-white">
                          {intensity} kg/kWh
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-eco-muted mb-1">Total Today</div>
                        <div className="font-mono font-bold text-eco-green">
                          {(team.yesterday_carbon_kg + team.wasted_carbon_kg).toFixed(4)} kg
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-eco-muted mb-1">Savings Potential</div>
                        <div className="font-mono font-bold text-eco-warn">
                          {((team.wasted_carbon_kg / Math.max(0.0001, team.yesterday_carbon_kg + team.wasted_carbon_kg)) * 100).toFixed(0)}% reducible
                        </div>
                      </div>
                    </div>
                  </div>
                </section>

                {/* AI Recommendations */}
                <section>
                  <h3 className="text-sm font-semibold text-eco-muted uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Lightbulb className="w-4 h-4" />
                    AI Mitigation Strategies
                  </h3>
                  <div className="space-y-3">
                    {team.ai_mitigation_strategies.map((strategy, i) => {
                      const isCritical = strategy.toLowerCase().includes('critical')
                      return (
                        <div
                          key={i}
                          className={`flex items-start gap-3 p-4 rounded-xl border text-sm leading-relaxed ${
                            isCritical
                              ? 'bg-eco-red/5 border-eco-red/25 text-white'
                              : 'bg-eco-green/5 border-eco-green/20 text-white'
                          }`}
                        >
                          {isCritical ? (
                            <AlertTriangle className="w-5 h-5 text-eco-red shrink-0 mt-0.5" />
                          ) : (
                            <CheckCircle className="w-5 h-5 text-eco-green shrink-0 mt-0.5" />
                          )}
                          <span>{strategy}</span>
                        </div>
                      )
                    })}
                  </div>
                </section>

                {/* Quick stats row */}
                <div className="grid grid-cols-3 gap-3 pt-2 border-t border-eco-border/30">
                  <div className="text-center">
                    <div className="text-xs text-eco-muted mb-1">Region</div>
                    <div className="text-sm font-semibold text-white">{team.region}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-eco-muted mb-1">Namespace</div>
                    <div className="text-sm font-mono text-eco-blue">{team.namespace}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-eco-muted mb-1">Service</div>
                    <div className="text-sm font-mono text-eco-teal">{team.service_name}</div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  )
}
