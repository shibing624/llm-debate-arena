import { useState, useEffect } from 'react'
import { Trophy, Home, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { getApiUrl } from '../config'

interface Competitor {
  model_id: string
  display_name: string
  provider: string
  elo_rating: number
  matches_played: number
  wins: number
  losses: number
  draws: number
  win_rate: number
}

// 🔧 新增：模型统计数据（脱敏）
interface RecentMatch {
  result: 'W' | 'L' | 'D'
  opponent: string  // 对手模型ID
}

interface ModelStats {
  recent_form: RecentMatch[]  // 最近10场战绩含对手
  win_streak: number  // 当前连胜
  loss_streak: number  // 当前连败
  elo_trend: number  // ELO趋势（最近变化）
  peak_elo: number  // 历史最高ELO
  total_matches: number
}

export default function Leaderboard() {
  const navigate = useNavigate()
  const [competitors, setCompetitors] = useState<Competitor[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedModel, setExpandedModel] = useState<string | null>(null)
  const [modelStats, setModelStats] = useState<Record<string, ModelStats>>({})

  useEffect(() => {
    fetchLeaderboard()
  }, [])

  const fetchLeaderboard = async () => {
    try {
      const apiUrl = getApiUrl('/api/tournament/leaderboard')
      const response = await fetch(apiUrl)
      const data = await response.json()
      setCompetitors(data)
    } catch (error) {
      console.error('获取排行榜失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 🔧 新增：获取模型统计数据（脱敏版本）
  const fetchModelStats = async (modelId: string) => {
    if (modelStats[modelId]) {
      return // 已加载
    }

    try {
      const apiUrl = getApiUrl(`/api/tournament/model/${modelId}/stats`)
      const response = await fetch(apiUrl)
      const data = await response.json()
      
      setModelStats(prev => ({
        ...prev,
        [modelId]: data
      }))
    } catch (error) {
      console.error('获取统计数据失败:', error)
    }
  }

  const toggleStats = (modelId: string) => {
    if (expandedModel === modelId) {
      setExpandedModel(null)
    } else {
      setExpandedModel(modelId)
      fetchModelStats(modelId)
    }
  }

  // 🔧 渲染战绩条（W/L/D + 对手）
  const renderRecentForm = (form: RecentMatch[]) => {
    return (
      <div className="flex flex-wrap items-center gap-1">
        {form.map((match, idx) => (
          <div
            key={idx}
            className={`px-2 py-1 rounded flex items-center space-x-1 text-xs font-medium ${
              match.result === 'W'
                ? 'bg-green-100 text-green-700 border border-green-300'
                : match.result === 'L'
                ? 'bg-red-100 text-red-700 border border-red-300'
                : 'bg-gray-100 text-gray-700 border border-gray-300'
            }`}
            title={`${match.result === 'W' ? '胜' : match.result === 'L' ? '负' : '平'} vs ${match.opponent}`}
          >
            <span className="font-bold">{match.result}</span>
            <span className="text-[10px] opacity-75">vs</span>
            <span className="truncate max-w-[60px]">{match.opponent}</span>
          </div>
        ))}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6 flex items-center justify-center min-h-[60vh]">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold flex items-center">
          <Trophy className="w-8 h-8 mr-2 text-yellow-600" />
          天梯榜
        </h1>
        
        <button
          onClick={() => navigate('/')}
          className="flex items-center space-x-2 px-4 py-2 bg-gray-900 text-white rounded hover:bg-gray-700 transition"
        >
          <Home className="w-4 h-4" />
          <span>返回主页</span>
        </button>
      </div>

      {/* 🔧 隐私保护提示 */}
      <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        🔒 为保护用户隐私，仅展示模型的统计数据，不显示具体对战内容
      </div>

      <div className="space-y-4">
        {competitors.map((comp, i) => (
          <div
            key={comp.model_id}
            onClick={() => toggleStats(comp.model_id)}
            className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition cursor-pointer"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <div className={`
                  text-3xl font-bold
                  ${i === 0 ? 'text-yellow-600' : i === 1 ? 'text-gray-400' : i === 2 ? 'text-orange-600' : 'text-gray-400'}
                `}>
                  #{i + 1}
                </div>
                <div>
                  <h3 className="text-xl font-bold hover:text-blue-600 transition">
                    {comp.display_name}
                  </h3>
                  <div className="text-sm text-gray-500">
                    {comp.matches_played} 场 · 胜率 {comp.win_rate}% · {comp.provider}
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="text-3xl font-bold text-blue-600">
                  {comp.elo_rating}
                </div>
                <div className="text-sm text-gray-500">ELO Rating</div>
              </div>
            </div>

            {/* 战绩统计 */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-2 bg-green-50 rounded">
                <div className="text-2xl font-bold text-green-600">{comp.wins}</div>
                <div className="text-xs text-gray-600">胜</div>
              </div>
              <div className="text-center p-2 bg-red-50 rounded">
                <div className="text-2xl font-bold text-red-600">{comp.losses}</div>
                <div className="text-xs text-gray-600">负</div>
              </div>
              <div className="text-center p-2 bg-gray-50 rounded">
                <div className="text-2xl font-bold text-gray-600">{comp.draws}</div>
                <div className="text-xs text-gray-600">平</div>
              </div>
            </div>

            {/* 🔧 展开的统计数据（脱敏版本） */}
            {expandedModel === comp.model_id && (
              <div 
                className="mt-4 space-y-3 border-t pt-4"
                onClick={(e) => e.stopPropagation()}
              >
                {modelStats[comp.model_id] ? (
                  <>
                    {/* 最近战绩 */}
                    <div className="bg-gray-50 rounded p-3">
                      <div className="text-xs text-gray-600 mb-2">最近10场战绩</div>
                      {renderRecentForm(modelStats[comp.model_id].recent_form)}
                    </div>

                    {/* 关键指标 */}
                    <div className="grid grid-cols-2 gap-3">
                      {/* 连胜/连败 */}
                      {modelStats[comp.model_id].win_streak > 0 && (
                        <div className="bg-green-50 rounded p-3">
                          <div className="flex items-center space-x-2">
                            <TrendingUp className="w-4 h-4 text-green-600" />
                            <span className="text-sm text-gray-700">
                              连胜 <span className="font-bold text-green-600">{modelStats[comp.model_id].win_streak}</span> 场
                            </span>
                          </div>
                        </div>
                      )}
                      
                      {modelStats[comp.model_id].loss_streak > 0 && (
                        <div className="bg-red-50 rounded p-3">
                          <div className="flex items-center space-x-2">
                            <TrendingDown className="w-4 h-4 text-red-600" />
                            <span className="text-sm text-gray-700">
                              连败 <span className="font-bold text-red-600">{modelStats[comp.model_id].loss_streak}</span> 场
                            </span>
                          </div>
                        </div>
                      )}

                      {/* 历史最高ELO */}
                      <div className="bg-blue-50 rounded p-3">
                        <div className="text-xs text-gray-600">历史最高</div>
                        <div className="text-lg font-bold text-blue-600">
                          {modelStats[comp.model_id].peak_elo}
                        </div>
                      </div>

                      {/* ELO趋势 */}
                      <div className={`rounded p-3 ${
                        modelStats[comp.model_id].elo_trend > 0 
                          ? 'bg-green-50' 
                          : modelStats[comp.model_id].elo_trend < 0 
                          ? 'bg-red-50' 
                          : 'bg-gray-50'
                      }`}>
                        <div className="text-xs text-gray-600">近期趋势</div>
                        <div className={`text-lg font-bold flex items-center space-x-1 ${
                          modelStats[comp.model_id].elo_trend > 0 
                            ? 'text-green-600' 
                            : modelStats[comp.model_id].elo_trend < 0 
                            ? 'text-red-600' 
                            : 'text-gray-600'
                        }`}>
                          {modelStats[comp.model_id].elo_trend > 0 ? (
                            <TrendingUp className="w-4 h-4" />
                          ) : modelStats[comp.model_id].elo_trend < 0 ? (
                            <TrendingDown className="w-4 h-4" />
                          ) : (
                            <Minus className="w-4 h-4" />
                          )}
                          <span>{modelStats[comp.model_id].elo_trend > 0 ? '+' : ''}{modelStats[comp.model_id].elo_trend}</span>
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center text-gray-400 py-4 text-sm">
                    无
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {competitors.length === 0 && (
        <div className="text-center text-gray-500 py-12">
          暂无数据，快去竞技场开始第一场比赛吧！
        </div>
      )}
    </div>
  )
}
