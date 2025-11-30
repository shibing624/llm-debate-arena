import { useState, useCallback, useRef } from 'react'

interface SSEMessage {
  type: string
  [key: string]: any
}

export function useSSE() {
  const [messages, setMessages] = useState<SSEMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [currentMatchId, setCurrentMatchId] = useState<string | null>(null)
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null)

  const connect = useCallback((url: string, config: any) => {
    console.log('📡 正在连接 SSE:', url)
    console.log('📤 配置:', config)

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
        setIsConnected(false)
        setCurrentMatchId(null)
        readerRef.current = null
      })
  }, [])

  const clearMessages = useCallback(() => {
    console.log('🗑️ 清空消息')
    setMessages([])
    setCurrentMatchId(null)
  }, [])

  const loadMessages = useCallback((historyMessages: SSEMessage[]) => {
    console.log('📥 加载历史消息:', historyMessages.length, '条')
    setMessages(historyMessages)
  }, [])

  return {
    messages,
    isConnected,
    currentMatchId,
    connect,
    clearMessages,
    loadMessages,
  }
}
