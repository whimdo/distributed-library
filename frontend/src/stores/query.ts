import { defineStore } from 'pinia'
import { ref } from 'vue'
import { executeSql } from '@/api/client'
import type { QueryResponse } from '@/types'

export interface QueryHistoryItem {
  sql: string
  executedAt: string
  duration: number
  rowCount: number
  success: boolean
}

export const useQueryStore = defineStore('query', () => {
  const result = ref<QueryResponse | null>(null)
  const running = ref(false)
  const history = ref<QueryHistoryItem[]>([])

  async function run(sql: string): Promise<QueryResponse> {
    const started = performance.now()
    running.value = true
    try {
      const response = await executeSql(sql)
      result.value = response
      history.value.unshift({
        sql,
        executedAt: new Date().toISOString(),
        duration: Math.round(performance.now() - started),
        rowCount: response.row_count,
        success: true,
      })
      history.value = history.value.slice(0, 12)
      return response
    } catch (error) {
      history.value.unshift({
        sql,
        executedAt: new Date().toISOString(),
        duration: Math.round(performance.now() - started),
        rowCount: 0,
        success: false,
      })
      throw error
    } finally {
      running.value = false
    }
  }

  return { result, running, history, run }
})
