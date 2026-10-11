<template>
  <div class="result-wrap">
    <el-table v-if="rows.length" :data="rows" height="360" border>
      <el-table-column v-for="column in columns" :key="column" :prop="column" :label="column" min-width="150" show-overflow-tooltip>
        <template #default="scope">{{ formatValue(scope.row[column]) }}</template>
      </el-table-column>
    </el-table>
    <el-empty v-else description="查询未返回数据" :image-size="70" />
  </div>
</template>

<script setup lang="ts">
import type { DataRow } from '@/types'

defineProps<{ columns: string[]; rows: DataRow[] }>()

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return 'NULL'
  if (typeof value === 'object') return JSON.stringify(value)
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  return String(value)
}
</script>

<style scoped>
.result-wrap { min-height: 210px; }
</style>
