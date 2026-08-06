export type UserAIConfig = {
  provider: 'openai' | 'gemini'
  configured: boolean
  masked_key: string | null
}

export type UserAIConfigUpdateReq = {
  provider?: string
  api_key?: string
}
