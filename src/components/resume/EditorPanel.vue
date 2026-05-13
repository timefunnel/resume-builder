<script setup lang="ts">
// author: jf
import { computed, onMounted, onUnmounted, reactive, ref, watch, type Component } from 'vue'
import { useResumeStore } from '@/stores/resume'
import { useAuthStore } from '@/stores/auth'
import BasicInfoEditor from './editors/BasicInfoEditor.vue'
import EducationEditor from './editors/EducationEditor.vue'
import SkillsEditor from './editors/SkillsEditor.vue'
import WorkExperienceEditor from './editors/WorkExperienceEditor.vue'
import ProjectExperienceEditor from './editors/ProjectExperienceEditor.vue'
import AwardsEditor from './editors/AwardsEditor.vue'
import SelfIntroEditor from './editors/SelfIntroEditor.vue'
import AiOptimizePanel from '@/components/ai/AiOptimizePanel.vue'
import { importResumeWithAi } from '@/api/resumeImportApi'
import { getModuleIconPaths, MODULE_ICON_VIEWBOX } from '@/constants/moduleIcons'

const store = useResumeStore()
const authStore = useAuthStore()
const showSaved = ref(false)
const searchValue = ref('')
const showAiPanel = ref(false)
const moduleMenuOpen = ref(false)
const moduleMenuRef = ref<HTMLElement | null>(null)
const jsonImportInputRef = ref<HTMLInputElement | null>(null)
const draggingModuleKey = ref<string | null>(null)
const dragOverModuleKey = ref<string | null>(null)
const nowTick = ref(Date.now())
const resumeTitleDraft = ref('')
const resumeTitleInputRef = ref<HTMLInputElement | null>(null)
const isEditingResumeTitle = ref(false)
const titleDirty = ref(false)
const aiImportInputRef = ref<HTMLInputElement | null>(null)
const aiImporting = ref(false)
const newResumeNameDraft = ref('')
const aiImportStageText = ref('')
const aiImportError = ref('')
const aiImportSuccess = ref('')
const aiImportedDraft = ref<{ title: string; content: Record<string, unknown>; extractedText: string } | null>(null)

function handleAiClick() {
  showAiPanel.value = true
}

function toggleModuleMenu() {
  moduleMenuOpen.value = !moduleMenuOpen.value
}

function handleDocumentPointerDown(event: MouseEvent) {
  const target = event.target as Node | null
  if (!target || !moduleMenuRef.value) return
  if (!moduleMenuRef.value.contains(target)) {
    moduleMenuOpen.value = false
  }
}

const expanded = reactive<Record<string, boolean>>({
  basicInfo: true,
  education: false,
  skills: false,
  workExperience: false,
  projectExperience: false,
  awards: false,
  selfIntro: false,
})

const editorMap: Record<string, Component> = {
  basicInfo: BasicInfoEditor,
  education: EducationEditor,
  skills: SkillsEditor,
  workExperience: WorkExperienceEditor,
  projectExperience: ProjectExperienceEditor,
  awards: AwardsEditor,
  selfIntro: SelfIntroEditor,
}

const visibleCount = computed(() => store.modules.filter((m) => m.visible).length)
const searchKeyword = computed(() => searchValue.value.trim())
const filteredModules = computed(() =>
  store.modules.filter((m) => (searchKeyword.value ? m.label.includes(searchKeyword.value) : true))
)

function hasTextContent(value: string | undefined): boolean {
  if (!value) return false
  const text = value
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/gi, ' ')
    .trim()
  return text.length > 0
}

function countFilled(values: Array<string | undefined>): number {
  return values.reduce((count, value) => count + (value?.trim() ? 1 : 0), 0)
}

function scoreByFilled(values: Array<string | undefined>): number {
  if (values.length === 0) return 0
  return countFilled(values) / values.length
}

const moduleCompletion = computed<Record<string, number>>(() => {
  const basic = store.basicInfo

  const basicInfoScore = scoreByFilled([
    basic.name,
    basic.phone,
    basic.email,
    basic.jobTitle,
    basic.expectedLocation,
    basic.educationLevel,
  ])

  const firstEducation = store.educationList.find((e) =>
    [e.school, e.major, e.degree, e.startDate].some((value) => value?.trim())
  )
  const educationScore = firstEducation
    ? scoreByFilled([firstEducation.school, firstEducation.major, firstEducation.degree, firstEducation.startDate])
    : 0

  const firstWork = store.workList.find((w) =>
    [w.company, w.position, w.startDate, w.description].some((value) => value?.trim())
  )
  const workScore = firstWork
    ? scoreByFilled([firstWork.company, firstWork.position, firstWork.startDate, firstWork.description])
    : 0

  const firstProject = store.projectList.find((p) =>
    [p.name, p.role, p.startDate, p.mainWork].some((value) => value?.trim())
  )
  const projectScore = firstProject
    ? scoreByFilled([firstProject.name, firstProject.role, firstProject.startDate, firstProject.mainWork])
    : 0

  const firstAward = store.awardList.find((a) => [a.name, a.date].some((value) => value?.trim()))
  const awardsScore = firstAward ? scoreByFilled([firstAward.name, firstAward.date]) : 0

  return {
    basicInfo: basicInfoScore,
    education: educationScore,
    skills: hasTextContent(store.skills) ? 1 : 0,
    workExperience: workScore,
    projectExperience: projectScore,
    awards: awardsScore,
    selfIntro: hasTextContent(store.selfIntro) ? 1 : 0,
  }
})


const aiImportSummary = computed(() => {
  if (!aiImportedDraft.value) return null
  const content = aiImportedDraft.value.content as Record<string, any>
  const basicInfo = (content.basicInfo || {}) as Record<string, any>
  return {
    name: String(basicInfo.name || '').trim(),
    phone: String(basicInfo.phone || '').trim(),
    email: String(basicInfo.email || '').trim(),
    jobTitle: String(basicInfo.jobTitle || '').trim(),
    educationCount: Array.isArray(content.educationList) ? content.educationList.length : 0,
    workCount: Array.isArray(content.workList) ? content.workList.length : 0,
    projectCount: Array.isArray(content.projectList) ? content.projectList.length : 0,
    skills: String(content.skills || '').trim(),
    extractedTextPreview: String(aiImportedDraft.value.extractedText || '').trim().slice(0, 500),
  }
})

const completionPercent = computed(() => {
  const enabledModules = store.modules.filter((m) => m.visible)
  if (enabledModules.length === 0) return 0
  const total = enabledModules.reduce((sum, mod) => sum + (moduleCompletion.value[mod.key] ?? 0), 0)
  return Math.round((total / enabledModules.length) * 100)
})

async function handleSave() {
  store.saveToStorage()
  if (authStore.isLoggedIn) {
    try {
      await store.saveToCloud(resumeTitleDraft.value || store.currentResumeTitle)
      await store.fetchResumeList().catch(() => undefined)
    } catch (error) {
      console.warn('Failed to save resume to cloud', error)
    }
  }
  showSaved.value = true
  setTimeout(() => {
    showSaved.value = false
  }, 1800)
}


async function handleSwitchResumeById(id: number) {
  if (!Number.isFinite(id) || id <= 0) return
  try {
    await store.loadResumeById(id)
    resumeTitleDraft.value = store.currentResumeTitle
  } catch (error) {
    console.warn('Failed to switch resume', error)
  }
}

async function handleSwitchResume(event: Event) {
  const target = event.target as HTMLSelectElement
  const id = Number(target.value)
  if (!Number.isFinite(id) || id <= 0) return
  try {
    await store.loadResumeById(id)
    resumeTitleDraft.value = store.currentResumeTitle
  } catch (error) {
    console.warn('Failed to switch resume', error)
  }
}

async function handleCreateResume() {
  const requestedTitle = (newResumeNameDraft.value || '').trim() || '新的简历'
  try {
    const created = await store.createNewResume(requestedTitle)
    resumeTitleDraft.value = created?.title || '新的简历'
    titleDirty.value = false
    isEditingResumeTitle.value = false
    newResumeNameDraft.value = ''
    requestAnimationFrame(() => resumeTitleInputRef.value?.focus())
  } catch (error) {
    console.warn('Failed to create resume', error)
  }
}


function startRenameResume() {
  if (!hasCloudResume.value || store.operationState !== 'idle') return
  resumeTitleDraft.value = store.currentResumeTitle || ''
  isEditingResumeTitle.value = true
  titleDirty.value = false
  requestAnimationFrame(() => resumeTitleInputRef.value?.focus())
}

function cancelRenameResume() {
  resumeTitleDraft.value = store.currentResumeTitle || ''
  titleDirty.value = false
  isEditingResumeTitle.value = false
}

async function handleRenameResume(itemId?: number) {
  const targetId = itemId || store.cloudResumeId
  const nextTitle = resumeTitleDraft.value.trim()
  if (!targetId || !nextTitle || !titleDirty.value) return
  try {
    await store.renameResumeById(targetId, nextTitle)
    titleDirty.value = false
    isEditingResumeTitle.value = false
  } catch (error) {
    console.warn('Failed to rename resume', error)
  }
}

async function handleDeleteResume() {
  if (!hasCloudResume.value) return
  const confirmed = window.confirm(`确定删除简历《${resumeTitleDraft.value || store.currentResumeTitle}》吗？此操作不可撤销。`)
  if (!confirmed) return
  try {
    await store.deleteCurrentResume()
    resumeTitleDraft.value = store.currentResumeTitle
    titleDirty.value = false
    isEditingResumeTitle.value = false
  } catch (error) {
    console.warn('Failed to delete resume', error)
  }
}


function triggerAiImport() {
  if (aiImporting.value) return
  aiImportError.value = ''
  aiImportSuccess.value = ''
  aiImportInputRef.value?.click()
}

async function handleAiImport(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  input.value = ''
  aiImporting.value = true
  aiImportStageText.value = '正在上传并解析简历…'
  aiImportError.value = ''
  aiImportSuccess.value = ''
  try {
    aiImportStageText.value = '正在调用 AI 结构化简历…'
    const response = await importResumeWithAi(file)
    const payload = await response.json().catch(() => null)
    if (!response.ok) {
      throw new Error(String(payload?.detail || `AI 导入失败 (${response.status})`))
    }
    if (payload?.content) {
      aiImportedDraft.value = {
        title: typeof payload.title === 'string' && payload.title.trim() ? payload.title.trim() : '导入的简历',
        content: payload.content,
        extractedText: typeof payload.extractedText === 'string' ? payload.extractedText : '',
      }
      aiImportStageText.value = ''
      aiImportSuccess.value = 'AI 已完成简历解析，请先预览结果再决定如何导入。'
    }
  } catch (error) {
    aiImportStageText.value = ''
    aiImportError.value = error instanceof Error ? error.message : 'AI 导入失败'
    console.warn('Failed to import resume with AI', error)
  } finally {
    aiImporting.value = false
    if (!aiImportedDraft.value) aiImportStageText.value = ''
  }
}


function applyImportedDraftToCurrent() {
  if (!aiImportedDraft.value) return
  store.importResumeData(JSON.stringify(aiImportedDraft.value.content))
  resumeTitleDraft.value = aiImportedDraft.value.title
  aiImportedDraft.value = null
  aiImportSuccess.value = '导入结果已应用到当前简历。'
}

async function saveImportedDraftAsNewResume() {
  if (!aiImportedDraft.value) return
  try {
    const created = await store.createNewResume(aiImportedDraft.value.title || '导入的简历')
    store.importResumeData(JSON.stringify(aiImportedDraft.value.content))
    resumeTitleDraft.value = aiImportedDraft.value.title || created?.title || '导入的简历'
    await store.saveToCloud(resumeTitleDraft.value)
    aiImportedDraft.value = null
    aiImportSuccess.value = 'AI 导入结果已另存为一份新简历。'
  } catch (error) {
    console.warn('Failed to save imported draft as new resume', error)
  }
}

function dismissImportedDraft() {
  aiImportedDraft.value = null
  aiImportSuccess.value = ''
}

function triggerJsonImport() {
  jsonImportInputRef.value?.click()
}

async function handleImportJson(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const raw = await file.text()
  input.value = ''
  store.importResumeData(raw)
}

const isAutoSavePending = computed(() => store.nextAutoSaveAt !== null)
const autoSaveChipText = computed(() => {
  if (store.isSaving) {
    return '自动保存中...'
  }

  const nextAt = store.nextAutoSaveAt
  if (nextAt) {
    const remainMs = Math.max(nextAt - nowTick.value, 0)
    const remainSec = Math.max(remainMs / 1000, 0.1)
    return `${remainSec.toFixed(1)}秒后自动保存`
  }

  const savedAt = store.lastSavedAt
  if (!savedAt) {
    return `自动保存间隔 ${Math.max(store.autoSaveDelayMs / 1000, 0.1).toFixed(1)}秒`
  }

  const elapsedMs = Math.max(nowTick.value - savedAt, 0)
  const label = store.lastSaveMode === 'manual' ? '手动保存' : '自动保存'
  if (elapsedMs < 2_000) return `刚刚${label}`
  if (elapsedMs < 60_000) return `${Math.floor(elapsedMs / 1000)}秒前${label}`
  return `${Math.floor(elapsedMs / 60_000)}分钟前${label}`
})


const cloudStatusText = computed(() => {
  if (!authStore.isLoggedIn) return '未登录：当前仅保证本地草稿保存'
  if (store.isSaving) return '云端同步中...'
  if (store.cloudUpdatedAt) return `云端已同步 · ${store.cloudUpdatedAt}`
  return '已登录：将同步到云端'
})

const authHintText = computed(() => authStore.isLoggedIn ? `当前账号：${authStore.user?.nickname || authStore.user?.email || ''}` : '登录后可跨设备同步简历草稿')

const isDefaultOrder = computed(() => store.isDefaultModuleOrder())
const hasCloudResume = computed(() => typeof store.cloudResumeId === 'number')

function handleResetOrder() {
  store.resetModuleOrder()
}

function toggleExpand(key: string) {
  expanded[key] = !expanded[key]
}

function moduleIconPaths(key: string): string[] {
  return getModuleIconPaths(key)
}

function canMoveUp(key: string): boolean {
  return store.canMoveModule(key, 'up')
}

function canMoveDown(key: string): boolean {
  return store.canMoveModule(key, 'down')
}

function moveUp(key: string) {
  store.moveModule(key, 'up')
}

function moveDown(key: string) {
  store.moveModule(key, 'down')
}

function handleSwitchDragStart(event: DragEvent, key: string) {
  if (key === 'basicInfo') {
    event.preventDefault()
    return
  }
  draggingModuleKey.value = key
  event.dataTransfer?.setData('text/plain', key)
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

function handleSwitchDragOver(event: DragEvent, key: string) {
  if (!draggingModuleKey.value || draggingModuleKey.value === key) return
  event.preventDefault()
  dragOverModuleKey.value = key
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

function handleSwitchDrop(targetKey: string) {
  const sourceKey = draggingModuleKey.value
  if (!sourceKey || sourceKey === targetKey) return
  store.reorderModule(sourceKey, targetKey)
  dragOverModuleKey.value = null
}

function handleSwitchDragEnd() {
  draggingModuleKey.value = null
  dragOverModuleKey.value = null
}

let autoSaveTicker: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  autoSaveTicker = setInterval(() => {
    nowTick.value = Date.now()
  }, 200)
  document.addEventListener('mousedown', handleDocumentPointerDown)
})


watch(
  () => store.currentResumeTitle,
  (value) => {
    if (!isEditingResumeTitle.value) {
      resumeTitleDraft.value = value || ''
      titleDirty.value = false
    }
  },
  { immediate: true }
)

watch(resumeTitleDraft, (value) => {
  titleDirty.value = value.trim() !== (store.currentResumeTitle || '').trim()
})


onUnmounted(() => {
  if (autoSaveTicker) {
    clearInterval(autoSaveTicker)
    autoSaveTicker = null
  }
  document.removeEventListener('mousedown', handleDocumentPointerDown)
})
</script>

<template>
  <main class="editor-panel">
    <div class="editor-toolbar">
      <input v-model="searchValue" class="search-input" placeholder="搜索模块：基本信息 / 教育经历 / 专业技能" />
      <span
        class="chip"
        :class="{ 'chip-pending': isAutoSavePending, 'chip-saving': store.isSaving }"
        :title="autoSaveChipText"
        :aria-label="autoSaveChipText"
        role="status"
        aria-live="polite"
      >
        <span v-if="store.isSaving" class="chip-loading" aria-hidden="true"></span>
        <svg v-else class="chip-status-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 7v5l3 2" />
          <circle cx="12" cy="12" r="8" />
        </svg>
      </span>
    </div>

    <div ref="moduleMenuRef" class="floating-tools">
      <div class="floating-tools-stack">
        <div class="module-switch-anchor">
          <button
            class="floating-tool-btn module-tool-btn"
            type="button"
            :aria-expanded="moduleMenuOpen"
            aria-haspopup="menu"
            aria-label="模块开关"
            title="模块开关"
            @click="toggleModuleMenu"
          >
            <svg class="btn-module-switch-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill-rule="evenodd"
                clip-rule="evenodd"
                d="M10.65 2.45c-.18.06-.31.21-.35.4l-.42 2.28a7.2 7.2 0 0 0-1.32.76l-2.2-.76a.58.58 0 0 0-.58.14L4.22 6.83a.58.58 0 0 0-.14.58l.76 2.2c-.3.42-.55.86-.76 1.32l-2.28.42a.55.55 0 0 0-.45.54v2.22c0 .26.19.49.45.54l2.28.42c.2.46.46.9.76 1.32l-.76 2.2c-.07.2-.02.43.14.58l1.56 1.56c.15.16.38.21.58.14l2.2-.76c.42.3.86.55 1.32.76l.42 2.28c.04.26.28.45.54.45h2.22c.26 0 .5-.19.54-.45l.42-2.28a7.2 7.2 0 0 0 1.32-.76l2.2.76c.2.07.43.02.58-.14l1.56-1.56a.58.58 0 0 0 .14-.58l-.76-2.2c.3-.42.55-.86.76-1.32l2.28-.42a.55.55 0 0 0 .45-.54v-2.22a.55.55 0 0 0-.45-.54l-2.28-.42a7.2 7.2 0 0 0-.76-1.32l.76-2.2a.58.58 0 0 0-.14-.58l-1.56-1.56a.58.58 0 0 0-.58-.14l-2.2.76a7.2 7.2 0 0 0-1.32-.76l-.42-2.28a.55.55 0 0 0-.54-.45h-2.22c-.07 0-.13.01-.19.03ZM12 15.35a3.35 3.35 0 1 0 0-6.7 3.35 3.35 0 0 0 0 6.7Z"
              />
            </svg>
            <span class="floating-badge">{{ visibleCount }}</span>
          </button>
          <div v-if="moduleMenuOpen" class="module-switch-popover">
            <div class="module-switch-popover-header">
              <p class="module-switch-popover-title">选择展示模块</p>
              <button
                class="btn-reset-order-icon"
                type="button"
                :disabled="isDefaultOrder"
                aria-label="恢复默认顺序"
                title="恢复默认顺序"
                @click="handleResetOrder"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M20 11a8 8 0 1 1-2.34-5.66" />
                  <path d="M20 4v7h-7" />
                </svg>
              </button>
            </div>
            <ul class="module-switch-list">
              <li
                v-for="mod in store.modules"
                :key="`switch-${mod.key}`"
                class="module-switch-item"
                :class="{
                  active: mod.visible,
                  muted: !mod.visible,
                  draggable: mod.key !== 'basicInfo',
                  dragging: draggingModuleKey === mod.key,
                  'drag-over': dragOverModuleKey === mod.key,
                }"
                :draggable="mod.key !== 'basicInfo'"
                @dragstart="handleSwitchDragStart($event, mod.key)"
                @dragover="handleSwitchDragOver($event, mod.key)"
                @drop.prevent="handleSwitchDrop(mod.key)"
                @dragend="handleSwitchDragEnd"
              >
                <div class="module-switch-info">
                  <span v-if="mod.key !== 'basicInfo'" class="drag-handle" aria-hidden="true" title="拖拽排序">⋮⋮</span>
                  <span class="module-switch-icon" aria-hidden="true">
                    <svg class="module-switch-icon-svg" :viewBox="MODULE_ICON_VIEWBOX">
                      <path v-for="(d, idx) in moduleIconPaths(mod.key)" :key="`switch-${mod.key}-${idx}`" :d="d" />
                    </svg>
                  </span>
                  <span class="module-switch-label">{{ mod.label }}</span>
                </div>

                <div class="module-switch-actions">
                  <div v-if="mod.key !== 'basicInfo' && mod.visible" class="order-actions order-actions-switch">
                    <button class="order-btn" :disabled="!canMoveUp(mod.key)" @click.stop="moveUp(mod.key)">↑</button>
                    <button class="order-btn" :disabled="!canMoveDown(mod.key)" @click.stop="moveDown(mod.key)">↓</button>
                  </div>
                  <label class="toggle-switch">
                    <input
                      type="checkbox"
                      :checked="mod.visible"
                      :aria-label="`${mod.label}开关`"
                      @change="store.toggleModule(mod.key)"
                    />
                    <span class="toggle-slider"></span>
                  </label>
                </div>
              </li>
            </ul>
          </div>
        </div>
        <button
          class="floating-tool-btn ai-tool-btn"
          type="button"
          aria-label="AI优化建议"
          title="AI优化建议"
          @click="handleAiClick"
        >
          <span class="ai-tool-text">AI</span>
        </button>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <p class="stat-label">简历完整度</p>
        <p class="stat-value">{{ completionPercent }}%</p>
      </div>
      <div class="stat-card">
        <p class="stat-label">模块已启用</p>
        <p class="stat-value">{{ visibleCount }} / {{ store.modules.length }}</p>
      </div>
    </div>


    <section v-if="authStore.isLoggedIn" class="resume-library-panel">
      <div class="resume-library-header">
        <div>
          <h2 class="resume-library-title">我的简历</h2>
          <p class="resume-library-subtitle">这里会显示你当前账号下的云端简历，可直接切换、创建和删除。</p>
        </div>
        <div class="resume-library-actions">
          <input v-model.trim="newResumeNameDraft" class="resume-new-input" type="text" maxlength="255" placeholder="输入新简历名称" />
          <button class="btn-import" type="button" :disabled="store.operationState !== 'idle'" @click="handleCreateResume">新建简历</button>
          <button class="btn-save" type="button" :disabled="!hasCloudResume || store.operationState !== 'idle'" @click="handleSave">保存当前简历</button>
        </div>
      </div>

      <div v-if="store.resumeList.length === 0" class="resume-library-empty">
        当前账号下还没有云端简历，点击“新建简历”开始。
      </div>

      <div v-else class="resume-library-list">
        <button
          v-for="item in store.resumeList"
          :key="item.id"
          type="button"
          class="resume-library-item"
          :class="{ active: store.cloudResumeId === item.id, disabled: store.operationState !== 'idle' }"
          :disabled="store.operationState !== 'idle'"
          @click="handleSwitchResumeById(item.id)"
        >
          <div class="resume-library-item-main">
            <strong>{{ item.title }}</strong>
            <span>{{ item.updatedAt || '暂无更新时间' }}</span>
          </div>
          <div class="resume-library-item-actions">
            <button class="resume-inline-action danger" type="button" :disabled="store.operationState !== 'idle'" @click.stop="store.cloudResumeId = item.id; resumeTitleDraft = item.title; handleDeleteResume()">删除</button>
            <span v-if="store.cloudResumeId === item.id" class="resume-library-current">当前</span>
          </div>
        </button>
      </div>
    </section>

    <section class="mobile-module-panel">
      <div class="mobile-module-panel-header">
        <div>
          <h3 class="mobile-module-panel-title">功能菜单</h3>
          <p class="mobile-module-panel-subtitle">这里可以切换显示模块、调整顺序。</p>
        </div>
        <button
          class="btn-reset-order-icon"
          type="button"
          :disabled="isDefaultOrder"
          aria-label="恢复默认顺序"
          title="恢复默认顺序"
          @click="handleResetOrder"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M20 11a8 8 0 1 1-2.34-5.66" />
            <path d="M20 4v7h-7" />
          </svg>
        </button>
      </div>
      <ul class="module-switch-list mobile-module-switch-list">
        <li
          v-for="mod in store.modules"
          :key="`mobile-switch-${mod.key}`"
          class="module-switch-item"
          :class="{
            active: mod.visible,
            muted: !mod.visible,
            draggable: mod.key !== 'basicInfo',
            dragging: draggingModuleKey === mod.key,
            'drag-over': dragOverModuleKey === mod.key,
          }"
          :draggable="mod.key !== 'basicInfo'"
          @dragstart="handleSwitchDragStart($event, mod.key)"
          @dragover="handleSwitchDragOver($event, mod.key)"
          @drop.prevent="handleSwitchDrop(mod.key)"
          @dragend="handleSwitchDragEnd"
        >
          <div class="module-switch-info">
            <span v-if="mod.key !== 'basicInfo'" class="drag-handle" aria-hidden="true" title="拖拽排序">⋮⋮</span>
            <span class="module-switch-icon" aria-hidden="true">
              <svg class="module-switch-icon-svg" :viewBox="MODULE_ICON_VIEWBOX">
                <path v-for="(d, idx) in moduleIconPaths(mod.key)" :key="`mobile-switch-${mod.key}-${idx}`" :d="d" />
              </svg>
            </span>
            <span class="module-switch-label">{{ mod.label }}</span>
          </div>

          <div class="module-switch-actions">
            <div v-if="mod.key !== 'basicInfo' && mod.visible" class="order-actions order-actions-switch">
              <button class="order-btn" :disabled="!canMoveUp(mod.key)" @click.stop="moveUp(mod.key)">↑</button>
              <button class="order-btn" :disabled="!canMoveDown(mod.key)" @click.stop="moveDown(mod.key)">↓</button>
            </div>
            <label class="toggle-switch">
              <input
                type="checkbox"
                :checked="mod.visible"
                :aria-label="`${mod.label}开关`"
                @change="store.toggleModule(mod.key)"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </li>
      </ul>
    </section>

    <section class="info-editor">
      <div class="info-editor-header">
        <div class="editor-title-row">
          <div class="editor-title-group">
            <div v-if="isEditingResumeTitle" class="resume-title-editing">
              <input
                ref="resumeTitleInputRef"
                v-model.trim="resumeTitleDraft"
                class="resume-title-input"
                type="text"
                maxlength="255"
                placeholder="请输入简历名称"
                @keydown.enter.prevent="handleRenameResume()"
                @keydown.esc.prevent="cancelRenameResume"
              />
              <button class="title-icon-btn success" type="button" :disabled="!titleDirty || store.operationState !== 'idle'" aria-label="保存简历名称" title="保存简历名称" @click="handleRenameResume()">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6 9 17l-5-5" /></svg>
              </button>
              <button class="title-icon-btn" type="button" :disabled="store.operationState !== 'idle'" aria-label="取消重命名" title="取消重命名" @click="cancelRenameResume">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
              </button>
            </div>
            <div v-else class="resume-title-display">
              <h2 class="editor-title">{{ store.currentResumeTitle || '信息编辑区' }}</h2>
              <button class="title-icon-btn" type="button" :disabled="!hasCloudResume || store.operationState !== 'idle'" aria-label="编辑简历名称" title="编辑简历名称" @click="startRenameResume">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20h9" /><path d="M16.5 3.5a2.12 2.12 0 1 1 3 3L7 19l-4 1 1-4Z" /></svg>
              </button>
            </div>
          </div>
          <span class="storage-tip-wrap">
            <button
              class="storage-tip-trigger"
              type="button"
              aria-label="查看简历本地存储提示"
              aria-describedby="resume-storage-tooltip"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 11v5" />
                <path d="M12 8h.01" />
              </svg>
            </button>
            <span id="resume-storage-tooltip" class="storage-tooltip" role="tooltip">
              简历编辑不存储任何个人数据，存储到您本人浏览器缓存里，如果您删除浏览器缓存可能造成数据丢失，建议您编辑完先导出 json 后续可直接导入恢复。
            </span>
          </span>
        </div>
        <div class="editor-header-actions">
          <button class="btn-import" type="button" :disabled="aiImporting" @click="triggerAiImport">{{ aiImporting ? 'AI 导入中…' : 'AI 导入简历' }}</button>
          <button class="btn-import" type="button" @click="triggerJsonImport">导入 JSON</button>
          <button class="btn-save" @click="handleSave">保存草稿</button>
        </div>
      </div>
      <p class="editor-subtitle">模块顺序与模块开关一致，点击右侧可展开/收起</p>
      <input ref="aiImportInputRef" type="file" accept=".pdf,.txt,.md,.docx,.png,.jpg,.jpeg,.webp" style="display: none" @change="handleAiImport" />
      <input
        ref="jsonImportInputRef"
        type="file"
        accept=".json,application/json"
        style="display: none"
        @change="handleImportJson"
      />
      <transition name="fade">
        <p v-if="showSaved" class="save-hint">已保存</p>
      </transition>

      <p v-if="aiImporting && aiImportStageText" class="ai-import-feedback processing">{{ aiImportStageText }}</p>
      <p v-if="aiImportError" class="ai-import-feedback error">{{ aiImportError }}</p>
      <p v-if="aiImportSuccess && !aiImportedDraft" class="ai-import-feedback success">{{ aiImportSuccess }}</p>

      <div v-if="aiImportedDraft" class="ai-import-result">
        <div class="ai-import-result-copy">
          <strong>AI 已完成简历解析：{{ aiImportedDraft.title }}</strong>
          <p>你可以先应用到当前编辑中的简历，或者直接另存为一份新简历。</p>
          <div v-if="aiImportSummary" class="ai-import-preview">
            <div class="ai-import-preview-grid">
              <span><b>姓名：</b>{{ aiImportSummary.name || '未识别' }}</span>
              <span><b>电话：</b>{{ aiImportSummary.phone || '未识别' }}</span>
              <span><b>邮箱：</b>{{ aiImportSummary.email || '未识别' }}</span>
              <span><b>求职意向：</b>{{ aiImportSummary.jobTitle || '未识别' }}</span>
              <span><b>教育经历：</b>{{ aiImportSummary.educationCount }}</span>
              <span><b>工作经历：</b>{{ aiImportSummary.workCount }}</span>
              <span><b>项目经历：</b>{{ aiImportSummary.projectCount }}</span>
            </div>
            <p v-if="aiImportSummary.skills" class="ai-import-preview-skills"><b>技能摘要：</b>{{ aiImportSummary.skills }}</p>
            <details v-if="aiImportSummary.extractedTextPreview" class="ai-import-preview-text">
              <summary>查看提取文本预览</summary>
              <pre>{{ aiImportSummary.extractedTextPreview }}</pre>
            </details>
          </div>
        </div>
        <div class="ai-import-result-actions">
          <button class="btn-import" type="button" @click="applyImportedDraftToCurrent">应用到当前简历</button>
          <button class="btn-save" type="button" @click="saveImportedDraftAsNewResume">另存为新简历</button>
          <button class="panel-action subtle" type="button" @click="dismissImportedDraft">取消</button>
        </div>
      </div>

      <div class="module-sections">
        <article
          v-for="mod in filteredModules"
          :key="mod.key"
          class="module-block"
          :class="{ disabled: !mod.visible }"
        >
	          <header class="module-head" @click="toggleExpand(mod.key)">
	            <div class="module-head-left">
	              <span class="module-head-icon" aria-hidden="true">
	                <svg class="module-head-icon-svg" :viewBox="MODULE_ICON_VIEWBOX">
	                  <path v-for="(d, idx) in moduleIconPaths(mod.key)" :key="`${mod.key}-${idx}`" :d="d" />
	                </svg>
	              </span>
	              <span class="module-head-title">{{ mod.label }}</span>
	            </div>
            <div class="module-head-right">
              <span v-if="!mod.visible" class="disabled-tag">已关闭</span>
              <span class="expand-text">{{ expanded[mod.key] && mod.visible ? '收起' : '展开' }} ▸</span>
            </div>
          </header>

          <div v-if="expanded[mod.key] && mod.visible" class="module-body">
            <component :is="editorMap[mod.key]" />
          </div>
        </article>

        <div v-if="filteredModules.length === 0" class="empty-result">没有匹配的模块</div>
      </div>
    </section>

    <AiOptimizePanel
      :open="showAiPanel"
      @close="showAiPanel = false"
    />
  </main>
</template>

<style scoped src="./EditorPanel.css"></style>
<style scoped src="./EditorPanel.responsive.css"></style>
<style scoped>

.editor-title-group { display:flex; align-items:center; gap:10px; min-width:0; }
.resume-title-display { display:flex; align-items:center; gap:10px; min-width:0; }
.resume-title-editing { display:flex; align-items:center; gap:8px; min-width:0; }
.resume-title-input { height:40px; min-width:220px; max-width:360px; border-radius:12px; border:1px solid #dfd2c2; background:#fff; padding:0 12px; font-size:18px; font-weight:800; color:#2d2521; }
.title-icon-btn { width:34px; height:34px; display:inline-flex; align-items:center; justify-content:center; border-radius:999px; border:1px solid #dfd2c2; background:#fff; color:#7b6a5b; padding:0; }
.title-icon-btn svg { width:16px; height:16px; stroke:currentColor; stroke-width:2; fill:none; stroke-linecap:round; stroke-linejoin:round; }
.title-icon-btn.success { color:#117a37; border-color:#b7dfc2; background:#f3fcf6; }
.title-icon-btn:disabled { opacity:.55; cursor:not-allowed; }
.mobile-module-panel { display:none; margin-bottom: 12px; padding: 14px; border: 1px solid #e7d8c8; border-radius: 16px; background:#fffaf5; }
.mobile-module-panel-header { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:10px; }
.mobile-module-panel-title { margin:0; font-size:16px; color:#2d2521; }
.mobile-module-panel-subtitle { margin:4px 0 0; color:#7b6a5b; font-size:12px; line-height:1.5; }
.mobile-module-switch-list { max-height:none; }
.resume-library-panel { margin-bottom: 14px; padding: 16px; border: 1px solid #e7d8c8; border-radius: 18px; background: #fffaf5; }
.resume-library-header { display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom: 12px; }
.resume-library-title { margin:0; font-size:18px; color:#2d2521; }
.resume-library-subtitle { margin:4px 0 0; color:#7b6a5b; font-size:12px; line-height:1.6; }
.resume-library-actions { display:flex; gap:8px; flex-wrap:wrap; }
.resume-new-input { height:36px; min-width:160px; border-radius:12px; border:1px solid #dfd2c2; background:#fff; padding:0 12px; font-size:12px; font-weight:700; color:#2d2521; }
.resume-library-empty { padding:12px 14px; border-radius:12px; background:#fff; color:#7b6a5b; font-size:12px; font-weight:700; }
.resume-library-list { display:flex; flex-direction:column; gap:8px; }
.resume-library-item { display:flex; align-items:center; justify-content:space-between; gap:10px; width:100%; padding:12px 14px; border-radius:14px; border:1px solid #e7d8c8; background:#fff; text-align:left; }
.resume-library-item-actions { display:flex; align-items:center; gap:8px; flex-shrink:0; }
.resume-inline-action { height:28px; padding:0 10px; border-radius:999px; border:1px solid #dfd2c2; background:#fff; color:#7b6a5b; font-size:11px; font-weight:800; }
.resume-inline-action.danger { color:#b42318; }
.resume-library-item.active { border-color:#2d2521; box-shadow:0 0 0 3px rgba(45,37,33,.08); background:#fffdf9; }
.resume-library-item.disabled { opacity:.65; cursor:not-allowed; }
.resume-library-item-main { display:flex; flex-direction:column; gap:4px; min-width:0; }
.resume-library-item-main strong { color:#2d2521; font-size:14px; }
.resume-library-item-main span { color:#8a7461; font-size:11px; }
.resume-library-current { flex-shrink:0; padding:4px 10px; border-radius:999px; background:#2d2521; color:#fff; font-size:11px; font-weight:800; }
.ai-import-feedback { margin:14px 0 0; padding:10px 12px; border-radius:12px; font-size:12px; font-weight:700; }
.ai-import-feedback.processing { background:#fff8f1; color:#7b6a5b; border:1px solid #ead9c6; }
.ai-import-feedback.error { background:#fff1f1; color:#b42318; border:1px solid #f1c7c7; }
.ai-import-feedback.success { background:#effaf3; color:#117a37; border:1px solid #cdebd5; }
.ai-import-result { margin: 14px 0 0; padding: 14px 16px; border: 1px solid #e7d8c8; border-radius: 16px; background: #fff8f1; display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.ai-import-result-copy strong { display:block; margin-bottom: 4px; color:#2d2521; }
.ai-import-result-copy p { margin:0; color:#7b6a5b; font-size:12px; line-height:1.6; }
.ai-import-preview { margin-top:10px; padding-top:10px; border-top:1px dashed #e7d8c8; }
.ai-import-preview-grid { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:6px 12px; font-size:12px; color:#5f534a; }
.ai-import-preview-skills { margin:8px 0 0; font-size:12px; color:#5f534a; line-height:1.6; }
.ai-import-preview-text { margin-top:10px; }
.ai-import-preview-text summary { cursor:pointer; font-size:12px; font-weight:800; color:#7b6a5b; }
.ai-import-preview-text pre { margin:8px 0 0; max-height:180px; overflow:auto; padding:10px 12px; border-radius:12px; background:#fff; font-size:12px; line-height:1.5; white-space:pre-wrap; color:#4c4038; }
.ai-import-result-actions { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
</style>
