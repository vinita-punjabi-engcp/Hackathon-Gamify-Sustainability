import { useState } from 'react'
import { Search, TrendingUp, Globe, Package } from 'lucide-react'
import type { LeaderboardEntry } from '../App'

interface TeamSearchProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  searchResults: LeaderboardEntry[]
  onSelectResult: (teamName: string) => void
  loading: boolean
}

export default function TeamSearch({
  searchQuery,
  onSearchChange,
  searchResults,
  onSelectResult,
  loading,
}: TeamSearchProps) {
  const [focused, setFocused] = useState(false)

  return (
    <div className="relative">
      <div className="flex items-center gap-3 bg-eco-surface border border-eco-border/40 rounded-xl px-4 py-3 focus-within:border-eco-green/50 focus-within:shadow-lg focus-within:shadow-eco-green/10 transition-all">
        <Search className="w-5 h-5 text-eco-muted shrink-0" />
        <input
          type="text"
          placeholder="🔍 Search for your team... (e.g., 'Core Search', 'CLM Lifecycle')"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 200)}
          className="flex-1 bg-transparent outline-none text-white placeholder-eco-muted/60 text-sm"
        />
      </div>

      {/* Search Results Dropdown */}
      {focused && searchQuery.trim() && (
        <div className="absolute top-full mt-2 w-full bg-eco-bg border border-eco-border/40 rounded-xl shadow-xl z-50 overflow-hidden">
          {loading && (
            <div className="p-4 text-center text-eco-muted text-sm">
              Loading team details...
            </div>
          )}

          {!loading && searchResults.length === 0 && (
            <div className="p-4 text-center text-eco-muted text-sm">
              No teams found matching "{searchQuery}"
            </div>
          )}

          {!loading && searchResults.length > 0 && (
            <div className="max-h-64 overflow-y-auto">
              {searchResults.map((team, index) => (
                <button
                  key={team.team_name}
                  onClick={() => onSelectResult(team.team_name)}
                  className={`w-full px-4 py-3 text-left hover:bg-eco-surface/40 transition-colors border-b border-eco-border/20 last:border-b-0 ${
                    index === 0 ? '' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-eco-green/20 to-eco-blue/20 flex items-center justify-center shrink-0">
                      <span className="text-sm font-bold text-eco-green">#{team.rank_placement}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-bold text-white text-sm truncate">{team.team_name}</h4>
                      <div className="flex items-center gap-2 mt-1">
                        <Package className="w-3 h-3 text-eco-muted shrink-0" />
                        <span className="text-eco-muted text-xs font-mono truncate">{team.namespace}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <div className="text-right">
                        <div className="text-xs font-bold text-eco-green">
                          {team.efficiency_score_pct.toFixed(1)}%
                        </div>
                        <div className="text-xs text-eco-muted">Efficiency</div>
                      </div>
                      <div className="flex items-center gap-1 text-eco-muted">
                        <Globe className="w-3.5 h-3.5" />
                        <span className="text-xs">{getRegionFlag(team.region)}</span>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function getRegionFlag(region: string): string {
  if (region.includes('europe')) return '🇪🇺'
  if (region.includes('us')) return '🇺🇸'
  if (region.includes('asia')) return '🌏'
  return '🌍'
}
