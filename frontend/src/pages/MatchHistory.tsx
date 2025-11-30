import { useState, useEffect } from 'react'
import { Clock, Users, ChevronRight, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import DebateViewer from '../components/DebateViewer'

interface Match {
  match_id: string
  topic: string
  proponent_model_id: string
  opponent_model_id: string
  status: string
  created_at: string
  finished_at: string | null
}

interface MatchDetail {
  match_id: string
  topic: string
  topic_difficulty: string
  proponent_model_id: string
  opponent_model_id: string
  status: string
  transcript: any[]
  judge_result: any
  elo_changes: any
  created_at: string
  finished_at: string | null
}

export default function MatchHistory() {
  const [matches, setMatches] = useState<Match[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedMatch, setSelectedMatch] = useState<MatchDetail | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    try {
      const isDev = window.location.hostname === 'localhost'
      const apiUrl = isDev
        ? 'http://localhost:8000/api/tournament/matches/history'
        : '/api/tournament/matches/history'
      
      const response = await fetch(apiUrl)
      const data = await response.json()
      setMatches(data)
    } catch (error) {
      console.error('获取历史记录失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchMatchDetail = async (matchId: string) => {
    setLoadingDetail(true)
    try {
      const isDev = window.location.hostname === 'localhost'
      const apiUrl = isDev
        ? `http://localhost:8000/api/tournament/match/${matchId}`
        : `/api/tournament/match/${matchId}`
      
      const response = await fetch(apiUrl)
      const data = await response.json()
      setSelectedMatch(data)
    } catch (error) {
      console.error('获取比赛详情失败:', error)
      alert('获取比赛详情失败')
    } finally {
      setLoadingDetail(false)
    }
  }

  const closeDetail = () => {
    setSelectedMatch(null)
  }

  // 将比赛详情转换为 DebateViewer 需要的消息格式
  const convertToMessages = (detail: MatchDetail) => {
    const messages: any[] = []

    // 添加辩论回合
    detail.transcript.forEach((turn: any) => {
      messages.push({
        type: 'turn_complete',
        turn: turn
      })
    })

    // 添加裁判结果
    if (detail.judge_result) {
      messages.push({
        type: 'judge_complete',
        result: detail.judge_result
      })
    }

    // 添加 ELO 更新
    if (detail.elo_changes) {
      messages.push({
        type: 'elo_update',
        data: detail.elo_changes
      })
    }

    return messages
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6 flex items-center justify-center min-h-[60vh]">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }

  return (
    <>
      <div className="container mx-auto p-6 max-w-6xl">
        <h1 className="text-2xl font-bold mb-6 text-black tracking-tight flex items-center">
          <Clock className="w-6 h-6 mr-2" />
          历史记录
        </h1>

        <div className="space-y-3">
          {matches.map((match) => (
            <div
              key={match.match_id}
              onClick={() => fetchMatchDetail(match.match_id)}
              className="bg-white border border-gray-200 rounded-lg shadow-sm p-5 hover:shadow-md transition cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-base font-semibold mb-2 text-black">{match.topic}</h3>
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                    <div className="flex items-center space-x-1">
                      <Users className="w-4 h-4" />
                      <span>
                        {match.proponent_model_id} vs {match.opponent_model_id}
                      </span>
                    </div>
                  </div>

                  <div className="text-xs text-gray-500">
                    {new Date(match.created_at).toLocaleString('zh-CN')}
                    {match.finished_at && (
                      <> → {new Date(match.finished_at).toLocaleString('zh-CN')}</>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <div className={`
                    px-3 py-1 rounded text-xs font-medium
                    ${match.status === 'FINISHED' ? 'bg-green-50 text-green-700 border border-green-200' : 
                      match.status === 'FIGHTING' ? 'bg-yellow-50 text-yellow-700 border border-yellow-200' : 
                      'bg-gray-50 text-gray-700 border border-gray-200'}
                  `}>
                    {match.status === 'FINISHED' ? '已完成' : 
                     match.status === 'FIGHTING' ? '进行中' : 
                     match.status === 'JUDGING' ? '评判中' : '准备中'}
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {matches.length === 0 && !loading && (
          <div className="text-center text-gray-500 py-12">
            暂无历史记录
          </div>
        )}
      </div>

      {/* 比赛详情弹窗 */}
      <AnimatePresence>
        {(selectedMatch || loadingDetail) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={closeDetail}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-gray-50 rounded-lg shadow-xl max-w-7xl w-full max-h-[90vh] overflow-hidden flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              {/* 头部 */}
              <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
                <div className="flex-1">
                  <h2 className="text-lg font-bold text-black">
                    {selectedMatch?.topic || '加载中...'}
                  </h2>
                  {selectedMatch && (
                    <div className="text-xs text-gray-500 mt-1">
                      {selectedMatch.proponent_model_id} vs {selectedMatch.opponent_model_id}
                    </div>
                  )}
                </div>
                <button
                  onClick={closeDetail}
                  className="p-2 hover:bg-gray-100 rounded-lg transition"
                >
                  <X className="w-5 h-5 text-gray-600" />
                </button>
              </div>

              {/* 内容 */}
              <div className="flex-1 overflow-y-auto p-6">
                {loadingDetail ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="text-gray-500">加载比赛详情中...</div>
                  </div>
                ) : selectedMatch ? (
                  <DebateViewer messages={convertToMessages(selectedMatch)} />
                ) : null}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
