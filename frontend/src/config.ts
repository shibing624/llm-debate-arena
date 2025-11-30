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
 */
export function getApiUrl(path: string): string {
  if (IS_DEV) {
    // 开发环境：使用完整 URL
    return `${API_BASE_URL}${path}`
  } else {
    // 生产环境：使用相对路径（通过 Nginx 代理）
    return path
  }
}

/**
 * 获取 SSE Stream URL
 * @param path API 路径（以 / 开头）
 * @returns 完整的 Stream URL
 */
export function getStreamUrl(path: string): string {
  // SSE 始终使用完整 URL
  return IS_DEV ? `${API_BASE_URL}${path}` : path
}
