import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Copy, Check } from 'lucide-react'
import DebateViewer from '../components/DebateViewer'
import { getApiUrl } from '../config'

interface MatchDetail {
  match_id: string
  topic: string
  custom_title: string | null
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

export default function MatchShare() {
  const { matchId } = useParams<{ matchId: string }>()
  const [match, setMatch] = useState<MatchDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (matchId) {
      fetchMatch(matchId)
    }
  }, [matchId])

  const fetchMatch = async (id: string) => {
    try {
      const apiUrl = getApiUrl(`/api/tournament/match/${id}`)
      const response = await fetch(apiUrl)
      if (!response.ok) {
        throw new Error('比赛不存在')
      }
      const data = await response.json()
      setMatch(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // 转换为 DebateViewer 消息格式
  const convertToMessages = (detail: MatchDetail) => {
    const messages: any[] = []

    detail.transcript.forEach((turn: any) => {
      messages.push({
        type: 'turn_complete',
        turn: turn
      })
    })

    if (detail.judge_result) {
      messages.push({
        type: 'judge_complete',
        result: detail.judge_result
      })
    }

    if (detail.elo_changes) {
      messages.push({
        type: 'elo_update',
        data: detail.elo_changes
      })
    }

    return messages
  }

  // 复制链接
  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('复制失败:', err)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }

  if (error || !match) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <div className="text-gray-500 mb-4">{error || '比赛不存在'}</div>
        <Link to="/" className="text-blue-600 hover:underline">
          返回首页
        </Link>
      </div>
    )
  }

  const displayTitle = match.custom_title || match.topic

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link to="/" className="p-2 hover:bg-gray-100 rounded-lg transition">
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </Link>
            <div>
              <h1 className="text-lg font-semibold text-gray-900 line-clamp-1">
                {displayTitle}
              </h1>
              <div className="text-xs text-gray-500">
                {match.proponent_model_id} vs {match.opponent_model_id}
              </div>
            </div>
          </div>
          
          <button
            onClick={copyLink}
            className="flex items-center space-x-1 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition text-sm"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-green-600" />
                <span className="text-green-600">已复制</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4 text-gray-600" />
                <span>复制链接</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* 内容区 */}
      <div className="max-w-6xl mx-auto p-6">
        {/* 标题卡片 */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-2">{displayTitle}</h2>
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span>🔵 {match.proponent_model_id}</span>
            <span>vs</span>
            <span>🔴 {match.opponent_model_id}</span>
            <span>·</span>
            <span>{new Date(match.created_at).toLocaleString('zh-CN')}</span>
          </div>
        </div>

        {/* 辩论内容 */}
        <DebateViewer 
          messages={convertToMessages(match)}
          proponentModel={match.proponent_model_id}
          opponentModel={match.opponent_model_id}
        />
      </div>
    </div>
  )
}
