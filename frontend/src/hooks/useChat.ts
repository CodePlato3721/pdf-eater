import { useCallback, useEffect, useState } from 'react'
import { askQuestion, clearHistory, getHistory, type HistoryPair } from '../api/chat'

export const ASK_FAILED_MESSAGE = 'Could not get an answer. Please try again.'
export const CLEAR_FAILED_MESSAGE = 'Could not clear the history. Please try again.'

export interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
}

export interface UseChatResult {
  messages: ChatMessage[]
  thinking: boolean
  askError: string | null
  ask: (question: string) => Promise<void>
  clearChat: () => Promise<void>
}

function toMessages(history: HistoryPair[]): ChatMessage[] {
  return history.flatMap(([question, answer]) => [
    { role: 'user' as const, text: question },
    { role: 'assistant' as const, text: answer },
  ])
}

export function useChat(): UseChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [thinking, setThinking] = useState(false)
  const [askError, setAskError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getHistory()
      .then((history) => {
        if (!cancelled) {
          // The user may have asked before the history arrived — never
          // overwrite messages that are already on screen.
          setMessages((prev) => (prev.length > 0 ? prev : toMessages(history)))
        }
      })
      .catch(() => {
        // Backend unreachable on load — start with an empty conversation.
      })
    return () => {
      cancelled = true
    }
  }, [])

  const ask = useCallback(async (question: string) => {
    const trimmed = question.trim()
    if (trimmed === '') {
      return
    }
    setThinking(true)
    setAskError(null)
    setMessages((prev) => [...prev, { role: 'user', text: trimmed }])
    try {
      const answer = await askQuestion(trimmed)
      setMessages((prev) => [...prev, { role: 'assistant', text: answer }])
    } catch (error) {
      setAskError(error instanceof Error ? error.message : ASK_FAILED_MESSAGE)
    } finally {
      setThinking(false)
    }
  }, [])

  const clearChat = useCallback(async () => {
    try {
      await clearHistory()
      setMessages([])
      setAskError(null)
    } catch (error) {
      setAskError(error instanceof Error ? error.message : CLEAR_FAILED_MESSAGE)
    }
  }, [])

  return { messages, thinking, askError, ask, clearChat }
}
