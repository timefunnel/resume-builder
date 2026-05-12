import { defineStore } from 'pinia'
import { reactive, ref, watch } from 'vue'
import {
  createResume,
  deleteResumeById,
  getCurrentResume,
  getResumeById,
  listResumes,
  putCurrentResume,
  updateResumeById,
  type ResumeSummaryPayload,
} from '@/api/resumeApi'
import { normalizeResumeTemplateKey, type ResumeTemplateKey } from '@/templates/resume'
// author: jf

export interface BasicInfo { name: string; phone: string; email: string; age: string; gender: string; location: string; jobTitle: string; educationLevel: string; avatar: string; workYears: string; currentStatus: string; expectedLocation: string; expectedSalary: string; website: string; wechat: string; currentCity: string; github: string; blog: string }
export interface EducationEntry { id: string; school: string; college: string; major: string; degree: string; startDate: string; endDate: string; gpa: string; description: string; type: string; location: string }
export interface WorkEntry { id: string; company: string; department: string; position: string; startDate: string; endDate: string; location: string; description: string }
export interface ProjectEntry { id: string; name: string; role: string; startDate: string; endDate: string; link: string; introduction: string; mainWork: string }
export interface AwardEntry { id: string; name: string; date: string; description: string }
export interface ModuleConfig { key: string; label: string; icon: string; visible: boolean }
type MoveDirection = 'up' | 'down'
const DEFAULT_MODULE_ORDER = ['basicInfo','education','skills','workExperience','projectExperience','awards','selfIntro'] as const
let _idCounter = 0
function genId(): string { return `item_${Date.now()}_${++_idCounter}` }

export const useResumeStore = defineStore('resume', () => {
  const modules = reactive<ModuleConfig[]>([
    { key: 'basicInfo', label: '基本信息', icon: '👤', visible: true },
    { key: 'education', label: '教育经历', icon: '🎓', visible: true },
    { key: 'skills', label: '专业技能', icon: '⚡', visible: true },
    { key: 'workExperience', label: '工作经历', icon: '💼', visible: true },
    { key: 'projectExperience', label: '项目经历', icon: '📁', visible: true },
    { key: 'awards', label: '荣誉奖项', icon: '🏆', visible: false },
    { key: 'selfIntro', label: '个人简介', icon: '📝', visible: false },
  ])
  const basicInfo = reactive<BasicInfo>({ name:'', phone:'', email:'', age:'', gender:'', location:'', jobTitle:'', educationLevel:'', avatar:'', workYears:'', currentStatus:'', expectedLocation:'', expectedSalary:'', website:'', wechat:'', currentCity:'', github:'', blog:'' })
  const educationList = reactive<EducationEntry[]>([{ id: genId(), school:'', college:'', major:'', degree:'', startDate:'', endDate:'', gpa:'', description:'', type:'', location:'' }])
  const skills = ref('')
  const workList = reactive<WorkEntry[]>([{ id: genId(), company:'', department:'', position:'', startDate:'', endDate:'', location:'', description:'' }])
  const projectList = reactive<ProjectEntry[]>([{ id: genId(), name:'', role:'', startDate:'', endDate:'', link:'', introduction:'', mainWork:'' }])
  const awardList = reactive<AwardEntry[]>([])
  const selfIntro = ref('')
  const selectedTemplateKey = ref<ResumeTemplateKey>('default')
  const nextAutoSaveAt = ref<number | null>(null)
  const lastSavedAt = ref<number | null>(null)
  const lastSaveMode = ref<'auto'|'manual'|null>(null)
  const isSaving = ref(false)
  const cloudResumeId = ref<number | null>(null)
  const cloudUpdatedAt = ref<string | null>(null)
  const resumeList = ref<ResumeSummaryPayload[]>([])
  const currentResumeTitle = ref('我的简历')
  const currentResumeLoaded = ref(false)
  const operationState = ref<'idle' | 'loading' | 'creating' | 'switching' | 'deleting' | 'saving'>('idle')

  const STORAGE_KEY_BASE = 'resume-builder-data'
  const AUTO_SAVE_DELAY_MS = 500
  const SAVE_LOADING_MIN_MS = 900
  const CLOUD_SAVE_DELAY_MS = 1200
  let saveLoadingTimer: ReturnType<typeof setTimeout> | null = null
  let saveTimer: ReturnType<typeof setTimeout> | null = null
  let cloudSaveTimer: ReturnType<typeof setTimeout> | null = null
  let activeStorageKey = STORAGE_KEY_BASE

  function updateStorageKey(userId?: number | null) { activeStorageKey = userId ? `${STORAGE_KEY_BASE}:user:${userId}` : STORAGE_KEY_BASE }
  function markSavingState() { isSaving.value = true; if (saveLoadingTimer) clearTimeout(saveLoadingTimer); saveLoadingTimer = setTimeout(() => { isSaving.value = false; saveLoadingTimer = null }, SAVE_LOADING_MIN_MS) }
  function snapshotResumeData() { return { modules: modules.map((m) => ({ ...m })), selectedTemplateKey: selectedTemplateKey.value, basicInfo: { ...basicInfo }, educationList: educationList.map((e) => ({ ...e })), skills: skills.value, workList: workList.map((w) => ({ ...w })), projectList: projectList.map((p) => ({ ...p })), awardList: awardList.map((a) => ({ ...a })), selfIntro: selfIntro.value } }
  function resetResumeState() {
    modules.splice(0, modules.length,
      { key: 'basicInfo', label: '基本信息', icon: '👤', visible: true },
      { key: 'education', label: '教育经历', icon: '🎓', visible: true },
      { key: 'skills', label: '专业技能', icon: '⚡', visible: true },
      { key: 'workExperience', label: '工作经历', icon: '💼', visible: true },
      { key: 'projectExperience', label: '项目经历', icon: '📁', visible: true },
      { key: 'awards', label: '荣誉奖项', icon: '🏆', visible: false },
      { key: 'selfIntro', label: '个人简介', icon: '📝', visible: false },
    )
    Object.assign(basicInfo, { name:'', phone:'', email:'', age:'', gender:'', location:'', jobTitle:'', educationLevel:'', avatar:'', workYears:'', currentStatus:'', expectedLocation:'', expectedSalary:'', website:'', wechat:'', currentCity:'', github:'', blog:'' })
    educationList.splice(0, educationList.length, { id: genId(), school:'', college:'', major:'', degree:'', startDate:'', endDate:'', gpa:'', description:'', type:'', location:'' })
    skills.value = ''
    workList.splice(0, workList.length, { id: genId(), company:'', department:'', position:'', startDate:'', endDate:'', location:'', description:'' })
    projectList.splice(0, projectList.length, { id: genId(), name:'', role:'', startDate:'', endDate:'', link:'', introduction:'', mainWork:'' })
    awardList.splice(0, awardList.length)
    selfIntro.value = ''
    selectedTemplateKey.value = 'default'
  }
  function applyResumeData(data: any) {
    if (!data || typeof data !== 'object') return
    if (data.modules) {
      const byKey = new Map<string, ModuleConfig>()
      ;(data.modules as ModuleConfig[]).forEach((m) => { if (m?.key) byKey.set(m.key, m) })
      const orderedKeys = ['basicInfo', ...(data.modules as ModuleConfig[]).map((m) => m.key).filter((key) => key && key !== 'basicInfo')]
      const seen = new Set<string>()
      const nextModules: ModuleConfig[] = []
      orderedKeys.forEach((key) => { if (seen.has(key)) return; seen.add(key); const fallback = modules.find((m) => m.key === key); if (!fallback) return; nextModules.push({ ...fallback, ...byKey.get(key) }) })
      modules.forEach((m) => { if (seen.has(m.key)) return; nextModules.push({ ...m, ...byKey.get(m.key) }) })
      modules.splice(0, modules.length, ...nextModules)
    }
    selectedTemplateKey.value = normalizeResumeTemplateKey(data.selectedTemplateKey ?? data.selectedTemplateId)
    if (data.basicInfo) Object.assign(basicInfo, data.basicInfo)
    if (data.educationList) educationList.splice(0, educationList.length, ...data.educationList)
    if (data.skills !== undefined) skills.value = data.skills
    if (data.workList) workList.splice(0, workList.length, ...data.workList)
    if (data.projectList) projectList.splice(0, projectList.length, ...data.projectList)
    if (data.awardList) awardList.splice(0, awardList.length, ...data.awardList)
    if (data.selfIntro !== undefined) selfIntro.value = data.selfIntro
  }
  function exportResumeData(): string { return JSON.stringify(snapshotResumeData(), null, 2) }
  function saveToStorage(mode: 'auto'|'manual'='manual') { if (mode === 'manual' && saveTimer) { clearTimeout(saveTimer); saveTimer = null }; markSavingState(); localStorage.setItem(activeStorageKey, JSON.stringify(snapshotResumeData())); nextAutoSaveAt.value = null; lastSavedAt.value = Date.now(); lastSaveMode.value = mode }
  function loadFromStorage() { const raw = localStorage.getItem(activeStorageKey); if (!raw) return; try { applyResumeData(JSON.parse(raw)) } catch (e) { console.warn('Failed to load resume data from localStorage', e) } }
  function importResumeData(raw: string) { const data = JSON.parse(raw); localStorage.setItem(activeStorageKey, JSON.stringify(data)); applyResumeData(data); saveToStorage('manual') }
  async function fetchResumeList() { const response = await listResumes(); if (!response.ok) throw new Error(`简历列表加载失败 (${response.status})`); resumeList.value = await response.json().catch(() => []); return resumeList.value }
  async function saveToCloud(title = currentResumeTitle.value || '我的简历') {
    if (operationState.value in {loading:1, creating:1, switching:1, deleting:1}) return null as any
    operationState.value = 'saving'
    markSavingState()
    try {
      const payload = { title, content: snapshotResumeData() }
      const response = cloudResumeId.value ? await updateResumeById(cloudResumeId.value, payload) : await putCurrentResume(payload)
      if (!response.ok) { const text = await response.text().catch(() => ''); throw new Error(text || `云端保存失败 (${response.status})`) }
      const result = await response.json().catch(() => null)
      cloudResumeId.value = typeof result?.id === 'number' ? result.id : null
      cloudUpdatedAt.value = typeof result?.updatedAt === 'string' ? result.updatedAt : null
      currentResumeTitle.value = typeof result?.title === 'string' ? result.title : title
      await fetchResumeList().catch(() => undefined)
      lastSavedAt.value = Date.now(); lastSaveMode.value = 'manual'; return result
    } finally {
      operationState.value = 'idle'
    }
  }
  function scheduleCloudSave(title = currentResumeTitle.value || '我的简历') { if (operationState.value !== 'idle' || !currentResumeLoaded.value || !cloudResumeId.value) return; if (cloudSaveTimer) clearTimeout(cloudSaveTimer); cloudSaveTimer = setTimeout(() => { if (operationState.value !== 'idle' || !currentResumeLoaded.value || !cloudResumeId.value) return; cloudSaveTimer = null; saveToCloud(title).catch((error) => console.warn('Failed to autosave resume to cloud', error)) }, CLOUD_SAVE_DELAY_MS) }
  async function loadResumeById(resumeId: number) { operationState.value = 'switching'; const response = await getResumeById(resumeId); if (!response.ok) throw new Error(`简历加载失败 (${response.status})`); const payload = await response.json().catch(() => null); cloudResumeId.value = typeof payload?.id === 'number' ? payload.id : null; cloudUpdatedAt.value = typeof payload?.updatedAt === 'string' ? payload.updatedAt : null; currentResumeTitle.value = typeof payload?.title === 'string' ? payload.title : '我的简历'; if (payload?.content && typeof payload.content === 'object') { localStorage.setItem(activeStorageKey, JSON.stringify(payload.content)); resetResumeState(); applyResumeData(payload.content) } currentResumeLoaded.value = true; operationState.value = 'idle'; return payload }
  async function loadFromCloud() { operationState.value = 'loading'; const response = await getCurrentResume(); if (!response.ok) throw new Error(`云端加载失败 (${response.status})`); const payload = await response.json().catch(() => null); cloudResumeId.value = typeof payload?.id === 'number' ? payload.id : null; cloudUpdatedAt.value = typeof payload?.updatedAt === 'string' ? payload.updatedAt : null; currentResumeTitle.value = typeof payload?.title === 'string' ? payload.title : '我的简历'; if (payload?.content && typeof payload.content === 'object' && Object.keys(payload.content).length > 0) { localStorage.setItem(activeStorageKey, JSON.stringify(payload.content)); resetResumeState(); applyResumeData(payload.content) } currentResumeLoaded.value = true; await fetchResumeList().catch(() => undefined); operationState.value = 'idle'; return payload }
  async function createNewResume(title = '新的简历') { operationState.value = 'creating'; const response = await createResume({ title, content: {} }); if (!response.ok) throw new Error(`新建简历失败 (${response.status})`); const payload = await response.json().catch(() => null); cloudResumeId.value = typeof payload?.id === 'number' ? payload.id : null; cloudUpdatedAt.value = typeof payload?.updatedAt === 'string' ? payload.updatedAt : null; currentResumeTitle.value = typeof payload?.title === 'string' ? payload.title : title; resetResumeState(); localStorage.setItem(activeStorageKey, JSON.stringify({})); currentResumeLoaded.value = true; await fetchResumeList().catch(() => undefined); operationState.value = 'idle'; return payload }
  async function deleteCurrentResume() { if (!cloudResumeId.value) return; operationState.value = 'deleting'; const id = cloudResumeId.value; const response = await deleteResumeById(id); if (!response.ok) throw new Error(`删除简历失败 (${response.status})`); cloudResumeId.value = null; cloudUpdatedAt.value = null; currentResumeTitle.value = '我的简历'; await fetchResumeList(); if (resumeList.value.length > 0) { await loadResumeById(resumeList.value[0].id) } else { resetResumeState(); currentResumeLoaded.value = false; localStorage.setItem(activeStorageKey, JSON.stringify({})); operationState.value = 'idle' } }

  function toggleModule(key: string) { const mod = modules.find((m) => m.key === key); if (mod) mod.visible = !mod.visible }
  function setTemplate(key: ResumeTemplateKey) { selectedTemplateKey.value = key }
  function canMoveModule(key: string, direction: MoveDirection): boolean { if (key === 'basicInfo') return false; const idx = modules.findIndex((m) => m.key === key); if (idx < 0) return false; const mod = modules[idx]; if (!mod?.visible) return false; return direction === 'up' ? idx > 1 : idx < modules.length - 1 }
  function moveModule(key: string, direction: MoveDirection) { if (!canMoveModule(key, direction)) return; const idx = modules.findIndex((m) => m.key === key); const target = direction === 'up' ? idx - 1 : idx + 1; const current = modules[idx]; const next = modules[target]; if (!current || !next) return; modules[idx] = next; modules[target] = current }
  function reorderModule(sourceKey: string, targetKey: string) { if (sourceKey === targetKey || sourceKey === 'basicInfo') return; const sourceIndex = modules.findIndex((m) => m.key === sourceKey); const targetIndex = modules.findIndex((m) => m.key === targetKey); if (sourceIndex < 0 || targetIndex < 0) return; const [sourceModule] = modules.splice(sourceIndex, 1); if (!sourceModule) return; let nextIndex = targetKey === 'basicInfo' ? 1 : targetIndex; if (sourceIndex < targetIndex) nextIndex -= 1; nextIndex = Math.max(1, Math.min(nextIndex, modules.length)); modules.splice(nextIndex, 0, sourceModule) }
  function isDefaultModuleOrder(): boolean { return modules.every((m, idx) => m.key === DEFAULT_MODULE_ORDER[idx]) }
  function resetModuleOrder() { const indexMap = new Map<string, number>(); DEFAULT_MODULE_ORDER.forEach((key, idx) => indexMap.set(key, idx)); const sorted = [...modules].sort((a, b) => (indexMap.get(a.key) ?? 999) - (indexMap.get(b.key) ?? 999)); modules.splice(0, modules.length, ...sorted) }
  function isModuleVisible(key: string): boolean { return !!modules.find((m) => m.key === key)?.visible }
  function addEducation() { educationList.push({ id: genId(), school:'', college:'', major:'', degree:'', startDate:'', endDate:'', gpa:'', description:'', type:'', location:'' }) }
  function removeEducation(id: string) { const idx = educationList.findIndex((e) => e.id === id); if (idx > -1) educationList.splice(idx, 1) }
  function addWork() { workList.push({ id: genId(), company:'', department:'', position:'', startDate:'', endDate:'', location:'', description:'' }) }
  function removeWork(id: string) { const idx = workList.findIndex((e) => e.id === id); if (idx > -1) workList.splice(idx, 1) }
  function addProject() { projectList.push({ id: genId(), name:'', role:'', startDate:'', endDate:'', link:'', introduction:'', mainWork:'' }) }
  function removeProject(id: string) { const idx = projectList.findIndex((e) => e.id === id); if (idx > -1) projectList.splice(idx, 1) }
  function canMoveProject(id: string, direction: MoveDirection): boolean { const idx = projectList.findIndex((e) => e.id === id); return idx >= 0 && (direction === 'up' ? idx > 0 : idx < projectList.length - 1) }
  function moveProject(id: string, direction: MoveDirection) { if (!canMoveProject(id, direction)) return; const idx = projectList.findIndex((e) => e.id === id); const target = direction === 'up' ? idx - 1 : idx + 1; const current = projectList[idx]; const next = projectList[target]; if (!current || !next) return; projectList[idx] = next; projectList[target] = current }
  function addAward() { awardList.push({ id: genId(), name:'', date:'', description:'' }) }
  function removeAward(id: string) { const idx = awardList.findIndex((e) => e.id === id); if (idx > -1) awardList.splice(idx, 1) }

  updateStorageKey(null)
  loadFromStorage()

  watch([() => JSON.stringify(basicInfo), () => JSON.stringify(educationList), skills, () => JSON.stringify(workList), () => JSON.stringify(projectList), () => JSON.stringify(awardList), selfIntro, selectedTemplateKey, () => JSON.stringify(modules)], () => {
    if (saveTimer) clearTimeout(saveTimer)
    nextAutoSaveAt.value = Date.now() + AUTO_SAVE_DELAY_MS
    saveTimer = setTimeout(() => { saveTimer = null; saveToStorage('auto') }, AUTO_SAVE_DELAY_MS)
  }, { deep: true })

  return { modules, selectedTemplateKey, basicInfo, educationList, skills, workList, projectList, awardList, selfIntro, toggleModule, setTemplate, canMoveModule, moveModule, reorderModule, isDefaultModuleOrder, resetModuleOrder, isModuleVisible, addEducation, removeEducation, addWork, removeWork, addProject, removeProject, canMoveProject, moveProject, addAward, removeAward, exportResumeData, snapshotResumeData, importResumeData, saveToStorage, saveToCloud, scheduleCloudSave, loadFromCloud, loadResumeById, fetchResumeList, createNewResume, deleteCurrentResume, updateStorageKey, autoSaveDelayMs: AUTO_SAVE_DELAY_MS, nextAutoSaveAt, lastSavedAt, lastSaveMode, isSaving, cloudResumeId, cloudUpdatedAt, resumeList, currentResumeTitle, currentResumeLoaded, operationState }
})
