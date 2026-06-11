import { useState, useEffect } from 'react'
import { ChevronRight, TrendingUp, TrendingDown, Globe, Package } from 'lucide-react'
import type { LeaderboardData, LeaderboardEntry } from '../App'

interface LeaderboardProps {
  leaderboard: LeaderboardData
  onTeamClick: (teamName: string) => void
}

interface Badge {
  label: string
  bg: string
  text: string
  border: string
  pulse?: boolean
}

function getBadgeForZone(efficiency: number, isGreenZone: boolean): Badge {
  if (isGreenZone) {
    // Green zone - show positive badges based on efficiency
    if (efficiency >= 90)
      return {
        label: '🌱 CHAMPION',
        bg: 'rgba(0,255,135,0.12)',
        text: '#00ff87',
        border: 'rgba(0,255,135,0.35)',
      }
    if (efficiency >= 70)
      return {
        label: '⚡ OPTIMIZED',
        bg: 'rgba(0,212,160,0.12)',
        text: '#00d4a0',
        border: 'rgba(0,212,160,0.35)',
      }
    // Even lower efficiency in green zone gets MONITOR (still good performance in this sort)
    return {
      label: '👀 SOLID',
      bg: 'rgba(0,255,135,0.12)',
      text: '#00ff87',
      border: 'rgba(0,255,135,0.35)',
    }
  } else {
    // Red zone - show warning badges
    if (efficiency >= 70)
      return {
        label: '⚠️ REVIEW',
        bg: 'rgba(252,129,129,0.12)',
        text: '#fc8181',
        border: 'rgba(252,129,129,0.4)',
      }
    if (efficiency >= 40)
      return {
        label: '⚠️ CAUTION',
        bg: 'rgba(252,129,129,0.12)',
        text: '#fc8181',
        border: 'rgba(252,129,129,0.4)',
      }
    // Low efficiency in red zone = critical
    return {
      label: '🚨 CRITICAL',
      bg: 'rgba(252,129,129,0.12)',
      text: '#fc8181',
      border: 'rgba(252,129,129,0.4)',
      pulse: true,
    }
  }
}

function getBadge(efficiency: number): Badge {
  if (efficiency >= 90)
    return {
      label: '🌱 CHAMPION',
      bg: 'rgba(0,255,135,0.12)',
      text: '#00ff87',
      border: 'rgba(0,255,135,0.35)',
    }
  if (efficiency >= 70)
    return {
      label: '⚡ OPTIMIZED',
      bg: 'rgba(0,212,160,0.12)',
      text: '#00d4a0',
      border: 'rgba(0,212,160,0.35)',
    }
  if (efficiency >= 40)
    return {
      label: '👀 MONITOR',
      bg: 'rgba(246,173,85,0.12)',
      text: '#f6ad55',
      border: 'rgba(246,173,85,0.35)',
    }
  return {
    label: '🚨 ACTION REQ.',
    bg: 'rgba(252,129,129,0.12)',
    text: '#fc8181',
    border: 'rgba(252,129,129,0.4)',
    pulse: true,
  }
}

function getRankDisplay(rank: number) {
  if (rank === 1) return { emoji: '🥇', cls: 'rank-gold' }
  if (rank === 2) return { emoji: '🥈', cls: 'rank-silver' }
  if (rank === 3) return { emoji: '🥉', cls: 'rank-bronze' }
  return { emoji: `#${rank}`, cls: 'rank-default' }
}

function getRegionFlag(region: string): string {
  if (region.includes('europe')) return '🇪🇺'
  if (region.includes('us')) return '🇺🇸'
  if (region.includes('asia')) return '🌏'
  return '🌍'
}

function EnvironmentalImpact({ carbon, isGreenZone }: { carbon: number; isGreenZone: boolean }) {
  // 1 tree absorbs ~20kg CO2 per year
  const treesEquivalent = Math.round((carbon / 20) * 100) / 100
  
  if (isGreenZone) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-2xl">🌳</span>
        <div className="text-xs">
          <p className="text-eco-green font-semibold">
            ✓ Good for Environment
          </p>
          <p className="text-eco-muted text-xs mt-0.5">
            Equivalent to {treesEquivalent} tree{treesEquivalent !== 1 ? 's' : ''} planted
          </p>
        </div>
      </div>
    )
  } else {
    return (
      <div className="flex items-center gap-2">
        <span className="text-2xl">⚠️</span>
        <div className="text-xs">
          <p className="text-eco-red font-semibold">
            Killing {treesEquivalent} tree{treesEquivalent !== 1 ? 's' : ''}/day
          </p>
          <p className="text-eco-muted text-xs mt-0.5">
            High emissions need optimization
          </p>
        </div>
      </div>
    )
  }
}

function EfficiencyBar({ value, delay = 0 }: { value: number; delay?: number }) {
  const [width, setWidth] = useState(0)
  useEffect(() => {
    const t = setTimeout(() => setWidth(value), delay + 100)
    return () => clearTimeout(t)
  }, [value, delay])

  const color =
    value >= 70
      ? 'linear-gradient(90deg, #00d4a0, #00ff87)'
      : value >= 40
      ? 'linear-gradient(90deg, #d97706, #f6ad55)'
      : 'linear-gradient(90deg, #dc2626, #fc8181)'

  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1.5">
        <span className="text-eco-muted">Resource Efficiency</span>
        <span
          className="font-bold font-mono"
          style={{
            color: value >= 70 ? '#00ff87' : value >= 40 ? '#f6ad55' : '#fc8181',
          }}
        >
          {value.toFixed(1)}%
        </span>
      </div>
      <div className="h-2 bg-eco-bg rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{ width: `${width}%`, background: color }}
        />
      </div>
    </div>
  )
}

function TeamCard({
  entry,
  isGreenZone,
  onTeamClick,
  delay = 0,
}: {
  entry: LeaderboardEntry
  isGreenZone: boolean
  onTeamClick: (name: string) => void
  delay?: number
}) {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay)
    return () => clearTimeout(t)
  }, [delay])

  // Badge is now based on ZONE + efficiency context
  const badge = getBadgeForZone(entry.efficiency_score_pct, isGreenZone)
  const rank = getRankDisplay(entry.rank_placement)

  const borderBase = isGreenZone ? 'rgba(0,255,135,0.12)' : 'rgba(252,129,129,0.12)'
  const borderHover = isGreenZone ? 'rgba(0,255,135,0.35)' : 'rgba(252,129,129,0.35)'

  return (
    <div
      onClick={() => onTeamClick(entry.team_name)}
      className={`group relative rounded-xl border bg-eco-surface p-4 cursor-pointer
        transition-all duration-250 hover:scale-[1.015] hover:-translate-y-0.5
        ${badge.pulse ? 'critical-pulse' : ''}
        ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
      style={{
        borderColor: borderBase,
        transitionDelay: `${delay}ms`,
        boxShadow: 'none',
      }}
      onMouseEnter={(e) => {
        ;(e.currentTarget as HTMLDivElement).style.borderColor = borderHover
        ;(e.currentTarget as HTMLDivElement).style.boxShadow = isGreenZone
          ? '0 4px 32px rgba(0,255,135,0.08)'
          : '0 4px 32px rgba(252,129,129,0.08)'
      }}
      onMouseLeave={(e) => {
        ;(e.currentTarget as HTMLDivElement).style.borderColor = borderBase
        ;(e.currentTarget as HTMLDivElement).style.boxShadow = 'none'
      }}
    >
      {/* Rank + Team header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-9 h-9 rounded-xl ${rank.cls} flex items-center justify-center text-sm font-bold shadow-md shrink-0`}
          >
            {rank.emoji}
          </div>
          <div className="min-w-0">
            <h3 className="font-bold text-white text-sm truncate">{entry.team_name}</h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <Package className="w-3 h-3 text-eco-muted shrink-0" />
              <span className="text-eco-muted text-xs font-mono truncate">{entry.namespace}</span>
            </div>
          </div>
        </div>
        <span
          className="text-xs px-2 py-1 rounded-lg border font-semibold shrink-0 ml-2"
          style={{ background: badge.bg, color: badge.text, borderColor: badge.border }}
        >
          {badge.label}
        </span>
      </div>

      {/* Efficiency bar */}
      <div className="mb-3">
        <EfficiencyBar value={entry.efficiency_score_pct} delay={delay} />
      </div>

      {/* Carbon stats */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-eco-bg/60 rounded-lg p-2.5 border border-eco-border/20">
          <div className="text-eco-muted text-xs mb-0.5">CO₂e Emitted</div>
          <div className="font-bold font-mono text-white text-sm">
            {entry.yesterday_carbon_kg.toFixed(3)}
            <span className="text-eco-muted text-xs font-normal ml-1">kg</span>
          </div>
        </div>
        <div className="bg-eco-bg/60 rounded-lg p-2.5 border border-eco-border/20">
          <div className="text-eco-muted text-xs mb-0.5">CO₂e Wasted</div>
          <div
            className="font-bold font-mono text-sm"
            style={{ color: entry.waste_ratio > 0.5 ? '#fc8181' : '#f6ad55' }}
          >
            {entry.wasted_carbon_kg.toFixed(3)}
            <span className="text-eco-muted text-xs font-normal ml-1">kg</span>
          </div>
        </div>
      </div>

      {/* Environmental Impact Message */}
      <div className="mb-3 p-3 rounded-lg bg-eco-bg/40 border border-eco-border/20">
        <EnvironmentalImpact carbon={entry.yesterday_carbon_kg} isGreenZone={isGreenZone} />
      </div>

      {/* Footer: Region + CTA */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs text-eco-muted">
          <Globe className="w-3.5 h-3.5" />
          <span>
            {getRegionFlag(entry.region)} {entry.region}
          </span>
        </div>
        <button className="flex items-center gap-1 text-xs font-medium text-eco-muted group-hover:text-eco-blue transition-colors">
          Inspect
          <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>
    </div>
  )
}

function ZoneHeader({
  title,
  subtitle,
  count,
  isGreen,
}: {
  title: string
  subtitle: string
  count: number
  isGreen: boolean
}) {
  return (
    <div
      className={`flex items-center justify-between mb-4 p-4 rounded-xl border ${
        isGreen
          ? 'bg-eco-green/5 border-eco-green/20'
          : 'bg-eco-red/5 border-eco-red/20'
      }`}
    >
      <div>
        <h2 className={`font-bold text-base ${isGreen ? 'text-eco-green' : 'text-eco-red'}`}>
          {title}
        </h2>
        <p className="text-eco-muted text-xs mt-0.5">{subtitle}</p>
      </div>
      <div className="flex items-center gap-2">
        {isGreen ? (
          <TrendingUp className="w-5 h-5 text-eco-green" />
        ) : (
          <TrendingDown className="w-5 h-5 text-eco-red" />
        )}
        <span
          className={`text-lg font-black font-mono ${isGreen ? 'text-eco-green' : 'text-eco-red'}`}
        >
          {count}
        </span>
      </div>
    </div>
  )
}

export default function Leaderboard({ leaderboard, onTeamClick }: LeaderboardProps) {
  const top = leaderboard.top_performers_green_zone
  const bottom = leaderboard.bottom_performers_action_required

  return (
    <section className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white">
            Team Leaderboard
            <span className="ml-2 text-eco-muted font-normal text-base">
              — {leaderboard.metadata.total_teams_logged} teams ranked
            </span>
          </h2>
          <p className="text-eco-muted text-sm mt-1">
            Sorted by{' '}
            <span className="text-eco-green font-medium">{leaderboard.metadata.sorting_metric}</span>.
            Click any card to inspect detailed metrics.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Green Zone */}
        <div className="animate-slide-in-left">
          <ZoneHeader
            title="🌿 Green Zone"
            subtitle="Top 5 performers — leading by example"
            count={top.length}
            isGreen
          />
          <div className="space-y-3">
            {top.map((entry, i) => (
              <TeamCard
                key={entry.team_name}
                entry={entry}
                isGreenZone
                onTeamClick={onTeamClick}
                delay={i * 80}
              />
            ))}
            {top.length === 0 && (
              <div className="text-center text-eco-muted py-8">No top performers yet</div>
            )}
          </div>
        </div>

        {/* Action Required */}
        <div className="animate-slide-in-right">
          <ZoneHeader
            title="⚠️ Under the Microscope"
            subtitle="Bottom 5 teams — immediate optimization needed"
            count={bottom.length}
            isGreen={false}
          />
          <div className="space-y-3">
            {bottom.map((entry, i) => (
              <TeamCard
                key={entry.team_name}
                entry={entry}
                isGreenZone={false}
                onTeamClick={onTeamClick}
                delay={i * 80}
              />
            ))}
            {bottom.length === 0 && (
              <div className="text-center text-eco-muted py-8">All teams are in the green zone! 🎉</div>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
