import type { RouteRecordRaw } from 'vue-router'
import Configurar from '../views/Configurar.vue'

export const routes: RouteRecordRaw[] = [
  {
    name: 'ai-config',
    path: '',
    component: Configurar,
    meta: { requiresAuth: true }
  }
]
