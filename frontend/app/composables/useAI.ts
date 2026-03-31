export function useAI() {
  const api = useApi()

  async function classifyTransaction(description: string, amount: number) {
    return api.post<{
      category: string
      btw_percentage: number
      type: string
      confidence_score: number
      explanation: string
    }>('/ai/classify', { description, amount })
  }

  async function chat(message: string) {
    return api.post<{ reply: string }>('/ai/chat', { message })
  }

  async function getInsights() {
    return api.get<Array<{
      title: string
      description: string
      type: string
      priority: string
    }>>('/ai/insights')
  }

  return { classifyTransaction, chat, getInsights }
}
