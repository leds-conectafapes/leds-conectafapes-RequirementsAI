<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { loadUserAIConfig, updateUserAIConfig, removeUserAIConfig } from '../controllers/aiConfig'
import type { UserAIConfig } from '../types/aiConfig'

const router = useRouter()
const { t } = useI18n()

const apiKey = ref('')
const provider = ref<'openai' | 'gemini'>('gemini')
const maskedKey = ref<string | null>(null)
const configured = ref(false)
const loading = ref(false)
const errorMessage = ref<string | null>(null)
const successMessage = ref<string | null>(null)

const title = computed(() => (configured.value ? t('aiConfig.title_configured') : t('aiConfig.title_configure')))

const fetchConfig = async () => {
  loading.value = true
  errorMessage.value = null
  successMessage.value = null

  try {
    const data = await loadUserAIConfig()
    configured.value = data.configured
    maskedKey.value = data.masked_key
    provider.value = (data.provider as any) || 'gemini'
  } catch (error) {
    errorMessage.value = t('aiConfig.error_load')
  } finally {
    loading.value = false
  }
}

const submit = async () => {
  if (!apiKey.value.trim()) {
    errorMessage.value = t('aiConfig.error_invalid_key')
    successMessage.value = null
    return
  }

  loading.value = true
  errorMessage.value = null
  successMessage.value = null

  try {
    const data = await updateUserAIConfig({ api_key: apiKey.value.trim(), provider: provider.value })
    configured.value = data.configured
    maskedKey.value = data.masked_key
    apiKey.value = ''
    successMessage.value = t('aiConfig.success_saved')
  } catch (error) {
    errorMessage.value = t('aiConfig.error_save')
  } finally {
    loading.value = false
  }
}

const clearConfig = async () => {
  loading.value = true
  errorMessage.value = null
  successMessage.value = null

  try {
    await removeUserAIConfig()
    configured.value = false
    maskedKey.value = null
    apiKey.value = ''
    successMessage.value = t('aiConfig.success_removed')
  } catch (error) {
    errorMessage.value = t('aiConfig.error_remove')
  } finally {
    loading.value = false
  }
}

onMounted(fetchConfig)
</script>

<template>
  <div class="w-11/12 max-w-3xl mx-auto my-10 p-6 bg-white rounded-lg shadow-sm">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900">{{ title }}</h1>
        <p class="text-sm text-gray-600 mt-1">{{ t('aiConfig.manage_description') }}</p>
      </div>
      <button
        class="px-4 py-2 border-gray-700 text-gray-700 rounded-lg hover:bg-gray-700 hover:text-white transition cursor-pointer"
        @click="router.push({ name: 'projeto-home' })"
      >
        {{ t('aiConfig.back') }}
      </button>
    </div>

    <div v-if="configured" class="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
      <p class="text-sm text-green-700">{{ t('aiConfig.current_key_configured', { maskedKey }) }}</p>
      <p class="text-sm text-gray-600 mt-1">{{ t('aiConfig.current_key_warning') }}</p>
    </div>

    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">{{ t('aiConfig.provider_label') }}</label>
        <select v-model="provider" class="w-full p-2 border rounded-md mb-3">
          <option value="gemini">{{ t('aiConfig.provider_gemini') }}</option>
          <option value="openai">{{ t('aiConfig.provider_openai') }}</option>
        </select>

        <label class="block text-sm font-medium text-gray-700 mb-2">{{ t('aiConfig.api_key_label') }}</label>
        <text-input
          class="w-full"
          type="password"
          :placeholder="t('aiConfig.api_key_placeholder')"
          v-model="apiKey"
        />
      </div>

      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div class="flex gap-3 whitespace-nowrap">
          <button
            class="px-5 py-2 bg-blue-800 text-white rounded-lg hover:bg-blue-900 transition cursor-pointer disabled:opacity-60 whitespace-nowrap"
            :disabled="loading"
            @click="submit"
          >
            {{ loading ? t('aiConfig.saving') : t('aiConfig.save_key') }}
          </button>

          <button
            v-if="configured"
            class="px-5 py-2 bg-red-800 text-white rounded-lg hover:bg-red-900 transition cursor-pointer disabled:opacity-60 whitespace-nowrap"
            :disabled="loading"
            @click="clearConfig"
          >
            {{ loading ? t('aiConfig.removing') : t('aiConfig.remove_config') }}
          </button>
        </div>

        <p v-if="configured" class="text-sm text-gray-600">{{ t('aiConfig.configured_usage') }}</p>
      </div>

      <div v-if="errorMessage" class="p-4 bg-red-50 text-red-700 rounded-md">{{ errorMessage }}</div>
      <div v-if="successMessage" class="p-4 bg-green-50 text-green-700 rounded-md">{{ successMessage }}</div>
    </div>
  </div>
</template>
