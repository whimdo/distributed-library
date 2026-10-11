<template>
  <div>
    <div class="page-intro"><div><h2>读者借阅记录</h2><p>使用读者编号定向访问其所属分片，避免遍历全部高校数据</p></div></div>
    <section class="search-card panel">
      <div><span>READER ID ROUTING</span><strong>输入读者编号查询</strong><p>编号首位标识数据站点，协调节点将自动执行站点裁剪。</p></div>
      <div class="search-form"><el-input v-model="readerId" size="large" placeholder="例如：110000000001" clearable @keyup.enter="search"><template #prefix><el-icon><User /></el-icon></template></el-input><el-button type="primary" size="large" :loading="loading" @click="search">查询借阅</el-button></div>
    </section>
    <div v-if="errorMessage" class="borrow-error">{{ errorMessage }}</div>
    <div class="borrow-grid section-gap">
      <section class="panel reader-panel">
        <div class="panel-header"><div class="panel-title">读者信息</div></div>
        <div v-if="reader" class="reader-card"><div class="avatar">{{ String(reader.reader_name).slice(0, 1) }}</div><strong>{{ reader.reader_name }}</strong><span>{{ reader.student_no }}</span><dl><dt>所属校区</dt><dd>{{ reader.home_campus_id }}</dd><dt>读者类型</dt><dd>{{ reader.reader_type }}</dd><dt>借阅数量</dt><dd>{{ reader.current_borrow_count }} / {{ reader.max_borrow_count }}</dd><dt>联网权限</dt><dd>{{ reader.network_permission ? '允许跨校借阅' : '仅限本校' }}</dd></dl></div>
        <el-empty v-else description="等待查询读者" :image-size="55" />
      </section>
      <section class="panel records-panel">
        <div class="panel-header"><div class="panel-title">借阅明细</div><span v-if="records.length" class="panel-subtitle">{{ records.length }} RECORDS</span></div>
        <div class="panel-body"><ResultTable :columns="recordColumns" :rows="records" /></div>
      </section>
    </div>
    <section v-if="plan" class="panel section-gap"><div class="panel-header"><div class="panel-title">本次路由说明</div></div><div class="route-explain"><span>逻辑查询</span><i>→</i><span>识别 reader_id 前缀</span><i>→</i><strong>{{ plan.selected_sites.length ? `仅访问 Site ${plan.selected_sites.join(', ')}` : '协调节点' }}</strong><i>→</i><span>返回合并结果</span></div></section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { User } from '@element-plus/icons-vue'
import ResultTable from '@/components/ResultTable.vue'
import { apiErrorMessage, executeSql } from '@/api/client'
import type { DataRow, QueryResponse } from '@/types'
const readerId = ref('110000000001'), reader = ref<DataRow>(), records = ref<DataRow[]>([]), plan = ref<QueryResponse>(), loading = ref(false), errorMessage = ref('')
const recordColumns = computed(() => records.value.length ? Object.keys(records.value[0]) : [])
async function search() {
  if (!/^\d+$/.test(readerId.value)) { errorMessage.value = '读者编号只能包含数字。'; return }
  loading.value = true; errorMessage.value = ''; reader.value = undefined; records.value = []
  try {
    const [readerResult, recordResult] = await Promise.all([
      executeSql(`SELECT reader_id, student_no, reader_name, home_campus_id, reader_type, network_permission, max_borrow_count, current_borrow_count, status FROM reader WHERE reader_id = ${readerId.value};`),
      executeSql(`SELECT borrow_id, book_id, copy_id, borrow_type, borrow_time, due_time, return_time, borrow_status, fine_amount FROM borrow_record WHERE reader_id = ${readerId.value} ORDER BY borrow_time;`),
    ])
    reader.value = readerResult.rows[0]; records.value = recordResult.rows; plan.value = recordResult
    if (!reader.value) errorMessage.value = '未找到该读者，请检查编号。'
  } catch (error) { errorMessage.value = apiErrorMessage(error) }
  finally { loading.value = false }
}
</script>

<style scoped>
.search-card { display: flex; justify-content: space-between; align-items: center; padding: 23px 26px; }.search-card > div:first-child { display: flex; flex-direction: column; }.search-card span { color: var(--cyan); font: 8px 'DM Mono'; letter-spacing: .12em; }.search-card strong { margin-top: 6px; font-size: 15px; }.search-card p { margin: 5px 0 0; color: #668096; font-size: 10px; }.search-form { display: flex; gap: 9px; width: 450px; }.borrow-error { margin-top: 13px; color: #e9949e; font-size: 10px; }.borrow-grid { display: grid; grid-template-columns: 270px minmax(0, 1fr); gap: 18px; }.reader-card { padding: 24px 20px; text-align: center; }.avatar { width: 54px; height: 54px; display: grid; place-items: center; margin: 0 auto 11px; color: var(--cyan); font-size: 20px; border-radius: 50%; border: 1px solid rgba(41,216,199,.3); background: rgba(41,216,199,.08); }.reader-card > strong { display: block; font-size: 14px; }.reader-card > span { display: block; color: #587087; font: 9px 'DM Mono'; margin-top: 4px; }.reader-card dl { margin: 22px 0 0; display: grid; grid-template-columns: 1fr 1.5fr; text-align: left; }.reader-card dt, .reader-card dd { margin: 0; padding: 8px 0; border-bottom: 1px solid rgba(151,179,207,.06); font-size: 9px; }.reader-card dt { color: #526b81; }.reader-card dd { color: #9aafc0; text-align: right; }.route-explain { padding: 22px; display: flex; justify-content: center; align-items: center; gap: 18px; color: #7992a7; font-size: 10px; }.route-explain i { color: #466175; }.route-explain strong { color: var(--cyan); font-weight: 500; }
@media (max-width: 760px) { .search-card { align-items: flex-start; flex-direction: column; gap: 18px; }.search-form { width: 100%; flex-direction: column; }.route-explain { flex-wrap: wrap; gap: 9px; } }
</style>
