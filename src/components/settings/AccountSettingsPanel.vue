<!-- author: jf -->
<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

type ThemeMode = 'light' | 'dark'
type AuthMode = 'login' | 'register'

const props = defineProps<{
  themeMode: ThemeMode
}>()

const emit = defineEmits<{
  (e: 'set-theme', mode: ThemeMode): void
  (e: 'auth-success'): void
}>()

const authStore = useAuthStore()
const authMode = ref<AuthMode>('login')
const authError = ref('')
const authSuccess = ref('')
const form = reactive({
  email: '',
  password: '',
  nickname: '',
})

const themeOptions: Array<{ mode: ThemeMode; label: string }> = [
  { mode: 'light', label: '光明' },
  { mode: 'dark', label: '黑暗' },
]

const isLoggedIn = computed(() => authStore.isLoggedIn)
const currentUserLabel = computed(() => authStore.user?.nickname?.trim() || authStore.user?.email || '')

function selectTheme(mode: ThemeMode) {
  if (props.themeMode === mode) return
  emit('set-theme', mode)
}

function switchAuthMode(mode: AuthMode) {
  authMode.value = mode
  authError.value = ''
  authSuccess.value = ''
}

async function submitAuth() {
  authError.value = ''
  authSuccess.value = ''
  try {
    if (authMode.value === 'register') {
      await authStore.register({
        email: form.email,
        password: form.password,
        nickname: form.nickname || undefined,
      })
      authSuccess.value = '注册并登录成功'
      emit('auth-success')
    } else {
      await authStore.login({ email: form.email, password: form.password })
      authSuccess.value = '登录成功'
      emit('auth-success')
    }
  } catch (error) {
    authError.value = error instanceof Error ? error.message : '操作失败'
  }
}

async function handleLogout() {
  authError.value = ''
  authSuccess.value = ''
  try {
    await authStore.logout()
    authSuccess.value = '已退出登录'
  } catch (error) {
    authError.value = error instanceof Error ? error.message : '退出失败'
  }
}
</script>

<template>
  <main class="account-settings-panel" :class="{ dark: props.themeMode === 'dark' }">
    <div class="settings-stack">
      <section class="theme-setting-card" aria-labelledby="theme-setting-title">
        <div class="theme-setting-main">
          <span class="theme-setting-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M12 3v2m0 14v2M5 5l1.4 1.4M17.6 17.6 19 19M3 12h2m14 0h2M5 19l1.4-1.4M17.6 6.4 19 5" />
              <circle cx="12" cy="12" r="4" />
            </svg>
          </span>
          <div class="theme-setting-copy">
            <h2 id="theme-setting-title">主题模式</h2>
            <span>{{ props.themeMode === 'dark' ? '当前黑暗' : '当前光明' }}</span>
          </div>
        </div>

        <div class="theme-toggle-group" role="radiogroup" aria-label="主题模式">
          <button
            v-for="option in themeOptions"
            :key="option.mode"
            class="theme-toggle-option"
            :class="{ active: props.themeMode === option.mode }"
            type="button"
            role="radio"
            :aria-checked="props.themeMode === option.mode"
            @click="selectTheme(option.mode)"
          >
            {{ option.label }}
          </button>
        </div>
      </section>

      <section class="auth-card" aria-labelledby="auth-card-title">
        <div class="auth-card-head">
          <div>
            <h2 id="auth-card-title">账户</h2>
            <p v-if="isLoggedIn">当前已登录：{{ currentUserLabel }}</p>
            <p v-else>请先注册或登录，登录后才能进入系统并隔离简历、面试与知识库数据</p>
          </div>
          <button v-if="isLoggedIn" class="ghost-button" type="button" :disabled="authStore.loading" @click="handleLogout">
            退出登录
          </button>
        </div>

        <template v-if="!isLoggedIn">
          <div class="auth-tabs" role="tablist" aria-label="账户操作切换">
            <button class="auth-tab" :class="{ active: authMode === 'login' }" type="button" @click="switchAuthMode('login')">登录</button>
            <button class="auth-tab" :class="{ active: authMode === 'register' }" type="button" @click="switchAuthMode('register')">注册</button>
          </div>

          <form class="auth-form" @submit.prevent="submitAuth">
            <label>
              <span>邮箱</span>
              <input v-model.trim="form.email" type="email" autocomplete="email" placeholder="you@example.com" required />
            </label>
            <label>
              <span>密码</span>
              <input v-model="form.password" type="password" autocomplete="current-password" minlength="8" placeholder="至少 8 位" required />
            </label>
            <label v-if="authMode === 'register'">
              <span>昵称</span>
              <input v-model.trim="form.nickname" type="text" maxlength="100" placeholder="可选" />
            </label>
            <button class="primary-button" type="submit" :disabled="authStore.loading">
              {{ authStore.loading ? '处理中...' : authMode === 'register' ? '注册并登录' : '登录' }}
            </button>
          </form>
        </template>

        <p v-if="authError" class="auth-error">{{ authError }}</p>
        <p v-if="authSuccess" class="auth-success">{{ authSuccess }}</p>
      </section>
    </div>
  </main>
</template>

<style scoped>
.account-settings-panel {
  --config-bg: #f7f2ec;
  --config-surface: rgba(255, 252, 248, 0.94);
  --config-surface-soft: #fff7ef;
  --config-border: rgba(122, 91, 68, 0.14);
  --config-text: #2d2521;
  --config-muted: #7b6a5b;
  --config-accent: #d97745;
  --config-accent-strong: #2d2521;
  --config-shadow: 0 24px 48px rgba(45, 37, 33, 0.1);
  --config-danger: #b42318;
  --config-success: #117a37;
  flex: 1;
  min-width: 0;
  height: 100%;
  overflow: auto;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 32px;
  background: radial-gradient(circle at 18% 10%, rgba(217, 119, 69, 0.12), transparent 28%), linear-gradient(135deg, var(--config-bg) 0%, #efe4d8 100%);
  color: var(--config-text);
}
.account-settings-panel.dark {
  --config-bg: #100f0d;
  --config-surface: rgba(24, 20, 16, 0.96);
  --config-surface-soft: #201912;
  --config-border: rgba(255, 208, 168, 0.14);
  --config-text: #f7efe5;
  --config-muted: #c8b7a5;
  --config-accent: #f08a45;
  --config-accent-strong: #ffd0a8;
  --config-shadow: 0 28px 58px rgba(0, 0, 0, 0.38);
  --config-danger: #ff8a80;
  --config-success: #63d297;
  background: radial-gradient(circle at 18% 10%, rgba(240, 138, 69, 0.12), transparent 28%), linear-gradient(135deg, #100f0d 0%, #18120d 100%);
}
.settings-stack { width: min(720px, 100%); display: flex; flex-direction: column; gap: 18px; }
.theme-setting-card, .auth-card {
  padding: 18px;
  border: 1px solid var(--config-border);
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.52), transparent), var(--config-surface);
  box-shadow: var(--config-shadow);
}
.theme-setting-main, .auth-card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.theme-setting-main { justify-content: flex-start; }
.theme-setting-icon {
  width: 40px; height: 40px; border-radius: 14px; background: var(--config-accent-strong); color: #fff; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.account-settings-panel.dark .theme-setting-icon { color: #15100c; }
.theme-setting-icon svg { width: 20px; height: 20px; }
.theme-setting-icon path, .theme-setting-icon circle { stroke: currentColor; stroke-width: 1.9; stroke-linecap: round; stroke-linejoin: round; }
.theme-setting-copy { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.theme-setting-copy h2, .auth-card-head h2 { margin: 0; color: var(--config-text); font-size: 16px; font-weight: 900; line-height: 1.25; }
.theme-setting-copy span, .auth-card-head p { color: var(--config-muted); font-size: 12px; font-weight: 800; line-height: 1.25; margin: 0; }
.theme-toggle-group, .auth-tabs { padding: 4px; border-radius: 999px; background: var(--config-surface-soft); border: 1px solid var(--config-border); display: inline-flex; gap: 4px; }
.theme-toggle-option, .auth-tab, .ghost-button, .primary-button {
  border: 0; border-radius: 999px; font-size: 13px; font-weight: 900; cursor: pointer; transition: background-color .18s ease, color .18s ease, box-shadow .18s ease;
}
.theme-toggle-option, .auth-tab { min-width: 64px; height: 34px; background: transparent; color: var(--config-muted); }
.theme-toggle-option.active, .auth-tab.active { background: var(--config-accent); color: #15100c; box-shadow: 0 8px 18px rgba(217,119,69,.18); }
.auth-card { display: flex; flex-direction: column; gap: 14px; }
.auth-form { display: flex; flex-direction: column; gap: 12px; }
.auth-form label { display: flex; flex-direction: column; gap: 6px; color: var(--config-muted); font-size: 12px; font-weight: 800; }
.auth-form input {
  height: 42px; border-radius: 12px; border: 1px solid var(--config-border); background: rgba(255,255,255,.7); padding: 0 12px; font-size: 14px; color: var(--config-text);
}
.account-settings-panel.dark .auth-form input { background: rgba(255,255,255,.04); }
.primary-button { height: 42px; background: var(--config-accent-strong); color: #fff; }
.account-settings-panel.dark .primary-button { color: #15100c; }
.ghost-button { min-width: 92px; height: 36px; background: var(--config-surface-soft); color: var(--config-text); border: 1px solid var(--config-border); }
.auth-error, .auth-success { margin: 0; font-size: 13px; font-weight: 800; }
.auth-error { color: var(--config-danger); }
.auth-success { color: var(--config-success); }
@media (max-width: 760px) {
  .account-settings-panel { padding: 8px; }
  .theme-setting-card, .auth-card { padding: 12px; border-radius: 16px; }
  .auth-card-head { align-items: flex-start; flex-direction: column; }
  .theme-setting-main { gap: 8px; }
  .theme-setting-icon { width: 30px; height: 30px; border-radius: 10px; }
}
</style>
