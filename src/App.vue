<!-- author: jf -->
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useResumeStore } from '@/stores/resume'
import KnowledgeBasePanel from '@/components/ai/knowledge/KnowledgeBasePanel.vue'
import AiInterviewerPanel from '@/components/ai/interview/AiInterviewerPanel.vue'
import ModuleSidebar from '@/components/common/ModuleSidebar.vue'
import EditorPanel from '@/components/resume/EditorPanel.vue'
import PreviewPanel from '@/components/resume/PreviewPanel.vue'
import AccountSettingsPanel from '@/components/settings/AccountSettingsPanel.vue'
import {
  DEFAULT_PRIMARY_MENU_KEY,
  isPrimaryMenuRoutePath,
  normalizePrimaryRoutePath,
  resolvePrimaryMenuFromPath,
  resolvePrimaryMenuPath,
  type PrimaryMenuKey,
} from '@/router/menuRoutes'

const authStore = useAuthStore()
const resumeStore = useResumeStore()
const sidebarCollapsed = ref(false)
type ResumeMobilePane = 'editor' | 'preview'
const activeMenu = ref<PrimaryMenuKey>(
  typeof window === 'undefined' ? DEFAULT_PRIMARY_MENU_KEY : resolvePrimaryMenuFromPath(window.location.pathname)
)
const activeResumePane = ref<ResumeMobilePane>('editor')
const currentUserLabel = computed(() => authStore.user?.nickname?.trim() || authStore.user?.email || '')
type ThemeMode = 'light' | 'dark'
const THEME_STORAGE_KEY = 'resume-builder-theme'
const themeMode = ref<ThemeMode>(resolveInitialThemeMode())

function resolveInitialThemeMode(): ThemeMode {
  if (typeof window === 'undefined') return 'light'
  let storedMode: string | null = null
  try {
    storedMode = window.localStorage.getItem(THEME_STORAGE_KEY)
  } catch {
    storedMode = null
  }
  return storedMode === 'dark' ? 'dark' : 'light'
}

function applyThemeMode(mode: ThemeMode) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  root.dataset.theme = mode
  root.classList.toggle('dark', mode === 'dark')
  root.style.colorScheme = mode
}

function persistThemeMode(mode: ThemeMode) {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, mode)
  } catch {
    // ignore
  }
}

function setThemeMode(mode: ThemeMode) {
  themeMode.value = mode
  applyThemeMode(mode)
  persistThemeMode(mode)
}

applyThemeMode(themeMode.value)

function setActiveMenu(key: PrimaryMenuKey) {
  activeMenu.value = key
  if (key === 'resume-editor') activeResumePane.value = 'editor'
}

function syncMenuFromLocation() {
  if (typeof window === 'undefined') return
  const key = resolvePrimaryMenuFromPath(window.location.pathname)
  const targetPath = resolvePrimaryMenuPath(key)
  const currentPath = normalizePrimaryRoutePath(window.location.pathname)
  setActiveMenu(key)
  if (!isPrimaryMenuRoutePath(window.location.pathname) || currentPath !== targetPath) {
    window.history.replaceState({ primaryMenu: key }, '', targetPath)
  }
}

function handleSelectMenu(key: PrimaryMenuKey) {
  if (!authStore.isLoggedIn) return
  setActiveMenu(key)
  if (typeof window === 'undefined') return
  const targetPath = resolvePrimaryMenuPath(key)
  if (normalizePrimaryRoutePath(window.location.pathname) !== targetPath) {
    window.history.pushState({ primaryMenu: key }, '', targetPath)
  }
}

onMounted(() => {
  authStore.fetchMe().then((user) => {
    resumeStore.updateStorageKey(user?.id ?? null)
    if (user) {
      resumeStore.loadFromCloud().catch(() => undefined)
    } else {
      resumeStore.updateStorageKey(null)
    }
  }).catch(() => undefined)
  syncMenuFromLocation()
  window.addEventListener('popstate', syncMenuFromLocation)
})

onUnmounted(() => {
  window.removeEventListener('popstate', syncMenuFromLocation)
})
</script>

<template>
  <div v-if="!authStore.initialized" class="auth-gate-shell" :class="{ dark: themeMode === 'dark' }">
    <div class="auth-gate-card auth-gate-card--loading">
      <h1>正在检查登录状态…</h1>
      <p>请稍候，马上带你进入系统。</p>
    </div>
  </div>

  <div v-else-if="!authStore.isLoggedIn" class="auth-gate-shell" :class="{ dark: themeMode === 'dark' }">
    <div class="auth-gate-card">
      <div class="auth-gate-brand">
        <img src="/favicon.svg?v=orange-black" alt="Resume Builder" class="auth-gate-logo" />
        <div>
          <h1>先注册或登录，再进入系统</h1>
          <p>为保证简历、面试记录和知识库数据隔离，当前系统仅对已登录用户开放。</p>
        </div>
      </div>
      <AccountSettingsPanel :theme-mode="themeMode" @set-theme="setThemeMode" />
    </div>
  </div>

  <div v-else class="app-layout">
    <ModuleSidebar
      :collapsed="sidebarCollapsed"
      :active-menu="activeMenu"
      :logged-in="authStore.isLoggedIn"
      :user-label="currentUserLabel"
      @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
      @select-menu="handleSelectMenu"
    />
    <div class="main-content">
      <template v-if="activeMenu === 'resume-editor'">
        <div class="mobile-resume-tabs" role="tablist" aria-label="简历移动端视图切换">
          <button class="mobile-resume-tab" :class="{ active: activeResumePane === 'editor' }" type="button" role="tab" :aria-selected="activeResumePane === 'editor'" @click="activeResumePane = 'editor'">编辑</button>
          <button class="mobile-resume-tab" :class="{ active: activeResumePane === 'preview' }" type="button" role="tab" :aria-selected="activeResumePane === 'preview'" @click="activeResumePane = 'preview'">预览</button>
        </div>
        <EditorPanel class="resume-workspace-pane" :class="{ 'mobile-pane-hidden': activeResumePane !== 'editor' }" />
        <PreviewPanel class="resume-workspace-pane" :class="{ 'mobile-pane-hidden': activeResumePane !== 'preview' }" />
      </template>
      <AiInterviewerPanel v-else-if="activeMenu === 'ai-interviewer'" />
      <KnowledgeBasePanel v-else-if="activeMenu === 'knowledge-base'" />
      <AccountSettingsPanel v-else :theme-mode="themeMode" @set-theme="setThemeMode" />
    </div>
  </div>
</template>

<style scoped>
.auth-gate-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: radial-gradient(circle at 18% 10%, rgba(217, 119, 69, 0.12), transparent 28%), linear-gradient(135deg, #f7f2ec 0%, #efe4d8 100%);
}
.auth-gate-shell.dark {
  background: radial-gradient(circle at 18% 10%, rgba(240, 138, 69, 0.12), transparent 28%), linear-gradient(135deg, #100f0d 0%, #18120d 100%);
}
.auth-gate-card {
  width: min(960px, 100%);
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.auth-gate-card--loading {
  width: min(520px, 100%);
  padding: 28px;
  border-radius: 24px;
  background: rgba(255,255,255,.9);
  border: 1px solid rgba(122, 91, 68, 0.14);
  box-shadow: 0 24px 48px rgba(45, 37, 33, 0.1);
}
.auth-gate-brand {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 22px;
  border-radius: 24px;
  background: rgba(255,255,255,.86);
  border: 1px solid rgba(122, 91, 68, 0.14);
  box-shadow: 0 24px 48px rgba(45, 37, 33, 0.08);
}
.auth-gate-logo {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  flex-shrink: 0;
}
.auth-gate-brand h1 {
  margin: 0 0 4px;
  font-size: 24px;
  color: #2d2521;
}
.auth-gate-brand p {
  margin: 0;
  color: #7b6a5b;
  font-size: 14px;
  line-height: 1.6;
}
.app-layout { display: flex; height: 100vh; min-height: 100vh; overflow: hidden; }
.main-content { flex: 1; display: flex; overflow: hidden; min-width: 0; }
.mobile-resume-tabs { display: none; }
@supports (height: 100dvh) {
  .app-layout { height: 100dvh; min-height: 100dvh; }
}
@media (max-width: 760px) {
  .app-layout { height: 100dvh; min-height: 100dvh; padding-bottom: calc(68px + env(safe-area-inset-bottom)); background: var(--bg-app); }
  .main-content { position: relative; flex-direction: column; height: 100%; min-height: 0; overflow: hidden; }
  .mobile-resume-tabs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 5px; padding: 7px 8px 6px; background: rgba(247, 242, 236, 0.96); border-bottom: 1px solid #e4d8cb; flex-shrink: 0; z-index: 4; }
  .mobile-resume-tab { min-height: 34px; border: 1px solid #dfd2c2; border-radius: 12px; background: #fff; color: #7b6a5b; font-size: 12px; font-weight: 800; }
  .mobile-resume-tab.active { border-color: #2d2521; background: #2d2521; color: #fff; box-shadow: 0 10px 20px rgba(45, 37, 33, 0.12); }
  .resume-workspace-pane { flex: 1 1 auto; min-height: 0; width: 100%; }
  .mobile-pane-hidden { display: none !important; }
  .auth-gate-shell { padding: 12px; }
  .auth-gate-brand { padding: 16px; border-radius: 18px; align-items: flex-start; }
  .auth-gate-brand h1 { font-size: 20px; }
}
</style>
