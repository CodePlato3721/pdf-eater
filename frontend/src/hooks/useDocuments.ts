import { useCallback, useEffect, useState } from 'react'
import { getStatus, uploadPdfs } from '../api/documents'

export const UPLOAD_FAILED_MESSAGE = 'Upload failed. Please try again.'

export interface UseDocumentsResult {
  files: string[]
  uploading: boolean
  uploadError: string | null
  uploadFiles: (selected: File[]) => Promise<void>
}

export function useDocuments(): UseDocumentsResult {
  const [files, setFiles] = useState<string[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getStatus()
      .then((status) => {
        if (!cancelled) {
          setFiles(status.files)
        }
      })
      .catch(() => {
        // Backend unreachable on load — leave the sidebar empty.
      })
    return () => {
      cancelled = true
    }
  }, [])

  const uploadFiles = useCallback(async (selected: File[]) => {
    if (selected.length === 0) {
      return
    }
    setUploading(true)
    setUploadError(null)
    try {
      const status = await uploadPdfs(selected)
      setFiles(status.files)
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : UPLOAD_FAILED_MESSAGE)
    } finally {
      setUploading(false)
    }
  }, [])

  return { files, uploading, uploadError, uploadFiles }
}
