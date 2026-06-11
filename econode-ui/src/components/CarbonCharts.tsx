import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  Legend,
  Cell,
} from 'recharts'
import type { LeaderboardEntry } from '../App'

interface CarbonChartsProps {
  allTeams: LeaderboardEntry[]
}

const TEAM_COLORS = ['#00ff87', '#4299e1', '#f6ad55', '#a78bfa', '#fb7185', '#34d399', '#60a5fa']

const tooltipStyle = {
  backgroundColor: '#111827',
  border: '1px solid rgba(30,58,95,0.5)',
  borderRadius: '12px',
  boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: { name: string; value: number; color: string }[]
  label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div
      className="px-4 py-3 text-xs rounded-xl shadow-2xl"
      style={tooltipStyle}
    >
      <p className="text-eco-muted font-medium mb-2 border-b border-eco-border/30 pb-1.5">
        {label}
      </p>
      {payload.map((entry, i) => (
        <p key={i} className="font-mono mt-1" style={{ color: entry.color }}>
          {entry.name}:{' '}
          <span className="font-bold">
            {typeof entry.value === 'number' ? entry.value.toFixed(4) : entry.value}
          </span>
        </p>
      ))}
    </div>
  )
}

function generateTrend(teams: LeaderboardEntry[]) {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  const factors = [1.12, 0.98, 1.05, 1.18, 0.92, 0.78, 1.0]
  return days.map((day, i) => {
    const point: Record<string, number | string> = { day }
    teams.forEach((team) => {
      const base = team.yesterday_carbon_kg + team.wasted_carbon_kg
      point[team.team_name] = parseFloat((base * factors[i] * (0.9 + Math.random() * 0.2)).toFixed(5))
    })
    return point
  })
}

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle: string
  children: React.ReactNode
}) {
  return (
    <div className="bg-eco-surface border border-eco-border/30 rounded-2xl p-5">
      <div className="mb-4">
        <h3 className="font-bold text-white text-sm">{title}</h3>
        <p className="text-eco-muted text-xs mt-0.5">{subtitle}</p>
      </div>
      {children}
    </div>
  )
}

export default function CarbonCharts({ allTeams }: CarbonChartsProps) {
  if (!allTeams.length) return null

  const trendData = generateTrend(allTeams)

  // Efficiency chart data — sorted high to low
  const efficiencyData = [...allTeams]
    .sort((a, b) => b.efficiency_score_pct - a.efficiency_score_pct)
    .map((t) => ({
      name: t.team_name.length > 14 ? t.team_name.slice(0, 12) + '…' : t.team_name,
      fullName: t.team_name,
      efficiency: parseFloat(t.efficiency_score_pct.toFixed(1)),
    }))

  // Carbon breakdown: used + wasted per team
  const carbonData = [...allTeams]
    .sort((a, b) => b.yesterday_carbon_kg + b.wasted_carbon_kg - (a.yesterday_carbon_kg + a.wasted_carbon_kg))
    .map((t) => ({
      name: t.team_name.length > 14 ? t.team_name.slice(0, 12) + '…' : t.team_name,
      fullName: t.team_name,
      'Active CO₂e': parseFloat(t.yesterday_carbon_kg.toFixed(5)),
      'Wasted CO₂e': parseFloat(t.wasted_carbon_kg.toFixed(5)),
    }))

  const axisStyle = { fill: '#64748b', fontSize: 11 }
  const gridStyle = { stroke: 'rgba(30,58,95,0.35)' }

  return (
    <section className="animate-fade-in space-y-5">
      <div>
        <h2 className="text-xl font-bold text-white">Insights & Trends</h2>
        <p className="text-eco-muted text-sm mt-1">
          Visual breakdown of fleet efficiency, carbon emissions, and simulated 7-day trend.
        </p>
      </div>

      {/* Row 1: Efficiency + Carbon Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <ChartCard
          title="⚡ Resource Efficiency Score"
          subtitle="% of allocated CPU actually used — higher is better"
        >
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={efficiencyData} layout="vertical" barSize={14}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} {...gridStyle} />
              <XAxis
                type="number"
                domain={[0, 100]}
                tick={axisStyle}
                tickLine={false}
                axisLine={false}
                unit="%"
              />
              <YAxis
                type="category"
                dataKey="name"
                tick={axisStyle}
                tickLine={false}
                axisLine={false}
                width={90}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="efficiency" radius={[0, 6, 6, 0]} name="Efficiency">
                {efficiencyData.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={
                      entry.efficiency >= 70
                        ? '#00ff87'
                        : entry.efficiency >= 40
                        ? '#f6ad55'
                        : '#fc8181'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="🔥 Carbon: Used vs Wasted"
          subtitle="Active compute emissions vs over-provisioned waste (kg CO₂e)"
        >
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={carbonData} barSize={14}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} {...gridStyle} />
              <XAxis
                dataKey="name"
                tick={axisStyle}
                tickLine={false}
                axisLine={false}
                interval={0}
                angle={-20}
                textAnchor="end"
                height={40}
              />
              <YAxis tick={axisStyle} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: 11, color: '#64748b', paddingTop: 8 }}
              />
              <Bar dataKey="Active CO₂e" fill="#4299e1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Wasted CO₂e" fill="#fc8181" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Row 2: 7-day trend */}
      <ChartCard
        title="📈 7-Day Carbon Trend (Simulated)"
        subtitle="Projected daily CO₂e emissions per team — based on current usage patterns"
      >
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={trendData}>
            <defs>
              {allTeams.map((team, i) => (
                <linearGradient key={team.team_name} id={`grad-${i}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={TEAM_COLORS[i % TEAM_COLORS.length]} stopOpacity={0.25} />
                  <stop offset="95%" stopColor={TEAM_COLORS[i % TEAM_COLORS.length]} stopOpacity={0.0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" {...gridStyle} />
            <XAxis dataKey="day" tick={axisStyle} tickLine={false} axisLine={false} />
            <YAxis tick={axisStyle} tickLine={false} axisLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11, color: '#64748b', paddingTop: 8 }} />
            {allTeams.map((team, i) => (
              <Area
                key={team.team_name}
                type="monotone"
                dataKey={team.team_name}
                stroke={TEAM_COLORS[i % TEAM_COLORS.length]}
                strokeWidth={2}
                fill={`url(#grad-${i})`}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0 }}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Carbon Efficiency Score (CES) explainer */}
      <div className="bg-gradient-to-r from-eco-green/5 to-eco-blue/5 border border-eco-green/15 rounded-2xl p-5">
        <div className="flex items-start gap-4">
          <div className="text-3xl shrink-0">🏆</div>
          <div>
            <h3 className="font-bold text-white text-sm mb-1">
              Carbon Efficiency Score (CES) — The Fair Ranking Formula
            </h3>
            <p className="text-eco-muted text-xs leading-relaxed">
              Raw carbon totals aren't fair — a team running the core signing API will always emit more
              than an internal HR tool. <span className="text-eco-green font-semibold">CES</span> normalizes
              by workload:{' '}
              <span className="font-mono text-eco-teal bg-eco-bg/60 px-1.5 py-0.5 rounded text-xs">
                CES = Total CO₂e ÷ (Active Pods × FTE Count)
              </span>.{' '}
              The <span className="text-eco-green font-semibold">efficiency %</span> shown in each card
              measures used CPU vs allocated quota — the single most actionable metric for FinOps and
              sustainability teams.
            </p>
            <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: '≥ 90%', desc: 'Carbon Champion', color: '#00ff87' },
                { label: '70–89%', desc: 'Well Optimized', color: '#00d4a0' },
                { label: '40–69%', desc: 'Needs Monitor', color: '#f6ad55' },
                { label: '< 40%', desc: 'Action Required', color: '#fc8181' },
              ].map((tier) => (
                <div
                  key={tier.label}
                  className="text-center p-2 rounded-lg border"
                  style={{ borderColor: `${tier.color}30`, background: `${tier.color}08` }}
                >
                  <div className="font-mono font-bold text-xs" style={{ color: tier.color }}>
                    {tier.label}
                  </div>
                  <div className="text-eco-muted text-xs mt-0.5">{tier.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
