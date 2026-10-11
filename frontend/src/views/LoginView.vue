<template>
  <main class="login-page">
    <section class="login-story">
      <div class="login-brand"><span>蓉</span><div><strong>蓉图云</strong><small>DISTRIBUTED LIBRARY NETWORK</small></div></div>
      <div class="story-copy"><span>CHENGDU · UNIVERSITY LIBRARIES</span><h1>让每一所高校的知识<br>在城市中自由流动</h1><p>统一检索、跨校借阅与空间服务，由三个数据站点协同完成。</p></div>
      <div class="network"><i></i><span>1 个协调节点</span><b></b><span>3 个数据站点</span><b></b><span>9 个高校校区</span></div>
    </section>
    <section class="login-panel">
      <div class="login-box">
        <header><span>SECURE ACCESS</span><h2>登录系统</h2><p>不同身份将进入对应的数据管理范围</p></header>
        <el-form @submit.prevent="submit">
          <label>账号／学号</label><el-input v-model="form.username" size="large" placeholder="学生请输入学号" autocomplete="username" />
          <label>密码</label><el-input v-model="form.password" size="large" type="password" show-password placeholder="请输入密码" autocomplete="current-password" @keyup.enter="submit" />
          <div v-if="error" class="login-error">{{ error }}</div>
          <el-button type="primary" size="large" native-type="submit" :loading="loading">登录并进入系统</el-button>
        </el-form>
        <div class="demo-title">演示身份快速填充</div>
        <div class="demo-users">
          <button @click="fill('UESTC-S001','student123')"><strong>学生</strong><span>UESTC-S001</span></button>
          <button @click="fill('site1_admin','site123')"><strong>站点管理员</strong><span>site1_admin</span></button>
          <button @click="fill('admin','admin123')"><strong>全局管理员</strong><span>admin</span></button>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiErrorMessage } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
const router = useRouter(), auth = useAuthStore()
const form = reactive({ username: '', password: '' }), loading = ref(false), error = ref('')
function fill(username: string, password: string) { form.username = username; form.password = password; error.value = '' }
async function submit() {
  if (!form.username || !form.password) { error.value = '请输入账号和密码。'; return }
  loading.value = true; error.value = ''
  try { const user = await auth.login(form.username, form.password); await router.replace(user.role === 'STUDENT' ? '/portal' : '/admin') }
  catch (reason) { error.value = apiErrorMessage(reason) }
  finally { loading.value = false }
}
</script>

<style scoped>
.login-page { min-height: 100vh; display: grid; grid-template-columns: 1.2fr .8fr; background: #07111f; }
.login-story { position: relative; display: flex; flex-direction: column; justify-content: space-between; padding: 45px 7vw; overflow: hidden; background: radial-gradient(circle at 78% 35%, rgba(41,216,199,.16), transparent 30%), linear-gradient(145deg,#071827,#092239); }
.login-story::after { content:''; position:absolute; width:520px; height:520px; right:-170px; top:17%; border:1px solid rgba(41,216,199,.13); border-radius:50%; box-shadow:0 0 0 70px rgba(41,216,199,.025),0 0 0 150px rgba(41,216,199,.018); }
.login-brand { display:flex; gap:14px; align-items:center; position:relative; z-index:1; }.login-brand > span { width:43px; height:43px; display:grid; place-items:center; transform:rotate(45deg); border:1px solid var(--cyan); border-radius:11px; color:var(--cyan); font-weight:700; }.login-brand > span::first-letter { transform:rotate(-45deg); }.login-brand div { display:flex; flex-direction:column; }.login-brand strong { font-size:20px; letter-spacing:.13em; }.login-brand small { color:#537187; font:8px 'DM Mono'; letter-spacing:.12em; margin-top:3px; }
.story-copy { position:relative; z-index:1; }.story-copy > span { color:var(--cyan); font:9px 'DM Mono'; letter-spacing:.18em; }.story-copy h1 { font-size:36px; line-height:1.45; letter-spacing:.04em; margin:18px 0; }.story-copy p { color:#7791a7; font-size:13px; }.network { display:flex; align-items:center; gap:13px; color:#7890a5; font-size:10px; position:relative; z-index:1; }.network i { width:7px; height:7px; border-radius:50%; background:var(--cyan); box-shadow:0 0 10px var(--cyan); }.network b { width:32px; height:1px; background:#294459; }
.login-panel { display:grid; place-items:center; padding:35px; background:#091421; }.login-box { width:min(390px,100%); }.login-box header span { color:var(--cyan); font:9px 'DM Mono'; letter-spacing:.15em; }.login-box h2 { margin:8px 0 5px; font-size:27px; }.login-box header p { color:#668096; font-size:11px; margin:0 0 30px; }.login-box label { display:block; color:#8299ad; font-size:10px; margin:15px 0 7px; }.login-box :deep(.el-button) { width:100%; margin-top:22px; }.login-error { color:#ff8996; font-size:10px; margin-top:12px; }.demo-title { color:#4e687e; font-size:9px; margin:30px 0 10px; border-top:1px solid var(--line); padding-top:18px; }.demo-users { display:grid; grid-template-columns:repeat(3,1fr); gap:7px; }.demo-users button { padding:10px 7px; text-align:left; border:1px solid var(--line); border-radius:6px; background:#0c1c2c; color:#8da2b4; cursor:pointer; }.demo-users button:hover { border-color:rgba(41,216,199,.32); }.demo-users strong,.demo-users span { display:block; font-size:9px; }.demo-users span { color:#4e6a80; font:8px 'DM Mono'; margin-top:4px; }
@media(max-width:760px){.login-page{grid-template-columns:1fr}.login-story{display:none}.login-panel{min-height:100vh;padding:24px}}
</style>
