import { useState, useCallback, useRef } from 'react'

interface SSEMessage {
  type: string
  [key: string]: any
}

// 默认超时时间：15分钟
const DEFAULT_TIMEOUT_MS = 15 * 60 * 1000

export function useSSE() {
  const [messages, setMessages] = useState<SSEMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [currentMatchId, setCurrentMatchId] = useState<string | null>(null)
  const [isTimeout, setIsTimeout] = useState(false)
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // 清除超时定时器
  const clearTimeoutTimer = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
  }, [])

  const connect = useCallback((url: string, config: any, timeoutMs: number = DEFAULT_TIMEOUT_MS) => {
    console.log('📡 正在连接 SSE:', url)
    console.log('📤 配置:', config)
    console.log('⏱️ 超时设置:', timeoutMs / 1000 / 60, '分钟')

    // 重置超时状态
    setIsTimeout(false)

    // 🔧 如果已有连接，先关闭旧连接
    if (readerRef.current) {
      console.log('⚠️ 检测到旧的 SSE 连接，正在关闭...')
      try {
        readerRef.current.cancel()
        readerRef.current = null
      } catch (error) {
        console.error('关闭旧连接失败:', error)
      }
    }

    // 清除旧的超时定时器
    clearTimeoutTimer()

    // 设置超时定时器
    timeoutRef.current = setTimeout(() => {
      console.log('⏰ 比赛超时，强制断开连接')
      setIsTimeout(true)
      if (readerRef.current) {
        try {
          readerRef.current.cancel()
        } catch (error) {
          console.error('超时断开连接失败:', error)
        }
        readerRef.current = null
      }
      setIsConnected(false)
      // 添加超时消息
      setMessages((prev) => [...prev, { type: 'timeout', content: '比赛超时，已显示当前已输出的内容' }])
    }, timeoutMs)

    // 发起 POST 请求
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        console.log('✅ SSE 连接成功')
        setIsConnected(true)

        const reader = response.body?.getReader()
        const decoder = new TextDecoder()

        if (!reader) {
          throw new Error('无法获取响应流')
        }

        // 保存 reader 引用，用于关闭连接
        readerRef.current = reader

        // 读取流式数据
        let buffer = ''
        
        while (true) {
          const { done, value } = await reader.read()
          
          if (done) {
            console.log('🏁 SSE 流结束')
            clearTimeoutTimer() // 正常结束，清除超时定时器
            setIsConnected(false)
            setCurrentMatchId(null)
            readerRef.current = null // 清空 reader 引用
            break
          }

          // 解码数据
          buffer += decoder.decode(value, { stream: true })

          // 处理 SSE 数据（按行分割）
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // 保留最后一行（可能不完整）

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6) // 移除 "data: " 前缀
              try {
                const message = JSON.parse(data)
                console.log('📩 收到 SSE 消息:', message.type)
                
                // 捕获 match_id（支持 match_init 和 match_start）
                if (message.type === 'match_init' && message.match_id) {
                  setCurrentMatchId(message.match_id)
                  console.log('🆔 设置当前比赛ID (init):', message.match_id)
                } else if (message.type === 'match_start' && message.data?.match_id) {
                  // 兼容：如果已经在 match_init 设置过，这里就不重复设置
                  if (!message.match_id) {
                    setCurrentMatchId(message.data.match_id)
                    console.log('🆔 设置当前比赛ID (start):', message.data.match_id)
                  }
                } else if (message.type === 'match_end') {
                  clearTimeoutTimer() // 比赛正常结束，清除超时定时器
                  setCurrentMatchId(null)
                  console.log('🆔 清除当前比赛ID')
                }
                
                setMessages((prev) => [...prev, message])
              } catch (error) {
                console.error('❌ 解析 SSE 消息失败:', error, data)
              }
            }
          }
        }
      })
      .catch((error) => {
        console.error('❌ SSE 连接错误:', error)
        clearTimeoutTimer()
        setIsConnected(false)
        setCurrentMatchId(null)
        readerRef.current = null
      })
  }, [clearTimeoutTimer])

  // 断开当前 SSE 连接
  const disconnect = useCallback(() => {
    if (readerRef.current) {
      console.log('🔌 断开 SSE 连接')
      try {
        readerRef.current.cancel()
      } catch (error) {
        console.error('断开连接失败:', error)
      }
      readerRef.current = null
    }
    clearTimeoutTimer()
    setIsConnected(false)
  }, [clearTimeoutTimer])

  const clearMessages = useCallback(() => {
    console.log('🗑️ 清空消息')
    // 先断开连接，再清空消息
    disconnect()
    setMessages([])
    setCurrentMatchId(null)
    setIsTimeout(false)
  }, [disconnect])

  const loadMessages = useCallback((historyMessages: SSEMessage[], matchId?: string) => {
    console.log('📥 加载历史消息:', historyMessages.length, '条')
    // 先断开当前 SSE 连接，停止流式输出
    disconnect()
    // 设置历史消息
    setMessages(historyMessages)
    // 设置历史比赛的 matchId（用于分享功能）
    if (matchId) {
      setCurrentMatchId(matchId)
    }
    setIsTimeout(false)
  }, [disconnect])

  return {
    messages,
    isConnected,
    currentMatchId,
    isTimeout,
    connect,
    disconnect,
    clearMessages,
    loadMessages,
  }
}
