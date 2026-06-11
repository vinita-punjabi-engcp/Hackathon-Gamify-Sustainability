import { useEffect, useState } from 'react'
import { Users, Leaf, Flame, Zap } from 'lucide-react'

interface SummaryCardsProps {
  totalTeams: number
  totalCarbon: number
  totalWasted: number
  avgEfficiency: number
}

function useAnimatedNumber(target: number, decimals = 3) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    const steps = 40
    const duration = 800
    const increment = target / steps
    let current = 0
    let step = 0
    const timer = setInterval(() => {
      step++
      current = Math.min(target, current + increment)
      setValue(parseFloat(current.toFixed(decimals)))
      if (step >= steps) clearInterval(timer)
    }, duration / steps)
    return () => clearInterval(timer)
  }, [target, decimals])
  return value
}

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string
  sub: string
  borderColor: string
  glowColor: string
  iconBg: string
  delay?: number
}

function StatCard({ icon, label, value, sub, borderColor, glowColor, iconBg, delay = 0 }: StatCardProps) {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay)
    return () => clearTimeout(t)
  }, [delay])

  return (
    <div
      className={`relative rounded-2xl p-5 border bg-eco-surface card-lift overflow-hidden
        transition-all duration-300 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
        hover:${glowColor}`}
      style={{ borderColor, transitionDelay: `${delay}ms` }}
    >
      {/* Subtle corner gradient */}
      <div
        className="absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl opacity-20"
        style={{ background: borderColor }}
      />

      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-eco-muted text-xs font-medium uppercase tracking-wider mb-2">{label}</p>
          <p className="text-2xl font-black text-white font-mono leading-none mb-1">{value}</p>
          <p className="text-eco-muted/70 text-xs mt-2">{sub}</p>
        </div>
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-md"
          style={{ background: iconBg }}
        >
          {icon}
        </div>
      </div>
    </div>
  )
}

export default function SummaryCards({
  totalTeams,
  totalCarbon,
  totalWasted,
  avgEfficiency,
}: SummaryCardsProps) {
  const animCarbon = useAnimatedNumber(totalCarbon, 4)
  const animWasted = useAnimatedNumber(totalWasted, 4)
  const animEff = useAnimatedNumber(avgEfficiency, 1)

  const wastePercent =
    totalCarbon + totalWasted > 0
      ? ((totalWasted / (totalCarbon + totalWasted)) * 100).toFixed(0)
      : '0'

  const effColor =
    avgEfficiency >= 70
      ? '#00ff87'
      : avgEfficiency >= 40
      ? '#f6ad55'
      : '#fc8181'

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-4 gap-3 md:gap-4 animate-fade-in">
      <StatCard
        icon={<Users className="w-5 h-5 text-eco-blue" />}
        label="Teams Tracked"
        value={String(totalTeams)}
        sub="Across all namespaces"
        borderColor="rgba(66,153,225,0.25)"
        glowColor="glow-blue"
        iconBg="rgba(66,153,225,0.15)"
        delay={0}
      />
      <StatCard
        icon={<Leaf className="w-5 h-5 text-eco-green" />}
        label="Total CO₂e Today"
        value={`${animCarbon.toFixed(3)} kg`}
        sub="Active compute emissions"
        borderColor="rgba(0,255,135,0.25)"
        glowColor="glow-green"
        iconBg="rgba(0,255,135,0.12)"
        delay={80}
      />
      <StatCard
        icon={<Flame className="w-5 h-5 text-eco-warn" />}
        label="Wasted Carbon"
        value={`${animWasted.toFixed(3)} kg`}
        sub={`${wastePercent}% of total — over-provisioned`}
        borderColor="rgba(246,173,85,0.25)"
        glowColor="glow-red"
        iconBg="rgba(246,173,85,0.12)"
        delay={160}
      />
      <StatCard
        icon={<Zap className="w-5 h-5" style={{ color: effColor }} />}
        label="Avg Efficiency"
        value={`${animEff.toFixed(1)}%`}
        sub={
          avgEfficiency >= 70
            ? '✅ Fleet is well optimized'
            : avgEfficiency >= 40
            ? '⚠️ Room for improvement'
            : '🚨 Significant over-provisioning'
        }
        borderColor={`${effColor}40`}
        glowColor="glow-green"
        iconBg={`${effColor}18`}
        delay={240}
      />
    </div>
  )
}
