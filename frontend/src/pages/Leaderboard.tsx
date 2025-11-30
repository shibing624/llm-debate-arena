import { useState, useEffect } from 'react'
import { Trophy, Home } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

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

interface MatchHistory {
  match_id: string
  topic: string
  proponent_model_id: string
  opponent_model_id: string
  judge_result: any
  same_model_battle: boolean
  created_at: string
}

export default function Leaderboard() {
  const navigate = useNavigate()
  const [competitors, setCompetitors] = useState<Competitor[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedModel, setExpandedModel] = useState<string | null>(null)
  const [modelHistory, setModelHistory] = useState<Record<string, MatchHistory[]>>({})

  useEffect(() => {
    fetchLeaderboard()
  }, [])

  const fetchLeaderboard = async () => {
    try {
      const isDev = window.location.hostname === 'localhost'
      const apiUrl = isDev
        ? 'http://localhost:8000/api/tournament/leaderboard'
        : '/api/tournament/leaderboard'
      
      const response = await fetch(apiUrl)
      const data = await response.json()
      setCompetitors(data)
    } catch (error) {
      console.error('获取排行榜失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchModelHistory = async (modelId: string) => {
    if (modelHistory[modelId]) {
      return // 已加载
    }

    try {
      const isDev = window.location.hostname === 'localhost'
      const apiUrl = isDev
        ? `http://localhost:8000/api/tournament/matches/history?model_id=${modelId}&limit=20`
        : `/api/tournament/matches/history?model_id=${modelId}&limit=20`
      
      const response = await fetch(apiUrl)
      const data = await response.json()
      
      setModelHistory(prev => ({
        ...prev,
        [modelId]: data
      }))
    } catch (error) {
      console.error('获取历史记录失败:', error)
    }
  }

  // 判断该模型在某场比赛中的胜负
  const getMatchResult = (match: MatchHistory, modelId: string): 'win' | 'loss' | 'draw' => {
    if (!match.judge_result || !match.judge_result.winner) {
      return 'draw'
    }
    
    const winner = match.judge_result.winner
    const isProponent = match.proponent_model_id === modelId
    
    if (winner === 'draw') {
      return 'draw'
    } else if ((winner === 'proponent' && isProponent) || (winner === 'opponent' && !isProponent)) {
      return 'win'
    } else {
      return 'loss'
    }
  }

  const toggleHistory = (modelId: string) => {
    if (expandedModel === modelId) {
      setExpandedModel(null)
    } else {
      setExpandedModel(modelId)
      fetchModelHistory(modelId)
    }
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

      <div className="space-y-4">
        {competitors.map((comp, i) => (
          <div
            key={comp.model_id}
            onClick={() => toggleHistory(comp.model_id)}
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

            {/* 展开的历史记录 */}
            {expandedModel === comp.model_id && (
              <div 
                className="mt-4 space-y-2 max-h-96 overflow-y-auto border-t pt-4"
                onClick={(e) => e.stopPropagation()}
              >
                {modelHistory[comp.model_id]?.length > 0 ? (
                  modelHistory[comp.model_id].map((match) => {
                    const result = getMatchResult(match, comp.model_id)
                    const opponentModel = match.proponent_model_id === comp.model_id 
                      ? match.opponent_model_id 
                      : match.proponent_model_id
                    
                    return (
                      <div
                        key={match.match_id}
                        className="p-3 bg-gray-50 rounded border border-gray-200 text-sm"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="font-medium text-gray-900 mb-1">
                              {match.topic}
                            </div>
                            <div className="text-xs text-gray-500 flex items-center space-x-2">
                              <span>vs {opponentModel}</span>
                              {match.same_model_battle && (
                                <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded">
                                  同模型对战
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">
                              {new Date(match.created_at).toLocaleDateString('zh-CN')}
                            </div>
                          </div>
                          <div
                            className={`ml-4 px-3 py-1 rounded text-xs font-semibold ${
                              result === 'win'
                                ? 'bg-green-100 text-green-700'
                                : result === 'loss'
                                ? 'bg-red-100 text-red-700'
                                : 'bg-gray-100 text-gray-700'
                            }`}
                          >
                            {result === 'win' ? '胜' : result === 'loss' ? '负' : '平'}
                          </div>
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <div className="text-center text-gray-400 py-4 text-sm">
                    无记录
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
