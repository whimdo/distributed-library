<template>
  <div v-if="result" class="plan-grid">
    <div class="route-summary">
      <div class="query-code">{{ result.query_id.slice(0, 12) }}</div>
      <div class="route-line">
        <div class="route-node primary"><span>协调节点</span><small>SQL 解析与优化</small></div>
        <div class="route-arrow">→</div>
        <div v-for="query in result.physical_queries" :key="query.target" class="route-node"><span>{{ labelTarget(query.target) }}</span><small>物理查询执行</small></div>
      </div>
    </div>

    <div class="event-list">
      <div v-for="(event, index) in result.events" :key="`${event.timestamp}-${index}`" class="event-row">
        <div class="event-index">{{ String(index + 1).padStart(2, '0') }}</div>
        <div class="event-rail"><i></i></div>
        <div class="event-content"><strong>{{ event.message }}</strong><span>{{ event.event_type }} · {{ event.source }}</span></div>
      </div>
    </div>

    <div v-if="result.physical_queries.length" class="physical-list">
      <div v-for="query in result.physical_queries" :key="query.target" class="physical-item">
        <span>{{ query.target }}</span><code>{{ query.sql }}</code>
      </div>
    </div>
  </div>
  <el-empty v-else description="执行查询后显示分解与优化过程" :image-size="65" />
</template>

<script setup lang="ts">
import type { QueryResponse } from '@/types'
defineProps<{ result: QueryResponse | null }>()
function labelTarget(target: string) { return target === 'coordinator_db' ? '主数据库' : target.replace('_db', '').toUpperCase() }
</script>

<style scoped>
.query-code { color: #587087; font: 10px 'DM Mono'; letter-spacing: .1em; }
.route-line { display: flex; align-items: center; gap: 12px; margin: 14px 0 23px; overflow-x: auto; padding-bottom: 3px; }
.route-node { min-width: 132px; padding: 11px 13px; border: 1px solid rgba(87,151,255,.2); background: rgba(87,151,255,.055); border-radius: 7px; display: flex; flex-direction: column; }
.route-node.primary { border-color: rgba(41,216,199,.3); background: rgba(41,216,199,.07); }
.route-node span { font-size: 12px; color: #c8d8e7; }
.route-node small { font-size: 9px; color: #607991; margin-top: 3px; }
.route-arrow { color: var(--cyan); }
.event-list { padding: 3px 0; }
.event-row { display: grid; grid-template-columns: 28px 16px 1fr; min-height: 50px; }
.event-index { color: #496279; font: 10px 'DM Mono'; padding-top: 2px; }
.event-rail { position: relative; }
.event-rail::after { content: ''; position: absolute; top: 9px; bottom: -7px; left: 3px; width: 1px; background: rgba(115,149,179,.18); }
.event-row:last-child .event-rail::after { display: none; }
.event-rail i { position: absolute; top: 4px; left: 0; width: 7px; height: 7px; border-radius: 50%; background: var(--cyan); box-shadow: 0 0 8px rgba(41,216,199,.55); }
.event-content { display: flex; flex-direction: column; }
.event-content strong { font-size: 11px; font-weight: 500; }
.event-content span { margin-top: 4px; color: #557087; font: 9px 'DM Mono'; }
.physical-list { border-top: 1px solid var(--line); margin-top: 7px; padding-top: 13px; }
.physical-item { margin-bottom: 12px; }
.physical-item span { display: block; color: var(--cyan); font: 9px 'DM Mono'; margin-bottom: 5px; }
.physical-item code { display: block; padding: 9px 10px; border-radius: 5px; background: #071522; color: #92a9bc; font: 10px/1.6 'DM Mono'; white-space: pre-wrap; word-break: break-all; }
</style>
