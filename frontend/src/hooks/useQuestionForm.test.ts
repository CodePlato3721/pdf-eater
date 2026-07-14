import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { ChangeEvent, FormEvent } from 'react'
import { useQuestionForm } from './useQuestionForm'

function changeEvent(value: string): ChangeEvent<HTMLInputElement> {
  return { target: { value } } as ChangeEvent<HTMLInputElement>
}

function submitEvent(): FormEvent<HTMLFormElement> {
  return { preventDefault: () => {} } as FormEvent<HTMLFormElement>
}

describe('useQuestionForm', () => {
  it('tracks the question text as the user types', () => {
    const { result } = renderHook(() => useQuestionForm(() => {}))

    act(() => {
      result.current.onQuestionChange(changeEvent('Where does Jo first appear?'))
    })

    expect(result.current.question).toBe('Where does Jo first appear?')
  })

  it('submits the trimmed question and clears the input', () => {
    const asked: string[] = []
    const { result } = renderHook(() => useQuestionForm((q) => asked.push(q)))

    act(() => {
      result.current.onQuestionChange(changeEvent('  Where does Jo first appear?  '))
    })
    act(() => {
      result.current.onSubmit(submitEvent())
    })

    expect(asked).toEqual(['Where does Jo first appear?'])
    expect(result.current.question).toBe('')
  })

  it('ignores a blank submission', () => {
    const asked: string[] = []
    const { result } = renderHook(() => useQuestionForm((q) => asked.push(q)))

    act(() => {
      result.current.onQuestionChange(changeEvent('   '))
    })
    act(() => {
      result.current.onSubmit(submitEvent())
    })

    expect(asked).toEqual([])
    expect(result.current.question).toBe('   ')
  })
})
