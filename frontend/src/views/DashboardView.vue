<template>
  <div>
    <div class="page-intro">
      <div><h2>成都高校图书资源网络</h2><p>统一查看协调节点、数据分片与资源运行情况</p></div>
      <el-button :loading="loading" plain @click="loadDashboard"><el-icon><Refresh /></el-icon>刷新数据</el-button>
    </div>

    <div class="metrics-grid">
      <article v-for="metric in metrics" :key="metric.label" class="metric-card panel">
        <div class="metric-icon" :style="{ color: metric.color, background: `${metric.color}16` }"><el-icon><component :is="metric.icon" /></el-icon></div>
        <div><span>{{ metric.label }}</span><strong>{{ metric.value }}</strong><small>{{ metric.note }}</small></div>
      </article>
    </div>

    <div class="dashboard-main section-gap">
      <section class="panel cluster-panel">
        <div class="panel-header"><div class="panel-title">分布式节点拓扑</div><span class="panel-subtitle">LIVE HEALTH CHECK</span></div>
        <div class="panel-body">
          <div class="cluster-line"><span></span><span></span><span></span></div>
          <div class="node-grid">
            <NodeCard v-for="node in nodes" :key="node.key" :node-id="node.id" :title="node.title" :database="node.database" :role="node.role" :port="node.port" :status="node.status" />
          </div>
        </div>
      </section>

      <section class="panel distribution-panel">
        <div class="panel-header"><div class="panel-title">校区分片分布</div><span class="panel-subtitle">HORIZONTAL SHARDING</span></div>
        <div class="panel-body">
          <div v-for="site in siteDistribution" :key="site.id" class="distribution-row">
            <div class="distribution-label"><span>Site {{ site.id }}</span><strong>{{ site.count }} 个校区</strong></div>
            <div class="distribution-track"><i :style="{ width: `${site.percent}%`, background: site.color }"></i></div>
          </div>
          <div class="fragment-note"><el-icon><Connection /></el-icon><p><strong>水平分片策略</strong><span>按校区所属管理区域路由到数据节点</span></p></div>
        </div>
      </section>
    </div>

    <section class="panel section-gap">
      <div class="panel-header"><div class="panel-title">最近的系统事件</div><RouterLink to="/monitor" class="view-all">查看全部 →</RouterLink></div>
      <div class="event-table">
        <div v-for="event in recentEvents" :key="`${event.query_id}-${event.timestamp}-${event.event_type}`" class="event-line">
          <span class="event-time mono">{{ timeOnly(event.timestamp) }}</span>
          <span class="event-source">{{ event.source }}</span>
          <span class="event-type mono">{{ event.event_type }}</span>
          <span class="event-message">{{ event.message }}</span>
        </div>
        <el-empty v-if="!recentEvents.length" description="暂无查询事件，执行一次 SQL 后将在这里显示" :image-size="55" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, onMounted, ref } from 'vue'
import { Collection, Connection, Files, OfficeBuilding, Reading, Refresh } from '@element-plus/icons-vue'
import NodeCard from '@/components/NodeCard.vue'
import { executeSql, getEvents, getHealth, nodeApis } from '@/api/client'
import type { QueryEvent } from '@/types'

const loading = ref(false)
const counts = ref({ books: 0, campuses: 0, libraries: 0, copies: 0 })
const campuses = ref<Array<{ site_id: number }>>([])
const recentEvents = ref<QueryEvent[]>([])
type NodeStatus = 'online' | 'offline' | 'checking'
interface DashboardNode { key: string; id: string; title: string; role: string; port: string; database: string; status: NodeStatus }
const nodes = ref<DashboardNode[]>([
  { key: 'coordinator', id: 'NODE 00', title: '协调节点', role: '查询解析 · 全局目录', port: ':8000', database: '', status: 'checking' as const },
  { key: 'site1', id: 'NODE 01', title: '数据站点一', role: '西北片区', port: ':8001', database: '', status: 'checking' as const },
  { key: 'site2', id: 'NODE 02', title: '数据站点二', role: '中东片区', port: ':8002', database: '', status: 'checking' as const },
  { key: 'site3', id: 'NODE 03', title: '数据站点三', role: '中南片区', port: ':8003', database: '', status: 'checking' as const },
])

const metrics = computed(() => [
  { label: '统一书目', value: counts.value.books, note: '全局目录数据', color: '#29d8c7', icon: markRaw(Collection) },
  { label: '接入校区', value: counts.value.campuses, note: '4 所成都高校', color: '#5797ff', icon: markRaw(OfficeBuilding) },
  { label: '共享图书馆', value: counts.value.libraries, note: '跨校资源共享', color: '#a98bff', icon: markRaw(Reading) },
  { label: '实体馆藏', value: counts.value.copies, note: '分布于三个站点', color: '#f6b84a', icon: markRaw(Files) },
])

const siteDistribution = computed(() => [1, 2, 3].map((id, index) => {
  const count = campuses.value.filter((campus) => Number(campus.site_id) === id).length
  return { id, count, percent: counts.value.campuses ? count / counts.value.campuses * 100 : 0, color: ['#29d8c7', '#5797ff', '#a98bff'][index] }
}))

function timeOnly(value: string) { return new Date(value).toLocaleTimeString('zh-CN', { hour12: false }) }

async function loadDashboard() {
  loading.value = true
  await Promise.all(Object.entries(nodeApis).map(async ([key, api]) => {
    const node = nodes.value.find((item) => item.key === key)!
    try { const health = await getHealth(api); node.status = 'online'; node.database = health.database }
    catch { node.status = 'offline'; node.database = '连接失败' }
  }))
  const queryJobs = [
    executeSql('SELECT COUNT(*) AS total FROM book'),
    executeSql('SELECT campus_id, site_id FROM campus ORDER BY campus_id'),
    executeSql('SELECT COUNT(*) AS total FROM library'),
    executeSql('SELECT COUNT(*) AS total FROM book_copy'),
  ]
  try {
    const [books, campusResult, libraries, copies] = await Promise.all(queryJobs)
    campuses.value = campusResult.rows as Array<{ site_id: number }>
    counts.value = { books: Number(books.rows[0]?.total || 0), campuses: campusResult.row_count, libraries: Number(libraries.rows[0]?.total || 0), copies: Number(copies.rows[0]?.total || 0) }
    recentEvents.value = (await getEvents(nodeApis.coordinator)).slice(-6).reverse()
  } catch { /* Health cards still communicate the failure. */ }
  loading.value = false
}

onMounted(loadDashboard)
</script>

<style scoped>
.metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }
.metric-card { padding: 19px; display: flex; align-items: center; gap: 15px; }
.metric-icon { width: 42px; height: 42px; border-radius: 8px; display: grid; place-items: center; font-size: 20px; }
.metric-card > div:last-child { display: grid; grid-template-columns: 1fr auto; align-items: baseline; flex: 1; }
.metric-card span { font-size: 11px; color: #718ba2; }
.metric-card strong { grid-row: span 2; font: 500 28px 'DM Mono'; color: #e6f0f8; }
.metric-card small { color: #486278; font-size: 9px; margin-top: 5px; }
.dashboard-main { display: grid; grid-template-columns: 2fr 1fr; gap: 18px; }
.cluster-panel .panel-body { position: relative; }
.node-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 11px; position: relative; z-index: 1; }
.cluster-line { position: absolute; left: 15%; right: 15%; top: 49%; height: 1px; background: rgba(41,216,199,.14); }
.distribution-row { margin-bottom: 20px; }
.distribution-label { display: flex; justify-content: space-between; margin-bottom: 8px; color: #7b93aa; font-size: 10px; }
.distribution-label strong { color: #afc1d2; font-weight: 500; }
.distribution-track { height: 4px; border-radius: 5px; background: rgba(255,255,255,.045); overflow: hidden; }
.distribution-track i { display: block; height: 100%; border-radius: inherit; }
.fragment-note { display: flex; align-items: center; gap: 11px; padding: 12px; margin-top: 28px; border: 1px solid rgba(41,216,199,.12); background: rgba(41,216,199,.035); border-radius: 7px; color: var(--cyan); }
.fragment-note p { margin: 0; display: flex; flex-direction: column; }
.fragment-note strong { color: #a9c6cf; font-size: 10px; }.fragment-note span { color: #587487; font-size: 9px; margin-top: 3px; }
.view-all { color: var(--cyan); font-size: 10px; }
.event-table { padding: 7px 18px 12px; }
.event-line { display: grid; grid-template-columns: 85px 100px 170px 1fr; align-items: center; min-height: 39px; border-bottom: 1px solid rgba(151,179,207,.07); font-size: 10px; }
.event-time { color: #4e687f; }.event-source { color: #91a8bd; }.event-type { color: #57a7b9; }.event-message { color: #8298ab; }
</style>
