import { type RouteRecordRaw } from 'vue-router'

import { routes as projetoRoute } from './Projeto'
import { routes as moduloRoute } from './Modulo'
import { routes as documentoRoute } from './Documento'
import { routes as aiConfigRoute } from './AIConfig'


export const routes: RouteRecordRaw[] = [
  ...projetoRoute,
  ...moduloRoute,
  ...documentoRoute,
  ...aiConfigRoute,

]