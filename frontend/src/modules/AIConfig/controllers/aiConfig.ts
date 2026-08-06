import { getUserAIConfig, saveUserAIConfig, deleteUserAIConfig } from '../api/aiConfig'
import type { UserAIConfigUpdateReq } from '../types/aiConfig'

export const loadUserAIConfig = async () => {
  const response = await getUserAIConfig()
  return response.data
}

export const updateUserAIConfig = async (payload: UserAIConfigUpdateReq) => {
  const response = await saveUserAIConfig(payload)
  return response.data
}

export const removeUserAIConfig = async () => {
  await deleteUserAIConfig()
}
