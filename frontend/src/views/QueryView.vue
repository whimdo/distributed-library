<template>
  <div>
    <div class="page-intro">
      <div><h2>逻辑 SQL 工作台</h2><p>支持 SELECT 以及受控的单行 INSERT、主键 UPDATE 和主键 DELETE</p></div>
      <span class="security-note"><el-icon><Lock /></el-icon>参数化写入 · 权限与分片校验</span>
    </div>

    <div class="query-layout">
      <section class="panel editor-panel">
        <div class="panel-header">
          <div class="panel-title">SQL 编辑器</div>
          <div class="editor-tools"><button @click="sql = ''">清空</button><button @click="formatSql">格式化</button><span>Ctrl + Enter 执行</span></div>
        </div>
        <div class="panel-body">
          <SqlEditor v-model="sql" @execute="runQuery" />
          <div class="editor-footer">
            <el-select v-model="example" placeholder="载入示例" style="width: 180px" @change="loadExample">
              <el-option v-for="item in examples" :key="item.label" :label="item.label" :value="item.sql" />
            </el-select>
            <el-button type="primary" :loading="queryStore.running" @click="runQuery"><el-icon><VideoPlay /></el-icon>执行查询</el-button>
          </div>
        </div>
      </section>

      <section class="panel catalog-panel">
        <div class="panel-header"><div class="panel-title">逻辑表</div><span class="panel-subtitle">{{ schema.length }} TABLES</span></div>
        <div class="schema-list">
          <button v-for="table in schema" :key="table.logical_name" @click="selectTable(table.logical_name)">
            <span><el-icon><Grid /></el-icon>{{ table.logical_name }}</span>
            <small :class="table.location">{{ table.location === 'coordinator' ? 'GLOBAL' : 'SHARDED' }}</small>
          </button>
        </div>
      </section>
    </div>

    <section v-if="errorMessage" class="error-box section-gap"><el-icon><Warning /></el-icon><div><strong>查询未执行</strong><span>{{ errorMessage }}</span></div></section>

    <section class="panel section-gap">
      <div class="panel-header">
        <div class="panel-title">查询结果</div>
        <div v-if="queryStore.result" class="result-meta"><span>{{ queryStore.result.row_count }} ROWS</span><span>{{ duration }} MS</span><button @click="exportCsv">导出 CSV</button></div>
      </div>
      <div class="panel-body"><ResultTable :columns="queryStore.result?.columns || []" :rows="queryStore.result?.rows || []" /></div>
    </section>

    <section class="panel section-gap">
      <div class="panel-header"><div class="panel-title">查询分解与优化过程</div><span class="panel-subtitle">TRANSPARENT DISTRIBUTION</span></div>
      <div class="panel-body"><QueryPlan :result="queryStore.result" /></div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Grid, Lock, VideoPlay, Warning } from '@element-plus/icons-vue'
import SqlEditor from '@/components/SqlEditor.vue'
import ResultTable from '@/components/ResultTable.vue'
import QueryPlan from '@/components/QueryPlan.vue'
import { apiErrorMessage, getLogicalSchema } from '@/api/client'
import { useQueryStore } from '@/stores/query'
import type { LogicalTable } from '@/types'

const queryStore = useQueryStore()
const sql = ref("SELECT copy_id, book_id, owner_campus_id, copy_status\nFROM book_copy\nWHERE copy_status = 'AVAILABLE'\nORDER BY copy_id\nLIMIT 20;")
const example = ref('')
const schema = ref<LogicalTable[]>([])
const errorMessage = ref('')
const duration = ref(0)
const examples = [
  { label: '可借馆藏（广播）', sql: "SELECT copy_id, book_id, owner_campus_id, copy_status FROM book_copy WHERE copy_status = 'AVAILABLE' ORDER BY copy_id LIMIT 20;" },
  { label: '按校区定位图书馆', sql: 'SELECT library_id, library_name, campus_id, longitude, latitude FROM library WHERE campus_id = 1009;' },
  { label: '跨校借阅记录', sql: "SELECT borrow_id, reader_id, book_id, borrow_type, borrow_status FROM borrow_record WHERE borrow_type = 'CROSS_UNIVERSITY';" },
  { label: '书目与分类连接', sql: 'SELECT b.book_id, b.title, b.author, c.category_name FROM book b JOIN category c ON b.category_id = c.category_id ORDER BY b.book_id LIMIT 20;' },
  { label: '新增读者（示例）', sql: "INSERT INTO reader (home_university_id, home_campus_id, student_no, network_card_no, reader_name, phone, email, reader_type, network_permission, max_borrow_count, status) VALUES (102, 1004, 'SQL-DEMO-S001', 'SQL-DEMO-CARD-001', 'SQL演示学生', '13800000000', 'sql-demo@example.test', 'UNDERGRADUATE', TRUE, 10, 'ACTIVE');" },
  { label: '修改读者（主键路由）', sql: "UPDATE reader SET status = 'ACTIVE', max_borrow_count = 12 WHERE reader_id = 110000000001;" },
  { label: '删除读者（请先改 ID）', sql: 'DELETE FROM reader WHERE reader_id = 110000000000;' },
]

function loadExample(value: string) { sql.value = value }
function selectTable(name: string) { sql.value = `SELECT *\nFROM ${name}\nLIMIT 50;` }
function formatSql() { sql.value = sql.value.replace(/\s+(FROM|WHERE|ORDER BY|GROUP BY|LIMIT|JOIN|LEFT JOIN|RIGHT JOIN)\s+/gi, '\n$1 ') }

async function runQuery() {
  if (!sql.value.trim()) return ElMessage.warning('请输入 SQL 语句。')
  const operation = sql.value.trim().match(/^([a-z]+)/i)?.[1]?.toUpperCase()
  if (operation && operation !== 'SELECT') {
    try { await ElMessageBox.confirm(`即将执行 ${operation} 写操作，系统会修改实际数据库。`, '确认执行写操作', { type: 'warning', confirmButtonText: '确认执行' }) }
    catch { return }
  }
  errorMessage.value = ''
  const started = performance.now()
  try { await queryStore.run(sql.value); duration.value = Math.round(performance.now() - started); ElMessage.success(operation === 'SELECT' ? '查询执行完成' : '写操作执行完成') }
  catch (error) { errorMessage.value = apiErrorMessage(error) }
}

function exportCsv() {
  const result = queryStore.result
  if (!result?.rows.length) return ElMessage.warning('当前没有可导出的结果。')
  const escape = (value: unknown) => `"${String(value ?? '').replaceAll('"', '""')}"`
  const csv = [result.columns.join(','), ...result.rows.map((row) => result.columns.map((column) => escape(row[column])).join(','))].join('\n')
  const link = document.createElement('a')
  link.href = URL.createObjectURL(new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8' }))
  link.download = `query-${result.query_id.slice(0, 8)}.csv`
  link.click(); URL.revokeObjectURL(link.href)
}

onMounted(async () => { try { schema.value = await getLogicalSchema() } catch { /* backend status is shown on run */ } })
</script>

<style scoped>
.security-note { color: #668198; font-size: 10px; display: flex; gap: 6px; align-items: center; }
.query-layout { display: grid; grid-template-columns: minmax(0, 1fr) 230px; gap: 18px; }
.editor-tools { display: flex; align-items: center; gap: 13px; }
.editor-tools button { color: #6c849a; background: none; border: 0; cursor: pointer; font-size: 10px; }.editor-tools button:hover { color: var(--cyan); }
.editor-tools span { color: #3f5b72; font: 9px 'DM Mono'; padding-left: 8px; border-left: 1px solid var(--line); }
.editor-footer { display: flex; justify-content: space-between; margin-top: 14px; }
.catalog-panel { overflow: hidden; }
.schema-list { padding: 7px 9px 12px; max-height: 323px; overflow-y: auto; }
.schema-list button { width: 100%; padding: 9px 8px; display: flex; justify-content: space-between; align-items: center; color: #8399ad; background: transparent; border: 0; border-bottom: 1px solid rgba(151,179,207,.06); cursor: pointer; }
.schema-list button:hover { color: var(--cyan); background: rgba(41,216,199,.035); }
.schema-list button span { display: flex; align-items: center; gap: 7px; font: 10px 'DM Mono'; }
.schema-list small { padding: 2px 5px; font: 7px 'DM Mono'; border-radius: 3px; color: #66829a; background: rgba(87,151,255,.08); }.schema-list small.fragmented { color: #d2a04d; background: rgba(246,184,74,.08); }
.error-box { display: flex; gap: 12px; align-items: center; padding: 14px 17px; color: var(--red); background: rgba(255,110,125,.07); border: 1px solid rgba(255,110,125,.18); border-radius: 8px; }
.error-box div { display: flex; flex-direction: column; }.error-box strong { font-size: 11px; }.error-box span { margin-top: 3px; color: #bd7f88; font-size: 10px; }
.result-meta { display: flex; align-items: center; gap: 13px; color: #587187; font: 9px 'DM Mono'; }.result-meta button { color: var(--cyan); background: none; border: 0; cursor: pointer; }
</style>
