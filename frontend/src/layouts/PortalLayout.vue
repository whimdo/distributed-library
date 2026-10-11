<template>
  <div class="portal-shell">
    <header class="portal-header">
      <RouterLink to="/portal" class="portal-brand"><span>蓉</span><div><strong>蓉图云</strong><small>高校图书共享服务</small></div></RouterLink>
      <nav><RouterLink to="/portal">图书检索</RouterLink><RouterLink to="/portal/map">附近图书馆</RouterLink><RouterLink to="/portal/borrowings">我的借阅</RouterLink></nav>
      <div class="portal-user"><div><strong>{{ auth.user?.display_name }}</strong><span>学生用户 · Site {{ auth.user?.home_site_id }}</span></div><button @click="logout">退出</button></div>
    </header>
    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore(), router = useRouter()
function logout(){ auth.logout(); router.replace('/login') }
</script>

<style scoped>
.portal-shell { min-height:100vh; color:#183047; background:#f3f7f8; }
.portal-header { height:74px; display:flex; align-items:center; padding:0 5vw; background:#fff; border-bottom:1px solid #dfe9eb; position:sticky; top:0; z-index:20; }.portal-brand { display:flex; align-items:center; gap:11px; margin-right:7vw; }.portal-brand > span { width:34px;height:34px;display:grid;place-items:center;border-radius:10px;background:#087f76;color:#fff;font-weight:700; }.portal-brand div,.portal-user div { display:flex;flex-direction:column; }.portal-brand strong{letter-spacing:.12em}.portal-brand small{font-size:8px;color:#819498;margin-top:2px}.portal-header nav{display:flex;gap:30px;height:100%;align-items:center}.portal-header nav a{height:100%;display:flex;align-items:center;color:#637a83;font-size:13px;border-bottom:2px solid transparent}.portal-header nav a.router-link-exact-active{color:#087f76;border-color:#0ca79a}.portal-user{margin-left:auto;display:flex;align-items:center;gap:17px;text-align:right}.portal-user strong{font-size:11px}.portal-user span{font-size:8px;color:#8b9da3;margin-top:2px}.portal-user button{border:1px solid #dbe6e8;background:#fff;color:#71858c;border-radius:5px;padding:6px 10px;font-size:9px;cursor:pointer}
@media(max-width:760px){.portal-header{padding:0 14px}.portal-brand div,.portal-user div{display:none}.portal-header nav{gap:14px}.portal-header nav a{font-size:10px}.portal-user{margin-left:auto}.portal-brand{margin-right:15px}}
</style>
