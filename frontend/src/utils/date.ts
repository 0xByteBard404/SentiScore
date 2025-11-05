/**
 * 格式化日期时间
 * @param date 日期字符串或Date对象
 * @returns 格式化后的日期时间字符串
 */
export const formatDate = (date: string | Date): string => {
  if (!date) return ''
  
  const d = typeof date === 'string' ? new Date(date) : date
  if (isNaN(d.getTime())) return ''
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

/**
 * 格式化日期（仅日期部分）
 * @param date 日期字符串或Date对象
 * @returns 格式化后的日期字符串
 */
export const formatDateOnly = (date: string | Date): string => {
  if (!date) return ''
  
  const d = typeof date === 'string' ? new Date(date) : date
  if (isNaN(d.getTime())) return ''
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  
  return `${year}-${month}-${day}`
}

/**
 * 获取北京时间的今日日期字符串 (YYYY-MM-DD)
 * @returns 今日日期字符串
 */
export const getBeijingToday = (): string => {
  // 创建当前时间的Date对象
  const now = new Date()
  
  // 转换为北京时间 (UTC+8)
  const beijingTime = new Date(now.getTime() + (8 * 60 * 60 * 1000))
  
  const year = beijingTime.getUTCFullYear()
  const month = String(beijingTime.getUTCMonth() + 1).padStart(2, '0')
  const day = String(beijingTime.getUTCDate()).padStart(2, '0')
  
  return `${year}-${month}-${day}`
}

/**
 * 将UTC时间转换为北京时间
 * @param date UTC时间字符串或Date对象
 * @returns 北京时间的Date对象
 */
export const utcToBeijing = (date: string | Date): Date => {
  const d = typeof date === 'string' ? new Date(date) : date
  if (isNaN(d.getTime())) return d
  
  // 转换为北京时间 (UTC+8)
  return new Date(d.getTime() + (8 * 60 * 60 * 1000))
}