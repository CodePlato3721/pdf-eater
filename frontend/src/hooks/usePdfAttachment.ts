import { useCallback, useRef, type ChangeEvent } from 'react'

export interface UsePdfAttachmentResult {
  inputRef: React.RefObject<HTMLInputElement>
  openPicker: () => void
  onFilesSelected: (event: ChangeEvent<HTMLInputElement>) => void
}

export function usePdfAttachment(
  onUpload: (files: File[]) => void,
): UsePdfAttachmentResult {
  const inputRef = useRef<HTMLInputElement>(null)

  const openPicker = useCallback(() => {
    inputRef.current?.click()
  }, [])

  const onFilesSelected = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const selected = Array.from(event.target.files ?? [])
      // Reset so selecting the same file again re-triggers the change event.
      event.target.value = ''
      if (selected.length > 0) {
        onUpload(selected)
      }
    },
    [onUpload],
  )

  return { inputRef, openPicker, onFilesSelected }
}
