<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

const auth = useAuthStore()
const { locale } = useI18n()
const router = useRouter()

function changeLanguage(lang: string) {
  locale.value = lang
  localStorage.setItem('language', lang)
}

function goToAIConfig() {
  router.push({ name: 'ai-config' })
}

const sair = async () => {
  await auth.logout()
  router.push('/')
}
</script>

<template>
  <div class="flex flex-row w-full min-h-screen overflow-x-hidden">
    <nav class="fixed top-0 left-0 w-full h-14 bg-blue-800 border-b-2 border-blue-1000 flex items-center justify-between px-4 z-50 text-white">
      <!-- Nome do projeto -->
      <span class="text-lg font-semibold">
        RequirementsAI
      </span>
      <!-- Botões -->
        <div class="flex items-center">
        <!-- Botões de Idioma -->
        <div>
          <p-button class="bg-blue-950 mr-2 hover:bg-blue-500 transition cursor-pointer" @click="changeLanguage('en')">EN</p-button>
          <p-button class="bg-blue-950 mr-4 hover:bg-blue-500 transition cursor-pointer" @click="changeLanguage('pt')">PT</p-button>
        </div>
        <!-- Botão de configuração de API Key, visível apenas quando usuário logado -->
        <p-button
          v-if="auth.accessToken"
          class="min-w-[110px] min-h-[40px] whitespace-nowrap bg-blue-950 hover:bg-blue-500 transition cursor-pointer mr-4"
          @click="goToAIConfig"
        >
          {{ $t('navigation.api_key') }}
        </p-button>

        <p-button v-if="auth.accessToken" class="min-w-[110px] min-h-[40px] whitespace-nowrap bg-blue-950 hover:bg-blue-500 transition cursor-pointer" @click="sair"> {{ $t('navigation.logout') }} </p-button>
      </div>
    </nav>
    <main class="flex justify-center items-start w-full pt-10 px-4">
      <div class="w-full max-w-[1600px]">
        <router-view />
      </div>
    </main>
  </div>
</template>