<template>
  <div>
    <div class="page-intro"><div><h2>用户逻辑表结构</h2><p>用户只需要理解逻辑模式，无需了解底层分片表和节点位置</p></div></div>
    <div class="schema-grid">
      <article v-for="table in tables" :key="table.logical_name" class="panel table-card">
        <header><div><el-icon><Grid /></el-icon><strong>{{ table.logical_name }}</strong></div><span :class="table.location">{{ table.location === 'coordinator' ? '主节点全局表' : '水平分片表' }}</span></header>
        <div class="column-list"><code v-for="column in table.columns" :key="column">{{ column }}</code></div>
        <footer><button @click="openQuery(table.logical_name)">在查询工作台中打开 →</button></footer>
      </article>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Grid } from '@element-plus/icons-vue'
import { getLogicalSchema } from '@/api/client'
import type { LogicalTable } from '@/types'
const router = useRouter(); const tables = ref<LogicalTable[]>([])
function openQuery(_name: string) { router.push('/query') }
onMounted(async () => { try { tables.value = await getLogicalSchema() } catch { /* empty state */ } })
</script>

<style scoped>
.schema-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.table-card { overflow: hidden; }
.table-card header { padding: 15px 17px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--line); }
.table-card header div { display: flex; align-items: center; gap: 9px; color: var(--cyan); }.table-card header strong { font: 500 13px 'DM Mono'; color: #d5e1ec; }
.table-card header span { color: #7592aa; font-size: 8px; padding: 3px 6px; border-radius: 3px; background: rgba(87,151,255,.09); }.table-card header span.fragmented { color: #d3a552; background: rgba(246,184,74,.08); }
.column-list { display: flex; flex-wrap: wrap; gap: 6px; align-content: flex-start; padding: 15px 17px; min-height: 125px; }
.column-list code { height: 23px; padding: 4px 7px; color: #7891a7; background: #081725; border: 1px solid rgba(151,179,207,.08); border-radius: 4px; font: 9px 'DM Mono'; }
.table-card footer { padding: 10px 17px; border-top: 1px solid var(--line); }.table-card footer button { color: var(--cyan); font-size: 9px; background: none; border: 0; cursor: pointer; padding: 0; }
</style>
