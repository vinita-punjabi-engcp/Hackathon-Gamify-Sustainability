import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import SummaryCards from './components/SummaryCards'
import Leaderboard from './components/Leaderboard'
import TeamModal from './components/TeamModal'
import CarbonCharts from './components/CarbonCharts'
import TeamSearch from './components/TeamSearch'

export interface LeaderboardEntry {
  team_name: string
  namespace: string
  region: string
  efficiency_score_pct: number
  yesterday_carbon_kg: number
  wasted_carbon_kg: number
  waste_ratio: number
  rank_placement: number
}

export interface LeaderboardData {
  metadata: {
    total_teams_logged: number
    sorting_metric: string
    retrieved_at: string
    total_carbon_kg: number
    total_wasted_kg: number
    avg_efficiency_pct: number
  }
  top_performers_green_zone: LeaderboardEntry[]
  bottom_performers_action_required: LeaderboardEntry[]
}

export interface TeamDetail {
  team_name: string
  namespace: string
  region: string
  service_name: string
  cpu_usage_cores: number
  memory_usage_gb: number
  resource_quota_cpu: number
  resource_quota_mem: number
  efficiency_score_pct: number
  yesterday_carbon_kg: number
  wasted_carbon_kg: number
  waste_ratio: number
  ai_mitigation_strategies: string[]
}

export default function App() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardData | null>(null)
  const [selectedTeam, setSelectedTeam] = useState<TeamDetail | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [loadingTeam, setLoadingTeam] = useState(false)
  const [sortBy, setSortBy] = useState<'efficiency' | 'carbon'>('efficiency')
  const [loading, setLoading] = useState(true)
  const [seeding, setSeeding] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
  const [searchQuery, setSearchQuery] = useState('')

  const fetchLeaderboard = useCallback(async () => {
    try {
      const res = await fetch(`/api/leaderboard?sort_by=${sortBy}`)
      if (!res.ok) throw new Error('API error')
      const data: LeaderboardData = await res.json()
      setLeaderboard(data)
      setLastUpdated(new Date())
      setCountdown(30)
    } catch {
      // keep previous data
    } finally {
      setLoading(false)
    }
  }, [sortBy])

  const handleTeamClick = async (teamName: string) => {
    setModalOpen(true)
    setLoadingTeam(true)
    setSelectedTeam(null)
    try {
      const res = await fetch(`/api/team-metrics?team_name=${encodeURIComponent(teamName)}`)
      if (!res.ok) throw new Error('Not found')
      const data: TeamDetail = await res.json()
      setSelectedTeam(data)
    } catch {
      setModalOpen(false)
    } finally {
      setLoadingTeam(false)
    }
  }

  const handleCloseModal = () => {
    setModalOpen(false)
    setSelectedTeam(null)
    setLoadingTeam(false)
  }

  const handleSearchTeam = (query: string) => {
    setSearchQuery(query)
  }

  const handleSelectSearchResult = async (teamName: string) => {
    setSearchQuery('')
    await handleTeamClick(teamName)
  }

  // Get all teams for search
  const allTeams: LeaderboardEntry[] = [
    ...(leaderboard?.top_performers_green_zone ?? []),
    ...(leaderboard?.bottom_performers_action_required ?? []),
  ].filter(
    (team, index, self) =>
      index === self.findIndex((t) => t.team_name === team.team_name),
  )

  // Filter teams based on search query
  const searchResults = searchQuery.trim() 
    ? allTeams.filter(team =>
        team.team_name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : []

  const seedDatabase = async () => {
    setSeeding(true)
    try {
      await fetch('/api/admin/seed-mock-database', { method: 'POST' })
      await fetchLeaderboard()
    } finally {
      setSeeding(false)
    }
  }

  useEffect(() => {
    fetchLeaderboard()
  }, [sortBy, fetchLeaderboard])

  // All calculations come from backend - no UI calculations
  const totalCarbon = leaderboard?.metadata.total_carbon_kg ?? 0
  const totalWasted = leaderboard?.metadata.total_wasted_kg ?? 0
  const avgEfficiency = leaderboard?.metadata.avg_efficiency_pct ?? 0

  return (
    <div className="min-h-screen bg-eco-bg grid-bg">
      {/* Ambient blobs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-eco-green/[0.04] rounded-full blur-3xl" />
        <div className="absolute top-1/3 right-1/4 w-80 h-80 bg-eco-blue/[0.05] rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/2 w-96 h-96 bg-purple-600/[0.03] rounded-full blur-3xl" />
      </div>

      <div className="relative z-10">
        <Header
          sortBy={sortBy}
          onSortChange={setSortBy}
          onSeed={seedDatabase}
          seeding={seeding}
          lastUpdated={lastUpdated}
          totalCarbon={totalCarbon}
          onRefresh={fetchLeaderboard}
        />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
          {loading ? (
            <LoadingSkeleton />
          ) : !leaderboard || leaderboard.metadata.total_teams_logged === 0 ? (
            <EmptyState onSeed={seedDatabase} seeding={seeding} />
          ) : (
            <>
              <TeamSearch 
                searchQuery={searchQuery}
                onSearchChange={handleSearchTeam}
                searchResults={searchResults}
                onSelectResult={handleSelectSearchResult}
                loading={loadingTeam}
              />
              <SummaryCards
                totalTeams={leaderboard.metadata.total_teams_logged}
                totalCarbon={totalCarbon}
                totalWasted={totalWasted}
                avgEfficiency={avgEfficiency}
              />
              <Leaderboard leaderboard={leaderboard} onTeamClick={handleTeamClick} />
              <CarbonCharts allTeams={allTeams} />
            </>
          )}
        </main>
      </div>

      {modalOpen && (
        <TeamModal team={selectedTeam} loading={loadingTeam} onClose={handleCloseModal} />
      )}
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-32 rounded-2xl loading-shimmer" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="h-[480px] rounded-2xl loading-shimmer" />
        <div className="h-[480px] rounded-2xl loading-shimmer" />
      </div>
      <div className="h-72 rounded-2xl loading-shimmer" />
    </div>
  )
}

function EmptyState({ onSeed, seeding }: { onSeed: () => void; seeding: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[65vh] text-center space-y-8 animate-fade-in">
      <div className="relative">
        <div className="text-9xl filter drop-shadow-lg">🌱</div>
        <div className="absolute -top-2 -right-2 w-8 h-8 bg-eco-green/20 rounded-full animate-ping" />
      </div>
      <div>
        <h2 className="text-3xl font-bold text-white mb-3">No Data Tracked Yet</h2>
        <p className="text-eco-muted max-w-md leading-relaxed">
          Your GreenOps database is empty. Seed it with realistic mock data to explore the full
          leaderboard, carbon charts, and team insights.
        </p>
      </div>
      <button
        onClick={onSeed}
        disabled={seeding}
        className="group px-8 py-4 bg-eco-green text-eco-bg font-bold text-lg rounded-2xl
          hover:bg-eco-teal transition-all duration-200 disabled:opacity-50
          shadow-lg hover:shadow-eco-green/25 hover:shadow-xl
          flex items-center gap-3"
      >
        {seeding ? (
          <>
            <span className="animate-spin text-xl">⚡</span> Seeding Database…
          </>
        ) : (
          <>
            <span className="text-xl group-hover:scale-110 transition-transform">⚡</span>
            Load Demo Data
          </>
        )}
      </button>
      <p className="text-eco-muted/60 text-sm">
        Populates 6 realistic engineering teams with Kubernetes namespace metrics
      </p>
    </div>
  )
}
