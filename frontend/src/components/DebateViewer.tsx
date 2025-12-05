import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Award, Loader2, ChevronDown } from 'lucide-react'
import { useState, useEffect } from 'react'

interface Message {
  type: string
  [key: string]: any
}

interface Props {
  messages: Message[]
  proponentModel?: string
  opponentModel?: string
  isTimeout?: boolean
}

interface StreamingTurn {
  round: number
  speaker: string
  content: string
  isStreaming: boolean
  toolCalls: any[]
}

export default function DebateViewer({ messages, proponentModel, opponentModel, isTimeout }: Props) {
  const [streamingTurns, setStreamingTurns] = useState<Map<string, StreamingTurn>>(new Map())
  const [completedTurns, setCompletedTurns] = useState<any[]>([])
  const [statusMessages, setStatusMessages] = useState<any[]>([])
  const [result, setResult] = useState<any>(null)
  const [eloUpdate, setEloUpdate] = useState<any>(null)
  const [judgeProgress, setJudgeProgress] = useState<any>(null)
  const [collapsedTurns, setCollapsedTurns] = useState<Set<string>>(new Set()) // 默认全部展开，记录用户手动折叠的卡片
  const [processedMessageIds, setProcessedMessageIds] = useState<Set<number>>(new Set())

  // 🔧 当 messages 数组清空或大幅减少时，重置所有状态
  useEffect(() => {
    if (messages.length === 0) {
      console.log('🗑️ 消息数组已清空，重置所有状态')
      setStreamingTurns(new Map())
      setCompletedTurns([])
      setStatusMessages([])
      setResult(null)
      setEloUpdate(null)
      setJudgeProgress(null)
      setCollapsedTurns(new Set())
      setProcessedMessageIds(new Set())
    }
  }, [messages.length])

  useEffect(() => {
    console.log('📩 收到新消息:', messages[messages.length - 1])
    
    // 只处理新消息，避免重复
    messages.forEach((msg, index) => {
      if (processedMessageIds.has(index)) return
      
      switch (msg.type) {
        case 'status':
          setStatusMessages((prev) => [...prev, msg])
          break

        case 'turn_delta':
          // ✅ 流式内容增量 - 实时更新
          setStreamingTurns((prev) => {
            const key = `${msg.speaker}-${msg.round}`
            const existing = prev.get(key) || {
              round: msg.round,
              speaker: msg.speaker,
              content: '',
              isStreaming: true,
              toolCalls: []
            }
            
            return new Map(prev).set(key, {
              ...existing,
              content: existing.content + msg.delta
            })
          })
          break

        case 'turn_tool_call':
          // 工具调用
          setStreamingTurns((prev) => {
            const key = `${msg.speaker}-${msg.round}`
            const existing = prev.get(key)
            if (existing) {
              return new Map(prev).set(key, {
                ...existing,
                toolCalls: [...existing.toolCalls, msg.tool_call]
              })
            }
            return prev
          })
          break

        case 'turn_tool_result':
          // 工具执行结果
          setStreamingTurns((prev) => {
            const key = `${msg.speaker}-${msg.round}`
            const existing = prev.get(key)
            if (existing) {
              const updatedToolCalls = existing.toolCalls.map(tc => 
                tc.function.name === msg.tool_name 
                  ? { ...tc, result: msg.result }
                  : tc
              )
              return new Map(prev).set(key, {
                ...existing,
                toolCalls: updatedToolCalls
              })
            }
            return prev
          })
          break

        case 'turn_complete':
          // 发言完成 - 只添加一次
          const turnKey = `${msg.turn.speaker_role}-${msg.turn.round_number}`
          setStreamingTurns((prev) => {
            prev.delete(turnKey)
            return new Map(prev)
          })
          setCompletedTurns((prev) => {
            // 检查是否已存在相同的 turn
            const exists = prev.some(
              t => t.speaker_role === msg.turn.speaker_role && 
                   t.round_number === msg.turn.round_number
            )
            if (exists) {
              console.log('⚠️ 跳过重复的 turn:', turnKey)
              return prev
            }
            return [...prev, msg.turn]
          })
          break

        case 'judge_progress':
          setJudgeProgress(msg)
          break

        case 'judge_complete':
          setResult(msg.result)
          setJudgeProgress(null)
          break

        case 'elo_update':
          setEloUpdate(msg.data)
          break
      }
      
      // 标记该消息已处理
      setProcessedMessageIds((prev) => new Set(prev).add(index))
    })
  }, [messages, processedMessageIds])

  const currentStatus = statusMessages[statusMessages.length - 1]?.content

  // 折叠/展开切换（反转逻辑：默认展开，点击后折叠）
  const toggleCollapse = (key: string) => {
    setCollapsedTurns((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(key)) {
        newSet.delete(key) // 从折叠列表移除 = 展开
      } else {
        newSet.add(key) // 添加到折叠列表 = 折叠
      }
      return newSet
    })
  }

  // 截断内容用于预览
  const getPreviewContent = (content: string, maxLength: number = 200) => {
    if (content.length <= maxLength) return content
    return content.substring(0, maxLength) + '...'
  }

  // 合并完成的和流式的发言
  const allTurns = [...completedTurns]
  streamingTurns.forEach((turn) => {
    allTurns.push({
      round_number: turn.round,
      speaker_role: turn.speaker,
      content: turn.content,
      tool_calls: turn.toolCalls.map(tc => ({
        tool_name: tc.function?.name || 'unknown',
        arguments: tc.function?.arguments || '',
        result: tc.result
      })),
      isStreaming: true
    })
  })

  // 按轮次排序
  allTurns.sort((a, b) => {
    if (a.round_number !== b.round_number) return a.round_number - b.round_number
    return a.speaker_role === 'proponent' ? -1 : 1
  })

  return (
    <div className="space-y-4">
      {/* 状态提示 - 轻量化 */}
      <AnimatePresence>
        {currentStatus && !result && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-xs text-gray-500 text-center py-2"
          >
            {currentStatus}
          </motion.p>
        )}
      </AnimatePresence>

      {/* 裁判进度 */}
      {judgeProgress && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-white border border-gray-200 p-4 rounded-lg shadow-sm"
        >
          <div className="text-center mb-2 text-sm text-gray-700">
            ⚖️ 裁判评分中... ({judgeProgress.current}/{judgeProgress.total})
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5">
            <div
              className="bg-gray-800 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${judgeProgress.progress * 100}%` }}
            />
          </div>
        </motion.div>
      )}

      {/* 辩论记录 */}
      <div className="grid grid-cols-2 gap-3">
        {allTurns.map((turn, i) => {
          const isProponent = turn.speaker_role === 'proponent'
          const isStreaming = turn.isStreaming
          const turnKey = `${turn.speaker_role}-${turn.round_number}`
          const isCollapsed = collapsedTurns.has(turnKey) // 默认展开，检查是否在折叠列表中
          const canCollapse = !isStreaming && turn.content.length > 200 // 是否可以折叠

          return (
            <motion.div
              key={`${turn.speaker_role}-${turn.round_number}-${i}`}
              initial={{ opacity: 0, x: isProponent ? -20 : 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
              className={`
                ${isProponent ? 'col-start-1' : 'col-start-2'}
                p-4 rounded-lg bg-white border border-gray-200 shadow-sm hover:shadow-md transition-shadow
                ${isProponent ? 'border-l-2 border-l-black' : 'border-r-2 border-r-black'}
              `}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <span className={`text-sm font-semibold ${isProponent ? 'text-black' : 'text-gray-700'}`}>
                    {isProponent ? '🔵 正方' : '🔴 反方'}
                    {isProponent && proponentModel && (
                      <span className="text-xs font-normal text-gray-500 ml-1">- {proponentModel.toUpperCase()}</span>
                    )}
                    {!isProponent && opponentModel && (
                      <span className="text-xs font-normal text-gray-500 ml-1">- {opponentModel.toUpperCase()}</span>
                    )}
                  </span>
                  <span className="text-xs text-gray-400">·</span>
                  <span className="text-xs text-gray-500">Round {turn.round_number}</span>
                  {isStreaming && (
                    <>
                      <span className="text-xs text-gray-400">·</span>
                      <span className="flex items-center text-xs text-gray-400">
                        <Loader2 className="w-3 h-3 animate-spin mr-1" />
                        思考中
                      </span>
                    </>
                  )}
                </div>
                {canCollapse && (
                  <button
                    onClick={() => toggleCollapse(turnKey)}
                    className="p-1 hover:bg-gray-100 rounded transition-colors"
                    aria-label={isCollapsed ? '展开' : '折叠'}
                    title={isCollapsed ? '展开完整内容' : '折叠内容'}
                  >
                    <motion.div
                      initial={false}
                      animate={{ rotate: isCollapsed ? 0 : 180 }}
                      transition={{ duration: 0.2 }}
                    >
                      <ChevronDown className="w-4 h-4 text-gray-400" />
                    </motion.div>
                  </button>
                )}
              </div>

              {/* Markdown 内容 - 极简样式 */}
              <motion.div
                className="prose prose-sm prose-gray max-w-none overflow-hidden"
                initial={false}
                animate={{
                  height: isCollapsed && canCollapse ? '16em' : 'auto'
                }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
              >
                <style>{`
                  .prose {
                    color: #1f2937;
                    font-size: 0.875rem;
                    line-height: 1.6;
                  }
                  .prose p {
                    margin-top: 0.5em;
                    margin-bottom: 0.5em;
                  }
                  .prose strong {
                    color: #000;
                    font-weight: 600;
                  }
                  .prose h1, .prose h2, .prose h3 {
                    color: #000;
                    font-weight: 600;
                    margin-top: 1em;
                    margin-bottom: 0.5em;
                  }
                  .prose h1 { font-size: 1.125rem; }
                  .prose h2 { font-size: 1rem; }
                  .prose h3 { font-size: 0.875rem; }
                  .prose ul, .prose ol {
                    margin-top: 0.5em;
                    margin-bottom: 0.5em;
                    padding-left: 1.5em;
                  }
                  .prose li {
                    margin-top: 0.25em;
                    margin-bottom: 0.25em;
                  }
                  .prose code {
                    background-color: #f3f4f6;
                    padding: 0.125rem 0.25rem;
                    border-radius: 0.25rem;
                    font-size: 0.8125rem;
                    color: #374151;
                    font-family: 'Monaco', 'Courier New', monospace;
                  }
                  .prose pre {
                    background-color: #f9fafb;
                    border: 1px solid #e5e7eb;
                    border-radius: 0.375rem;
                    padding: 0.75rem;
                    overflow-x: auto;
                    font-size: 0.8125rem;
                  }
                  .prose pre code {
                    background-color: transparent;
                    padding: 0;
                  }
                  .prose blockquote {
                    border-left: 2px solid #d1d5db;
                    padding-left: 1rem;
                    color: #6b7280;
                    font-style: italic;
                    margin: 0.5em 0;
                  }
                  .prose a {
                    color: #000;
                    text-decoration: underline;
                  }
                  .prose table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 1em 0;
                    font-size: 0.8125rem;
                  }
                  .prose table th {
                    background-color: #f3f4f6;
                    font-weight: 600;
                    text-align: left;
                    padding: 0.5rem 0.75rem;
                    border: 1px solid #d1d5db;
                    color: #1f2937;
                  }
                  .prose table td {
                    padding: 0.5rem 0.75rem;
                    border: 1px solid #e5e7eb;
                    color: #374151;
                  }
                  .prose table tr:nth-child(even) {
                    background-color: #f9fafb;
                  }
                  .prose table tr:hover {
                    background-color: #f3f4f6;
                  }
                `}</style>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {isCollapsed && canCollapse
                    ? getPreviewContent(turn.content) 
                    : turn.content}
                </ReactMarkdown>

                {/* 流式光标 */}
                {isStreaming && (
                  <span className="inline-block w-0.5 h-4 bg-gray-400 animate-pulse ml-0.5" />
                )}
              </motion.div>

              {/* 折叠提示 */}
              {canCollapse && isCollapsed && (
                <div className="mt-2 text-xs text-gray-400 text-center select-none">
                  点击右上角箭头展开完整内容
                </div>
              )}

              {/* 工具调用 */}
              {turn.tool_calls?.length > 0 && (
                <details className="mt-3 bg-gray-50 p-2.5 rounded border border-gray-200">
                  <summary className="cursor-pointer text-xs font-medium text-gray-600 hover:text-gray-900 select-none">
                    🔧 工具调用 ({turn.tool_calls.length})
                  </summary>
                  <div className="mt-2 space-y-2">
                    {turn.tool_calls.map((tc: any, j: number) => (
                      <div key={j} className="text-xs">
                        <div className="font-medium text-gray-700 flex items-center mb-1">
                          {tc.tool_name}
                          {!tc.result && <Loader2 className="w-3 h-3 animate-spin ml-2 text-gray-400" />}
                        </div>
                        {tc.result && (
                          <pre className="bg-white border border-gray-200 p-2 rounded text-xs overflow-x-auto font-mono text-gray-700">
                            {JSON.stringify(tc.result, null, 2)}
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </motion.div>
          )
        })}
      </div>

      {/* 超时提示 */}
      {isTimeout && !result && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-yellow-50 border border-yellow-300 rounded-lg p-4 mt-4"
        >
          <div className="flex items-center space-x-2">
            <span className="text-yellow-600 text-lg">⏰</span>
            <div>
              <div className="font-medium text-yellow-800">比赛超时</div>
              <div className="text-sm text-yellow-700">
                比赛已超过15分钟限制，已显示当前已输出的辩论内容。
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* 比赛结果 */}
      {result && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white border-2 border-black rounded-lg p-6 mt-6 shadow-lg"
        >
          <div className="text-center mb-6">
            <Award className="w-12 h-12 mx-auto text-black mb-2" />
            <h2 className="text-xl font-bold text-black tracking-tight">比赛结果</h2>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-gray-50 rounded border border-gray-200">
              <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">正方得分</div>
              <div className="text-2xl font-bold text-black">
                {result.final_scores.proponent}
              </div>
            </div>

            <div className="flex items-center justify-center">
              <div className={`text-2xl font-bold ${
                result.winner === 'proponent' ? 'text-black' :
                result.winner === 'opponent' ? 'text-gray-700' : 'text-gray-500'
              }`}>
                {result.winner === 'proponent' ? '正方获胜' :
                 result.winner === 'opponent' ? '反方获胜' : '平局'}
              </div>
            </div>

            <div className="text-center p-4 bg-gray-50 rounded border border-gray-200">
              <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">反方得分</div>
              <div className="text-2xl font-bold text-black">
                {result.final_scores.opponent}
              </div>
            </div>
          </div>

          {/* 判词 */}
          <div className="bg-gray-50 rounded border border-gray-200 p-4 mb-4">
            <h3 className="text-sm font-semibold mb-2 text-black uppercase tracking-wide">裁判判词</h3>
            <div className="text-xs text-gray-700 whitespace-pre-wrap leading-relaxed">
              {result.reasoning}
            </div>
          </div>

          {/* ELO 变化 */}
          {eloUpdate && (
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gray-50 border border-gray-200 p-3 rounded">
                <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">正方 ELO</div>
                <div className={`text-lg font-bold ${
                  eloUpdate.proponent.change >= 0 ? 'text-black' : 'text-gray-500'
                }`}>
                  {eloUpdate.proponent.change >= 0 ? '+' : ''}
                  {eloUpdate.proponent.change}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {eloUpdate.proponent.old_rating} → {eloUpdate.proponent.new_rating}
                </div>
              </div>

              <div className="bg-gray-50 border border-gray-200 p-3 rounded">
                <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">反方 ELO</div>
                <div className={`text-lg font-bold ${
                  eloUpdate.opponent.change >= 0 ? 'text-black' : 'text-gray-500'
                }`}>
                  {eloUpdate.opponent.change >= 0 ? '+' : ''}
                  {eloUpdate.opponent.change}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {eloUpdate.opponent.old_rating} → {eloUpdate.opponent.new_rating}
                </div>
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}
