import adminApi from '@/api/admin'
import type { UserAIConfig, UserAIConfigUpdateReq } from '../types/aiConfig'

const aiConfigUrl = 'classes/ai-config/'

export const getUserAIConfig = async () => {
  return await adminApi.get<UserAIConfig>(aiConfigUrl)
}

export const saveUserAIConfig = async (payload: UserAIConfigUpdateReq) => {
  return await adminApi.put<UserAIConfig>(aiConfigUrl, payload)
}

export const deleteUserAIConfig = async () => {
  return await adminApi.delete<void>(aiConfigUrl)
}
