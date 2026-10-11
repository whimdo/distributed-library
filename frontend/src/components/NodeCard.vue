<template>
  <article class="node-card" :class="status">
    <div class="node-head"><span class="node-id">{{ nodeId }}</span><span class="status-label"><i></i>{{ statusText }}</span></div>
    <strong>{{ title }}</strong>
    <p>{{ database || '等待服务响应' }}</p>
    <div class="node-foot"><span>{{ role }}</span><span class="mono">{{ port }}</span></div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ nodeId: string; title: string; database?: string; role: string; port: string; status: 'online' | 'offline' | 'checking' }>()
const statusText = computed(() => ({ online: 'ONLINE', offline: 'OFFLINE', checking: 'CHECKING' })[props.status])
</script>

<style scoped>
.node-card { padding: 17px; min-height: 140px; border: 1px solid var(--line); border-radius: 9px; background: linear-gradient(145deg, rgba(14,31,49,.85), rgba(9,23,38,.85)); position: relative; overflow: hidden; }
.node-card::after { content: ''; position: absolute; inset: auto 0 0; height: 2px; background: #405569; }
.node-card.online::after { background: var(--cyan); box-shadow: 0 0 12px rgba(41,216,199,.45); }
.node-card.offline::after { background: var(--red); }
.node-head, .node-foot { display: flex; align-items: center; justify-content: space-between; }
.node-id { color: #4c677f; font: 9px 'DM Mono'; letter-spacing: .12em; }
.status-label { color: #6a8298; font: 8px 'DM Mono'; }
.status-label i { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: currentColor; margin-right: 5px; }
.online .status-label { color: var(--cyan); }.offline .status-label { color: var(--red); }
.node-card > strong { display: block; margin-top: 16px; font-size: 14px; font-weight: 600; }
.node-card p { color: #6f8aa2; font: 10px 'DM Mono'; margin: 5px 0 17px; }
.node-foot { color: #566e84; font-size: 9px; }
</style>
