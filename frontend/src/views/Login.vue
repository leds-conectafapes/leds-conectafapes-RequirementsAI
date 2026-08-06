<script setup lang="ts">
import { ref, inject, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { chaveModal } from '@/types/ui'
import {
  campoNecessario,
  minimo3caracteres,
  caracteresEspeciais
} from '@/utils/regras'

const router = useRouter()
const auth = useAuthStore()
const { locale } = useI18n()

function changeLanguage(lang: string) {
  locale.value = lang
  localStorage.setItem('language', lang)
}

// Modal
const modal = inject(chaveModal)
const esqueciSenha = () => {
  modal?.abrirModal("Não implementado.")
}

// Estados
const usuario = ref('')
const senha = ref('')
const erro = ref('')
const loading = ref(false)

// Regras
const regrasUsuario = [campoNecessario, minimo3caracteres]
const regrasSenha = [campoNecessario, minimo3caracteres, caracteresEspeciais]

// Validação
const usuarioValido = ref(false)
const senhaValida = ref(false)

const updateUsuarioValido = (novoValor: boolean) => {
  usuarioValido.value = novoValor
}

const updateSenhaValida = (novoValor: boolean) => {
  senhaValida.value = novoValor
}

const podeEntrar = computed(() => {
  return usuarioValido.value && senhaValida.value && !loading.value
})

// Login
const entrar = async () => {
  try {
    loading.value = true
    erro.value = ''

    await auth.login(usuario.value, senha.value)

    // Redireciona para página principal
    router.push({ name: 'projeto-home' })
  } catch (e) {
    erro.value = 'Invalid username or password.'

  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="absolute top-4 right-4">
    <button 
      class="px-5 py-2 mr-2 bg-blue-800 text-white rounded-lg 
                  hover:bg-blue-900 transition cursor-pointer"
      @click="changeLanguage('en')"
    >
      EN
    </button>
    <button
      class="px-5 py-2 bg-blue-800 text-white rounded-lg 
                  hover:bg-blue-900 transition cursor-pointer"
      @click="changeLanguage('pt')"
    >
      PT
    </button>
  </div>

  <div class="flex flex-col items-center justify-center min-h-screen">
    
    <!-- Título -->
    <div class="text-[60px] text-blue-800 font-bold mb-10">
      <h1>RequirementsAI</h1>
    </div>

    <!-- Card -->
    <card class="w-md p-6">
      
      <text-input
        class="w-full mb-4"
        placeholder=""
        v-model="usuario"
        @keyup-enter="entrar"
      >
        {{ $t('login.username')}}
      </text-input>

      <text-input
        class="w-full mb-4"
        v-model="senha"
        @keyup-enter="entrar"
        type="password"
      >
        {{ $t('login.password')}}
      </text-input>

      <!-- Erro -->
      <p v-if="erro" class="text-red-500 text-sm mb-3">
        {{ erro }}
      </p>

      <!-- Botão -->
      <div class="flex justify-between items-center">
        <div>
          <button
            class="text-sm text-blue-700 hover:underline transition cursor-pointer mr-4"
            @click="$router.push({ name: 'register' })"
          >
            {{ $t('register.button') }}
          </button>

      
          <!-- <button
            class="text-sm text-blue-700 hover:underline transition cursor-pointer"
            @click="esqueciSenha"
          >
            {{ $t('login.forgot')}}
          </button> -->
        </div> 

        <button
          class="px-5 py-2 bg-blue-800 text-white rounded-lg 
                 hover:bg-blue-900 transition cursor-pointer"
          @click="entrar"
        >
          <span v-if="!loading">{{ $t('login.button')}}</span>
          <span v-else>{{ $t('login.loading') }}</span>
        </button>
      </div>

    </card>
  </div>
</template>