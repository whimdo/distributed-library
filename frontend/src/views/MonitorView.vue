<template>
  <div>
    <div class="page-intro">
      <div><h2>命令与处理过程</h2><p>直接显示各节点接收、执行和发送的命令，不写入日志文件</p></div>
      <div class="monitor-actions"><el-switch v-model="autoScroll" active-text="自动滚动" /><el-button @click="events = []">清空屏幕</el-button></div>
    </div>

    <div class="monitor-nodes">
      <button v-for="node in nodeList" :key="node.key" :class="{ active: selectedNode === node.key }" @click="selectedNode = node.key">
        <span><i :class="connections[node.key]"></i>{{ node.name }}</span><small>{{ filteredCount(node.key) }} EVENTS</small>
      </button>
    </div>

    <section class="terminal panel">
      <header><div><i></i><i></i><i></i><span>distributed-library / realtime-event-stream</span></div><span class="connection-label">● {{ connectedCount }}/{{ streamEntries.length }} STREAMS CONNECTED</span></header>
      <div ref="terminalBody" class="terminal-body">
        <div v-for="(event, index) in visibleEvents" :key="`${event.timestamp}-${event.source}-${index}`" class="log-line" :class="event.event_type.toLowerCase()">
          <span class="log-time">{{ formatTime(event.timestamp) }}</span><span class="log-source">[{{ event.source.toUpperCase() }}]</span><span class="log-type">{{ event.event_type }}</span><span class="log-message">{{ event.message }}</span>
          <code v-if="event.details?.sql">{{ event.details.sql }}</code>
        </div>
        <div v-if="!visibleEvents.length" class="terminal-empty"><span>_</span>等待当前权限范围内的节点命令。</div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { getEvents, nodeApis, websocketUrl } from '@/api/client'
import type { QueryEvent } from '@/types'
import { useAuthStore } from '@/stores/auth'

const allNodes = [
  { key: 'all', name: '全部节点' }, { key: 'coordinator', name: '协调节点' }, { key: 'site1', name: 'Site 1' }, { key: 'site2', name: 'Site 2' }, { key: 'site3', name: 'Site 3' },
]
type NodeKey = keyof typeof nodeApis
const auth = useAuthStore()
const streamEntries = computed<Array<[NodeKey, string]>>(() => auth.isGlobalAdmin
  ? Object.entries(nodeApis) as Array<[NodeKey, string]>
  : [[`site${auth.user?.managed_site_id}` as NodeKey, nodeApis[`site${auth.user?.managed_site_id}` as NodeKey]]])
const nodeList = computed(() => auth.isGlobalAdmin ? allNodes : [{ key: 'all', name: '本站点' }, { key: `site${auth.user?.managed_site_id}`, name: `Site ${auth.user?.managed_site_id}` }])
const selectedNode = ref('all'), events = ref<QueryEvent[]>([]), autoScroll = ref(true), terminalBody = ref<HTMLElement>()
const connections = reactive<Record<string, string>>({ coordinator: 'pending', site1: 'pending', site2: 'pending', site3: 'pending' })
const sockets: WebSocket[] = []
const visibleEvents = computed(() => selectedNode.value === 'all' ? events.value : events.value.filter((event) => event.source === selectedNode.value))
const connectedCount = computed(() => streamEntries.value.filter(([key]) => connections[key] === 'online').length)
function filteredCount(key: string) { return key === 'all' ? events.value.length : events.value.filter((event) => event.source === key).length }
function formatTime(value: string) { return new Date(value).toLocaleTimeString('zh-CN', { hour12: false, fractionalSecondDigits: 3 }) }
async function scrollBottom() { if (!autoScroll.value) return; await nextTick(); if (terminalBody.value) terminalBody.value.scrollTop = terminalBody.value.scrollHeight }
watch(visibleEvents, scrollBottom, { deep: true })

async function connectNode(key: NodeKey, api: string) {
  try { const historical = await getEvents(api); events.value.push(...historical.map((item) => ({ ...item, source: key === 'coordinator' ? item.source : key }))) } catch { /* websocket can still connect */ }
  const socket = new WebSocket(websocketUrl(api)); sockets.push(socket)
  socket.onopen = () => { connections[key] = 'online' }
  socket.onerror = () => { connections[key] = 'offline' }
  socket.onclose = () => { connections[key] = 'offline' }
  socket.onmessage = (message) => {
    try { const event = JSON.parse(message.data) as QueryEvent; events.value.push({ ...event, source: key === 'coordinator' ? event.source : key }); events.value = events.value.slice(-500) } catch { /* ignore malformed event */ }
  }
}

onMounted(() => { streamEntries.value.forEach(([key, api]) => connectNode(key, api)); scrollBottom() })
onBeforeUnmount(() => sockets.forEach((socket) => socket.close()))
</script>

<style scoped>
.monitor-actions { display: flex; gap: 15px; align-items: center; }
.monitor-nodes { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 16px; }.monitor-nodes button { display: flex; align-items: center; justify-content: space-between; height: 48px; padding: 0 14px; color: #70899f; background: rgba(13,27,44,.7); border: 1px solid var(--line); border-radius: 7px; cursor: pointer; }.monitor-nodes button.active { color: #c7e4e4; border-color: rgba(41,216,199,.3); background: rgba(41,216,199,.06); }.monitor-nodes button span { font-size: 10px; }.monitor-nodes small { font: 8px 'DM Mono'; color: #4f687e; }.monitor-nodes i { display: inline-block; width: 6px; height: 6px; margin-right: 7px; border-radius: 50%; background: var(--amber); }.monitor-nodes i.online { background: var(--cyan); box-shadow: 0 0 7px var(--cyan); }.monitor-nodes i.offline { background: var(--red); }
.terminal { overflow: hidden; }.terminal header { height: 45px; padding: 0 15px; display: flex; justify-content: space-between; align-items: center; background: #081522; border-bottom: 1px solid var(--line); }.terminal header > div { display: flex; align-items: center; gap: 6px; }.terminal header i { width: 8px; height: 8px; border-radius: 50%; background: #ff6e7d; }.terminal header i:nth-child(2) { background: #f6b84a; }.terminal header i:nth-child(3) { background: #29d8c7; }.terminal header span { margin-left: 8px; color: #476176; font: 9px 'DM Mono'; }.connection-label { color: var(--cyan) !important; font-size: 8px !important; }
.terminal-body { height: calc(100vh - 288px); min-height: 430px; overflow: auto; padding: 13px 16px; background: #06111c; font: 10px/1.75 'DM Mono'; }.log-line { display: grid; grid-template-columns: 92px 110px 165px minmax(250px, 1fr); border-bottom: 1px solid rgba(151,179,207,.035); padding: 4px 0; }.log-time { color: #405c71; }.log-source { color: var(--cyan); }.log-type { color: #648ca8; }.log-message { color: #9ab0c2; }.log-line code { grid-column: 2 / -1; margin: 3px 0 5px; padding: 5px 8px; white-space: pre-wrap; color: #7f9aaf; background: rgba(87,151,255,.05); border-left: 2px solid rgba(87,151,255,.35); }.log-line.error_occurred .log-type, .log-line.error_occurred .log-message { color: var(--red); }.log-line.result_sent .log-type { color: var(--amber); }.terminal-empty { padding: 30px; text-align: center; color: #3e586c; }.terminal-empty span { animation: blink 1s infinite; color: var(--cyan); } @keyframes blink { 50% { opacity: 0; } }
@media (max-width: 760px) { .monitor-actions { align-items: flex-end; flex-direction: column; }.terminal header > div span { display: none; }.log-line { grid-template-columns: 74px 80px 1fr; }.log-message { grid-column: 2 / -1; }.log-line code { grid-column: 1 / -1; }.terminal-body { padding: 10px; } }
</style>
