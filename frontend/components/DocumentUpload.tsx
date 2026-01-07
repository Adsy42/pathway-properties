'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Upload, File, Loader2, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { uploadDocument, listPropertyDocuments, DOCUMENT_TYPES, DocumentResponse } from '@/lib/api'

interface DocumentUploadProps {
  propertyId: string
  onComplete?: () => void
}

export function DocumentUpload({ propertyId, onComplete }: DocumentUploadProps) {
  const [selectedType, setSelectedType] = useState(DOCUMENT_TYPES[0].value)
  const queryClient = useQueryClient()

  // Fetch existing documents
  const { data: documents = [], isLoading: loadingDocs } = useQuery({
    queryKey: ['documents', propertyId],
    queryFn: () => listPropertyDocuments(propertyId),
    refetchInterval: (query) => {
      // Refetch every 2s if any document is processing
      const docs = query.state.data as DocumentResponse[] | undefined
      if (docs?.some(d => d.status === 'processing' || d.status === 'pending')) {
        return 2000
      }
      return false
    },
  })

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(propertyId, file, selectedType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', propertyId] })
    },
  })

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles[0]) {
        uploadMutation.mutate(acceptedFiles[0])
      }
    },
    [uploadMutation]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    disabled: uploadMutation.isPending,
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'processing':
      case 'pending':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
        return <Badge variant="success">Ready</Badge>
      case 'processing':
        return <Badge variant="secondary">Processing...</Badge>
      case 'pending':
        return <Badge variant="secondary">Pending</Badge>
      case 'error':
        return <Badge variant="destructive">Error</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const readyCount = documents.filter(d => d.status === 'ready').length

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Upload Documents</span>
          {readyCount > 0 && (
            <Badge variant="success">{readyCount} ready</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Document Type Selector */}
        <div>
          <label className="text-sm font-medium mb-2 block">Document Type</label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            {DOCUMENT_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'}
            ${uploadMutation.isPending ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />
          <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
          {uploadMutation.isPending ? (
            <div className="flex items-center justify-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Uploading...</span>
            </div>
          ) : isDragActive ? (
            <p>Drop the file here...</p>
          ) : (
            <div>
              <p className="font-medium">Drop file here or click to browse</p>
              <p className="text-sm text-muted-foreground mt-1">
                PDF and Word documents (.doc, .docx)
              </p>
            </div>
          )}
        </div>

        {uploadMutation.isError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            Upload failed: {(uploadMutation.error as Error).message}
          </div>
        )}

        {/* Document List */}
        {documents.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Uploaded Documents</h4>
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  {getStatusIcon(doc.status)}
                  <div>
                    <p className="font-medium text-sm">{doc.document_type}</p>
                    {doc.page_count && (
                      <p className="text-xs text-muted-foreground">
                        {doc.page_count} pages
                      </p>
                    )}
                  </div>
                </div>
                {getStatusBadge(doc.status)}
              </div>
            ))}
          </div>
        )}

        {/* Continue Button */}
        {readyCount > 0 && onComplete && (
          <Button onClick={onComplete} className="w-full">
            Continue to Analysis ({readyCount} documents)
          </Button>
        )}
      </CardContent>
    </Card>
  )
}




