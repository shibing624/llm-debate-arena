import { useState, useEffect } from 'react'
import { Play, Loader2, Plus, LogIn, LogOut, ChevronLeft, ChevronRight, Check, MoreVertical, Share2, Edit2, Trash2 } from 'lucide-react'
import { useSSE } from '../hooks/useSSE'
import { useToast } from '../hooks/useToast'
import { ToastContainer } from '../components/Toast'
import DebateViewer from '../components/DebateViewer'
import { useNavigate } from 'react-router-dom'
import { getApiUrl, getStreamUrl } from '../config'

interface ModelOption {
  value: string
  label: string
}

const PERSONALITIES = [
  { value: '', label: '默认' },
  { value: 'rational', label: '🧠 理性' },
  { value: 'aggressive', label: '⚔️ 激进' },
  { value: 'diplomatic', label: '🤝 温和' },
  { value: 'humorous', label: '😄 幽默' },
  { value: 'academic', label: '📚 学术' },
]

const AVAILABLE_TOOLS = [
  { value: 'python_interpreter', label: '🐍 Python' },
  { value: 'web_search', label: '🔍 搜索' },
  { value: 'calculator', label: '🔢 计算器' },
]

const TOPIC_EXAMPLES = [
  '远程办公比办公室办公更高效',
  '量子计算会在10年内改变世界',
  '35岁程序员真的没有出路吗?',
  '996是奋斗还是剥削?',
  '社交媒体让人更孤独了吗?',
  '真爱存在吗?'
]

interface Match {
  match_id: string
  topic: string
  proponent_model_id: string
  opponent_model_id: string
  status: string
  created_at: string
  finished_at: string | null
}

export default function ArenaNew() {
  const [models, setModels] = useState<ModelOption[]>([])
  const [loadingModels, setLoadingModels] = useState(true)
  const [topic, setTopic] = useState('')
  const [propModel, setPropModel] = useState('')
  const [oppModel, setOppModel] = useState('')
  const [propPersonality, setPropPersonality] = useState('')
  const [oppPersonality, setOppPersonality] = useState('')
  const [rounds, setRounds] = useState(3)
  const [judges, setJudges] = useState<string[]>([])
  const [enabledTools, setEnabledTools] = useState<string[]>([])
  const [isStarting, setIsStarting] = useState(false)
  const [historyMatches, setHistoryMatches] = useState<Match[]>([])
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true)  // 默认隐藏历史记录
  const [user, setUser] = useState<any>(null)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [loginEmail, setLoginEmail] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [menuOpen, setMenuOpen] = useState<string | null>(null)
  const [renameModal, setRenameModal] = useState<{ matchId: string; currentTitle: string } | null>(null)
  const [newTitle, setNewTitle] = useState('')
  
  const navigate = useNavigate()
  const { toasts, toast, removeToast } = useToast()
  const { messages, currentMatchId, isTimeout, connect, clearMessages, loadMessages } = useSSE()

  // 切换裁判选择
  const toggleJudge = (judgeModel: string) => {
    setJudges((prev) => {
      if (prev.includes(judgeModel)) {
        if (prev.length <= 2) {
          toast.warning('至少需要2个裁判')
          return prev
        }
        return prev.filter((j) => j !== judgeModel)
      } else {
        return [...prev, judgeModel]
      }
    })
  }

  // 切换工具选择
  const toggleTool = (tool: string) => {
    setEnabledTools((prev) => {
      if (prev.includes(tool)) {
        return prev.filter((t) => t !== tool)
      } else {
        return [...prev, tool]
      }
    })
  }

  // 加载历史记录
  const fetchHistory = async () => {
    try {
      // 如果用户已登录，添加 user_id 参数
      const params = new URLSearchParams({ limit: '50' })
      if (user?.id) {
        params.append('user_id', user.id.toString())
      }
      
      const apiUrl = getApiUrl(`/api/tournament/matches/history?${params}`)
      const response = await fetch(apiUrl)
      const data = await response.json()
      setHistoryMatches(data)
    } catch (error) {
      console.error('获取历史记录失败:', error)
    }
  }

  // 加载模型列表
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const apiUrl = getApiUrl('/api/tournament/leaderboard')
        const response = await fetch(apiUrl)
        const data = await response.json()
        
        // 转换为下拉选项格式
        const modelOptions: ModelOption[] = data.map((competitor: any) => ({
          value: competitor.model_id,
          label: competitor.display_name
        }))
        
        setModels(modelOptions)
        
        // 设置默认选择（第一个和第二个模型）
        if (modelOptions.length >= 2) {
          setPropModel(modelOptions[0].value)
          setOppModel(modelOptions[1].value)
          // 默认选择前两个模型作为裁判
          setJudges([modelOptions[0].value, modelOptions[1].value])
        } else if (modelOptions.length === 1) {
          setPropModel(modelOptions[0].value)
          setOppModel(modelOptions[0].value)
          setJudges([modelOptions[0].value])
        }
        
        setLoadingModels(false)
      } catch (error) {
        console.error('获取模型列表失败:', error)
        toast.error('获取模型列表失败')
        setLoadingModels(false)
      }
    }
    
    fetchModels()
  }, [])

  useEffect(() => {
    // 检查登录状态
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')
    if (token && userData) {
      setUser(JSON.parse(userData))
    }
    
    // 初始加载历史记录（不依赖 user 状态，直接读取 localStorage）
    const loadInitialHistory = async () => {
      try {
        const params = new URLSearchParams({ limit: '50' })
        
        // 从 localStorage 直接读取 user_id
        if (userData) {
          const parsedUser = JSON.parse(userData)
          if (parsedUser.id) {
            params.append('user_id', parsedUser.id.toString())
          }
        }
        
        const apiUrl = getApiUrl(`/api/tournament/matches/history?${params}`)
        const response = await fetch(apiUrl)
        const data = await response.json()
        setHistoryMatches(data)
      } catch (error) {
        console.error('获取历史记录失败:', error)
      }
    }
    
    loadInitialHistory()
  }, [])
  
  // 当用户状态变化时（登录/登出），重新加载历史记录
  useEffect(() => {
    // 跳过首次渲染（已经在上面加载过了）
    const isFirstRender = localStorage.getItem('token') && user === null
    if (!isFirstRender) {
      fetchHistory()
    }
  }, [user])

  // 点击外部关闭菜单
  useEffect(() => {
    const handleClickOutside = () => setMenuOpen(null)
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  // 登录处理
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!loginEmail || !loginPassword) {
      toast.warning('请输入邮箱和密码')
      return
    }

    setLoginLoading(true)
    
    try {
      const apiUrl = getApiUrl('/api/auth/login')
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          username: loginEmail, // 使用邮箱作为用户名
          password: loginPassword 
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || '登录失败')
      }

      // 保存登录信息
      localStorage.setItem('token', data.token)
      localStorage.setItem('user', JSON.stringify(data.user))
      setUser(data.user)
      setShowLoginModal(false)
      setLoginEmail('')
      setLoginPassword('')
      toast.success('登录成功！')
    } catch (err: any) {
      toast.error(err.message)
    } finally {
      setLoginLoading(false)
    }
  }

  // 登出处理
  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
    toast.info('已退出登录')
  }

  const startMatch = async () => {
    if (!topic.trim()) {
      toast.warning('请输入辩题')
      return
    }

    if (judges.length < 2) {
      toast.warning('至少需要2个裁判')
      return
    }

    setIsStarting(true)
    
    // 🔧 清空当前消息，准备接收新的流式输出
    clearMessages()

    const config = {
      topic: topic.trim(),
      topic_difficulty: 'medium',
      proponent_model: propModel,
      opponent_model: oppModel,
      proponent_personality: propPersonality || 'rational',
      opponent_personality: oppPersonality || 'rational',
      rounds: rounds,
      judges: judges,
      enabled_tools: enabledTools,
      user_id: user?.id || null,
    }

    const apiUrl = getStreamUrl('/api/tournament/match/stream')
    connect(apiUrl, config)
    
    // 🔧 立即刷新历史记录（新比赛会在后端立即创建 FIGHTING 状态的记录）
    setTimeout(() => {
      fetchHistory()
    }, 500) // 稍微延迟，确保后端已创建记录
  }

  // 监听比赛结束、错误或超时
  useEffect(() => {
    const lastMessage = messages[messages.length - 1]
    if (lastMessage?.type === 'match_end' || lastMessage?.type === 'error' || lastMessage?.type === 'timeout') {
      setIsStarting(false)
      fetchHistory() // 刷新历史记录
    }
  }, [messages])

  // 🔧 简化：加载历史记录的比赛（直接切换到该比赛，断开当前 SSE）
  const loadHistoryMatch = async (matchId: string) => {
    try {
      // 🔧 先断开当前 SSE 连接，停止流式输出
      clearMessages()
      setIsStarting(false) // 停止当前比赛状态
      
      const apiUrl = getApiUrl(`/api/tournament/match/${matchId}`)
      const response = await fetch(apiUrl)
      if (!response.ok) {
        throw new Error('加载失败')
      }
      
      const data = await response.json()
      
      // 转换为消息格式
      const historyMsgs: any[] = []
      
      // 添加辩论记录
      if (data.transcript && Array.isArray(data.transcript)) {
        data.transcript.forEach((turn: any) => {
          historyMsgs.push({
            type: 'turn_complete',
            turn: turn
          })
        })
      }
      
      // 添加裁判结果
      if (data.judge_result) {
        historyMsgs.push({
          type: 'judge_complete',
          result: data.judge_result
        })
      }
      
      // 添加 ELO 变化
      if (data.elo_changes) {
        historyMsgs.push({
          type: 'elo_update',
          data: data.elo_changes
        })
      }
      
      // 根据比赛状态添加不同的标记
      if (data.status === 'FINISHED') {
        // 已完成的比赛，添加结束标记（用于显示分享按钮）
        historyMsgs.push({
          type: 'match_end',
          match_id: matchId
        })
      } else if (data.status === 'FIGHTING' || data.status === 'JUDGING') {
        // 进行中的比赛，添加进行中标记
        historyMsgs.push({
          type: 'match_in_progress',
          match_id: matchId,
          status: data.status
        })
        // 设置为进行中状态
        setIsStarting(true)
      }
      
      // 🔧 加载历史消息，并传递 matchId（用于分享功能）
      loadMessages(historyMsgs, matchId)
      
      // 更新显示信息
      setTopic(data.topic || '')
      setPropModel(data.proponent_model_id || propModel)
      setOppModel(data.opponent_model_id || oppModel)
    } catch (error) {
      console.error('加载历史记录失败:', error)
      toast.error('加载历史记录失败')
    }
  }

  // 删除历史记录
  const handleDeleteMatch = async (matchId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setMenuOpen(null)
    
    if (!confirm('确定要删除这场比赛记录吗？')) return
    
    try {
      const apiUrl = getApiUrl(`/api/tournament/match/${matchId}`)
      const response = await fetch(apiUrl, { method: 'DELETE' })
      if (response.ok) {
        setHistoryMatches(prev => prev.filter(m => m.match_id !== matchId))
        toast.success('删除成功')
      } else {
        toast.error('删除失败')
      }
    } catch (error) {
      console.error('删除失败:', error)
      toast.error('删除失败')
    }
  }

  // 打开重命名弹窗
  const openRenameModal = (match: Match, e: React.MouseEvent) => {
    e.stopPropagation()
    setMenuOpen(null)
    setRenameModal({
      matchId: match.match_id,
      currentTitle: match.topic
    })
    setNewTitle(match.topic)
  }

  // 重命名比赛
  const handleRename = async () => {
    if (!renameModal || !newTitle.trim()) return
    
    try {
      const apiUrl = getApiUrl(`/api/tournament/match/${renameModal.matchId}/rename`)
      const response = await fetch(apiUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle.trim() })
      })
      
      if (response.ok) {
        setHistoryMatches(prev => prev.map(m => 
          m.match_id === renameModal.matchId 
            ? { ...m, topic: newTitle.trim() }
            : m
        ))
        setRenameModal(null)
        toast.success('重命名成功')
      } else {
        toast.error('重命名失败')
      }
    } catch (error) {
      console.error('重命名失败:', error)
      toast.error('重命名失败')
    }
  }

  // 分享 - 复制链接
  const handleShareMatch = (matchId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setMenuOpen(null)
    
    const shareUrl = `${window.location.origin}/match/${matchId}`
    navigator.clipboard.writeText(shareUrl).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      toast.success('链接已复制')
    })
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Toast 容器 */}
      <ToastContainer toasts={toasts} removeToast={removeToast} />

      {/* 登录弹窗 */}
      {showLoginModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowLoginModal(false)}>
          <div className="bg-white rounded-lg p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-xl font-bold mb-4">登录</h2>
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                <input
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
                  placeholder="请输入邮箱"
                  disabled={loginLoading}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
                  placeholder="请输入密码"
                  disabled={loginLoading}
                />
              </div>
              <button
                type="submit"
                disabled={loginLoading}
                className="w-full bg-gray-900 text-white py-2 rounded-lg hover:bg-gray-700 transition disabled:opacity-50"
              >
                {loginLoading ? '登录中...' : '登录'}
              </button>
              <button
                type="button"
                onClick={() => setShowLoginModal(false)}
                className="w-full text-gray-600 py-2 text-sm hover:text-gray-900"
              >
                取消
              </button>
              
              {/* 注册入口 */}
              <div className="text-center text-sm mt-2">
                <span className="text-gray-600">还没有账号？</span>
                <button
                  onClick={() => {
                    setShowLoginModal(false)
                    navigate('/register')
                  }}
                  className="ml-1 text-gray-900 font-medium hover:underline"
                >
                  立即注册
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 左侧固定侧边栏 */}
      <aside className={`${sidebarCollapsed ? 'w-0' : 'w-60'} bg-white border-r border-gray-200 flex flex-col transition-all duration-300 overflow-hidden relative`}>
        {/* 顶部 */}
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={() => {
              clearMessages()
              setTopic('')
              setIsStarting(false) // 重置比赛状态，解除输入框禁用
            }}
            className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-gray-900 text-white rounded hover:bg-gray-800 transition text-sm"
          >
            <Plus className="w-4 h-4" />
            <span>新建对话</span>
          </button>
        </div>

        {/* 历史记录列表 */}
        {!sidebarCollapsed && (
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {user ? (
              historyMatches.length > 0 ? (
                historyMatches.map((match) => (
                  <div
                    key={match.match_id}
                    className="relative group w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded border border-gray-200 transition cursor-pointer"
                    onClick={() => loadHistoryMatch(match.match_id)}
                  >
                    <div className="text-xs font-medium text-gray-900 line-clamp-2 mb-1 pr-6">
                      {match.topic}
                    </div>
                    <div className="text-xs text-gray-500 flex items-center justify-between">
                      <span className="truncate">{match.proponent_model_id} vs {match.opponent_model_id}</span>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {new Date(match.created_at).toLocaleDateString('zh-CN')}
                    </div>
                    
                    {/* 三点菜单按钮 */}
                    <div className="absolute top-2 right-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setMenuOpen(menuOpen === match.match_id ? null : match.match_id)
                        }}
                        className="p-1 hover:bg-gray-200 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <MoreVertical className="w-4 h-4 text-gray-500" />
                      </button>
                      
                      {/* 下拉菜单 */}
                      {menuOpen === match.match_id && (
                        <div 
                          className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50 min-w-[100px]"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <button
                            onClick={(e) => handleShareMatch(match.match_id, e)}
                            className="w-full px-3 py-1.5 text-left text-xs hover:bg-gray-50 flex items-center space-x-2"
                          >
                            <Share2 className="w-3 h-3" />
                            <span>分享</span>
                          </button>
                          <button
                            onClick={(e) => openRenameModal(match, e)}
                            className="w-full px-3 py-1.5 text-left text-xs hover:bg-gray-50 flex items-center space-x-2"
                          >
                            <Edit2 className="w-3 h-3" />
                            <span>重命名</span>
                          </button>
                          <button
                            onClick={(e) => handleDeleteMatch(match.match_id, e)}
                            className="w-full px-3 py-1.5 text-left text-xs hover:bg-gray-50 text-red-600 flex items-center space-x-2"
                          >
                            <Trash2 className="w-3 h-3" />
                            <span>删除</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-400 text-xs py-8">
                  暂无历史记录
                </div>
              )
            ) : (
              <div className="text-center py-8 px-4">
                <p className="text-xs text-gray-500 mb-3">
                  登录后可查看历史记录
                </p>
                <button
                  onClick={() => setShowLoginModal(true)}
                  className="text-xs px-4 py-2 bg-gray-900 text-white rounded hover:bg-gray-700 transition"
                >
                  立即登录
                </button>
              </div>
            )}
          </div>
        )}

        {/* 底部用户信息 */}
        {!sidebarCollapsed && (
          <div className="p-4 border-t border-gray-200">
            {user ? (
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 bg-gray-900 text-white rounded-full flex items-center justify-center font-semibold text-sm">
                  {user.username?.[0]?.toUpperCase() || 'U'}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {user.username}
                  </div>
                  <button
                    onClick={handleLogout}
                    className="text-xs text-gray-500 hover:text-gray-700 flex items-center space-x-1"
                  >
                    <LogOut className="w-3 h-3" />
                    <span>退出</span>
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowLoginModal(true)}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded transition"
              >
                <LogIn className="w-4 h-4" />
                <span className="text-sm">登录</span>
              </button>
            )}
          </div>
        )}
      </aside>

      {/* 侧边栏折叠按钮 */}
      <button
        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        className="fixed left-0 top-1/2 -translate-y-1/2 z-10 bg-white border border-gray-200 rounded-r-lg p-2 hover:bg-gray-50 transition shadow-sm"
        style={{ left: sidebarCollapsed ? '0' : '240px' }}
      >
        {sidebarCollapsed ? (
          <ChevronRight className="w-4 h-4 text-gray-600" />
        ) : (
          <ChevronLeft className="w-4 h-4 text-gray-600" />
        )}
      </button>

      {/* 右侧主内容区 */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* 顶部栏 */}
        <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-gray-900">辩论竞技场</h1>
          
          <div className="flex items-center space-x-3">
            {/* 分享按钮 - 辩论完成后显示 */}
            {messages.some(m => m.type === 'match_end') && currentMatchId && (
              <button
                onClick={() => {
                  const shareUrl = `${window.location.origin}/match/${currentMatchId}`
                  navigator.clipboard.writeText(shareUrl).then(() => {
                    setCopied(true)
                    setTimeout(() => setCopied(false), 2000)
                    toast.success('链接已复制，可分享给朋友')
                  })
                }}
                className="flex items-center space-x-1 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded transition text-sm"
                title="分享辩论"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4 text-green-600" />
                    <span className="text-green-600">已复制</span>
                  </>
                ) : (
                  <>
                    <Share2 className="w-4 h-4 text-gray-600" />
                    <span>分享</span>
                  </>
                )}
              </button>
            )}
            
            {/* 比赛进行中提示 */}
            {messages.some(m => m.type === 'match_in_progress') && (
              <span className="flex items-center space-x-1 px-3 py-1.5 bg-yellow-50 text-yellow-700 rounded text-sm border border-yellow-200">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>比赛进行中</span>
              </span>
            )}
            
            {/* 天梯榜入口 */}
            <a
              href="/leaderboard"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 bg-gray-900 text-white rounded hover:bg-gray-800 transition text-sm inline-block"
            >
              天梯榜
            </a>
          </div>
        </div>

        {/* 内容区 */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-[85%] mx-auto space-y-4">
            {/* 配置区 - 极简紧凑 */}
            <div className="bg-white border border-gray-200 rounded p-4">
              {loadingModels ? (
                <div className="text-center py-8 text-gray-500">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                  <p className="text-sm">加载模型列表中...</p>
                </div>
              ) : (
                <>
                  {/* 模型选择 - 单行 */}
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div>
                      <label className="block text-xs font-medium mb-1 text-gray-600">正方</label>
                      <select
                        value={propModel}
                        onChange={(e) => setPropModel(e.target.value)}
                        className="w-full p-2 border border-gray-300 rounded text-sm"
                        disabled={isStarting || models.length === 0}
                      >
                        {models.length === 0 && (
                          <option value="">暂无可用模型</option>
                        )}
                        {models.map((m) => (
                          <option key={m.value} value={m.value}>{m.label}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-medium mb-1 text-gray-600">反方</label>
                      <select
                        value={oppModel}
                        onChange={(e) => setOppModel(e.target.value)}
                        className="w-full p-2 border border-gray-300 rounded text-sm"
                        disabled={isStarting || models.length === 0}
                      >
                        {models.length === 0 && (
                          <option value="">暂无可用模型</option>
                        )}
                        {models.map((m) => (
                          <option key={m.value} value={m.value}>{m.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* 性格选择 - 可选 */}
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <select
                      value={propPersonality}
                      onChange={(e) => setPropPersonality(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded text-xs"
                      disabled={isStarting || models.length === 0}
                    >
                      {PERSONALITIES.map((p) => (
                        <option key={p.value} value={p.value}>{p.label}</option>
                      ))}
                    </select>

                    <select
                      value={oppPersonality}
                      onChange={(e) => setOppPersonality(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded text-xs"
                      disabled={isStarting || models.length === 0}
                    >
                      {PERSONALITIES.map((p) => (
                        <option key={p.value} value={p.value}>{p.label}</option>
                      ))}
                    </select>
                  </div>

                  {/* 高级设置 - 单行 */}
                  <div className="flex items-center space-x-3 mb-3 text-xs">
                    <div className="flex items-center space-x-2">
                      <span className="text-gray-600">轮数</span>
                      <select
                        value={rounds}
                        onChange={(e) => setRounds(Number(e.target.value))}
                        className="p-1 border border-gray-300 rounded"
                        disabled={isStarting || models.length === 0}
                      >
                        <option value={1}>1</option>
                        <option value={2}>2</option>
                        <option value={3}>3</option>
                      </select>
                    </div>

                    <div className="border-l border-gray-200 pl-3 flex items-center space-x-2">
                      <span className="text-gray-600">裁判</span>
                      {models.slice(0, 5).map((model) => (
                        <button
                          key={model.value}
                          onClick={() => toggleJudge(model.value)}
                          disabled={isStarting || models.length === 0}
                          className={`px-2 py-1 rounded text-xs transition ${
                            judges.includes(model.value)
                              ? 'bg-gray-900 text-white'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          {model.label}
                        </button>
                      ))}
                    </div>

                    <div className="border-l border-gray-200 pl-3 flex items-center space-x-2">
                      <span className="text-gray-600">工具</span>
                      {AVAILABLE_TOOLS.map((tool) => (
                        <button
                          key={tool.value}
                          onClick={() => toggleTool(tool.value)}
                          disabled={isStarting || models.length === 0}
                          className={`px-2 py-1 rounded text-xs transition ${
                            enabledTools.includes(tool.value)
                              ? 'bg-gray-900 text-white'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          {tool.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* 辩题输入 - 多行 */}
                  <div className="mb-3">
                    <textarea
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      placeholder="输入辩题..."
                      rows={3}
                      className="w-full p-2 border border-gray-300 rounded text-sm resize-none"
                      disabled={isStarting || models.length === 0}
                    />
                    {/* 辩题示例 */}
                    <div className="mt-2 flex flex-wrap gap-2">
                      {TOPIC_EXAMPLES.map((example, idx) => (
                        <button
                          key={idx}
                          onClick={() => setTopic(example)}
                          disabled={isStarting || models.length === 0}
                          className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition disabled:opacity-50"
                        >
                          {example}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* 开始按钮 - 紧挨辩题 */}
                  <button
                    onClick={startMatch}
                    className="w-full bg-gray-900 text-white text-sm font-medium py-2.5 rounded hover:bg-gray-800 transition flex items-center justify-center space-x-2 disabled:bg-gray-300"
                    disabled={!topic.trim() || isStarting || models.length === 0}
                  >
                    {isStarting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>比赛进行中...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        <span>开始对决</span>
                      </>
                    )}
                  </button>
                </>
              )}
            </div>

            {/* 辩论展示区 */}
            {messages.length > 0 && (
              <DebateViewer 
                messages={messages} 
                proponentModel={propModel}
                opponentModel={oppModel}
                isTimeout={isTimeout}
              />
            )}
          </div>
        </div>
      </main>

      {/* 重命名弹窗 */}
      {renameModal && (
        <div 
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          onClick={() => setRenameModal(null)}
        >
          <div 
            className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold mb-4">重命名</h3>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 mb-4"
              placeholder="输入新标题"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleRename()
              }}
            />
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setRenameModal(null)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition"
              >
                取消
              </button>
              <button
                onClick={handleRename}
                className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition"
              >
                确定
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
