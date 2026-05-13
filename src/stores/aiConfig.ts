import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

export interface AiConfig {
  apiUrl: string
  apiToken: string
  modelName: string
  useBackendSpeech: boolean
  backendSpeechAutoDisabled: boolean
  speechMode?: 'backend' | 'chunked' | 'browser'
}

const STORAGE_KEY = 'resume-builder-ai-config'

export const useAiConfigStore = defineStore('aiConfig', () => {
  const apiUrl = ref('')
  const apiToken = ref('')
  const modelName = ref('')
  const useBackendSpeech = ref(true)
  const backendSpeechAutoDisabled = ref(false)
  const speechMode = ref<'backend' | 'chunked' | 'browser'>('backend')

  const isConfigured = computed(
    () => apiUrl.value.trim() !== '' && apiToken.value.trim() !== '' && modelName.value.trim() !== '',
  )
  const shouldRequestBackendSpeech = computed(
    () => speechMode.value === 'backend' && useBackendSpeech.value && !backendSpeechAutoDisabled.value,
  )
  const shouldUseChunkedSpeech = computed(() => speechMode.value === 'chunked')
  const shouldUseBrowserSpeechOnly = computed(() => speechMode.value === 'browser')

  function loadFromStorage() {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    try {
      const data = JSON.parse(raw) as Partial<AiConfig>
      if (data.apiUrl) apiUrl.value = data.apiUrl
      if (data.apiToken) apiToken.value = data.apiToken
      if (data.modelName) modelName.value = data.modelName
      if (typeof data.useBackendSpeech === 'boolean') useBackendSpeech.value = data.useBackendSpeech
      if (typeof data.backendSpeechAutoDisabled === 'boolean') {
        backendSpeechAutoDisabled.value = data.backendSpeechAutoDisabled
      }
      if (data.speechMode === 'backend' || data.speechMode === 'chunked' || data.speechMode === 'browser') {
        speechMode.value = data.speechMode
      }
    } catch {
      console.warn('Failed to load AI config from localStorage')
    }
  }

  function saveToStorage() {
    const data: AiConfig = {
      apiUrl: apiUrl.value,
      apiToken: apiToken.value,
      modelName: modelName.value,
      useBackendSpeech: useBackendSpeech.value,
      backendSpeechAutoDisabled: backendSpeechAutoDisabled.value,
      speechMode: speechMode.value,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }

  function updateConfig(config: Pick<AiConfig, 'apiUrl' | 'apiToken' | 'modelName'> & Partial<Pick<AiConfig, 'useBackendSpeech'>>) {
    apiUrl.value = config.apiUrl
    apiToken.value = config.apiToken
    modelName.value = config.modelName
    if (typeof config.useBackendSpeech === 'boolean') {
      useBackendSpeech.value = config.useBackendSpeech
      if (config.useBackendSpeech) {
        backendSpeechAutoDisabled.value = false
      }
    }
    saveToStorage()
  }

  function setSpeechMode(mode: 'backend' | 'chunked' | 'browser') {
    speechMode.value = mode
    if (mode !== 'backend') {
      backendSpeechAutoDisabled.value = false
    }
    saveToStorage()
  }

  function setUseBackendSpeech(enabled: boolean) {
    useBackendSpeech.value = enabled
    if (enabled) {
      backendSpeechAutoDisabled.value = false
    }
    saveToStorage()
  }

  function markBackendSpeechUnavailable() {
    if (!useBackendSpeech.value) return
    backendSpeechAutoDisabled.value = true
    saveToStorage()
  }

  function clearBackendSpeechUnavailable() {
    backendSpeechAutoDisabled.value = false
    saveToStorage()
  }

  function clearConfig() {
    apiUrl.value = ''
    apiToken.value = ''
    modelName.value = ''
    useBackendSpeech.value = true
    backendSpeechAutoDisabled.value = false
    localStorage.removeItem(STORAGE_KEY)
  }

  loadFromStorage()

  watch([apiUrl, apiToken, modelName, useBackendSpeech, backendSpeechAutoDisabled], () => saveToStorage(), { deep: true })

  return {
    apiUrl,
    apiToken,
    modelName,
    useBackendSpeech,
    backendSpeechAutoDisabled,
    speechMode,
    shouldRequestBackendSpeech,
    shouldUseChunkedSpeech,
    shouldUseBrowserSpeechOnly,
    isConfigured,
    updateConfig,
    setSpeechMode,
    setUseBackendSpeech,
    markBackendSpeechUnavailable,
    clearBackendSpeechUnavailable,
    clearConfig,
  }
})
