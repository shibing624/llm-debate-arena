/**
 * 环境配置文件
 * 从 .env 文件读取配置
 */

/// <reference types="vite/client" />

// 是否为开发环境
export const IS_DEV = import.meta.env.VITE_IS_DEV === 'true' || import.meta.env.DEV

// API Base URL
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * 获取完整的 API URL
 * @param path API 路径（以 / 开头）
 * @returns 完整的 API URL
 * 
 * 逻辑：
 * 1. 如果设置了 VITE_API_BASE_URL（非默认值），则使用完整 URL
 * 2. 否则，开发环境使用完整 URL，生产环境使用相对路径
 */
export function getApiUrl(path: string): string {
  // 如果显式设置了 API_BASE_URL（不是默认值），则始终使用它
  const hasCustomBaseUrl = import.meta.env.VITE_API_BASE_URL && 
                           import.meta.env.VITE_API_BASE_URL !== 'http://localhost:8000'
  
  if (hasCustomBaseUrl || IS_DEV) {
    // 使用完整 URL
    return `${API_BASE_URL}${path}`
  } else {
    // 生产环境且未设置自定义 URL：使用相对路径（通过 Nginx 代理）
    return path
  }
}

/**
 * 获取 SSE Stream URL
 * @param path API 路径（以 / 开头）
 * @returns 完整的 Stream URL
 */
export function getStreamUrl(path: string): string {
  const hasCustomBaseUrl = import.meta.env.VITE_API_BASE_URL && 
                           import.meta.env.VITE_API_BASE_URL !== 'http://localhost:8000'
  
  if (hasCustomBaseUrl || IS_DEV) {
    return `${API_BASE_URL}${path}`
  } else {
    return path
  }
}
