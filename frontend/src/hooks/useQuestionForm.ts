import { useCallback, useState, type ChangeEvent, type FormEvent } from 'react'

export interface UseQuestionFormResult {
  question: string
  onQuestionChange: (event: ChangeEvent<HTMLInputElement>) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}

export function useQuestionForm(
  onAsk: (question: string) => void,
): UseQuestionFormResult {
  const [question, setQuestion] = useState('')

  const onQuestionChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setQuestion(event.target.value)
  }, [])

  const onSubmit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      const trimmed = question.trim()
      if (trimmed === '') {
        return
      }
      setQuestion('')
      onAsk(trimmed)
    },
    [question, onAsk],
  )

  return { question, onQuestionChange, onSubmit }
}
