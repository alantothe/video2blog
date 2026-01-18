import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  clearDatabase,
  fetchDebug,
  fetchResult,
  fetchStatus,
  resultDownloadUrl,
  uploadCsv
} from './api'
import type { StatusResponse } from '@shared/types'

const STAGE_ORDER = [
  'stage_0',
  'stage_1',
  'complete'
]

const STAGE_LABELS: Record<string, string> = {
  stage_0: 'Stage 0: CSV received',
  stage_1: 'Stage 1: Transcript cleaned',
  complete: 'Complete'
}

function stageProgress(stage: string): number {
  const index = STAGE_ORDER.indexOf(stage)
  if (index === -1) {
    return 0
  }
  return Math.min(100, Math.round((index / (STAGE_ORDER.length - 1)) * 100))
}

function StatusPanel({ status }: { status: StatusResponse }) {
  const progress = stageProgress(status.stage)
  const stageLabel = STAGE_LABELS[status.stage] ?? status.stage.replace(/_/g, ' ').toUpperCase()
  const stageOneState =
    status.state === 'completed'
      ? 'done'
      : status.stage === 'stage_1' && status.state === 'running'
        ? 'running'
        : 'pending'
  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Pipeline status</p>
          <h2>{stageLabel}</h2>
          <p className={`status ${status.state}`}>{status.state}</p>
        </div>
        <div className="progress">
          <div className="progress-bar" style={{ width: `${progress}%` }} />
        </div>
      </div>
      <div className="panel-body">
        <p>Last update: {new Date(status.updated_at).toLocaleString()}</p>
        {status.error ? <p className="error">{status.error}</p> : null}
        <div className="stage-checklist">
          <div className={`stage-item ${stageOneState}`}>
            <span className="stage-dot" />
            <span>Transcript extracted</span>
          </div>
          <div className={`stage-item ${stageOneState}`}>
            <span className="stage-dot" />
            <span>AI cleaned transcript</span>
          </div>
        </div>
        {status.evaluation_metrics ? (
          <div className="metrics">
            {Object.entries(status.evaluation_metrics).map(([key, value]) => (
              <div key={key} className="metric">
                <span>{key}</span>
                <strong>{value.toFixed(3)}</strong>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  )
}

export default function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [runIds, setRunIds] = useState<string[]>([])
  const [activeRunId, setActiveRunId] = useState<string | null>(null)
  const [showDebug, setShowDebug] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)

  const uploadMutation = useMutation({
    mutationFn: uploadCsv,
    onSuccess: (data) => {
      const ids = data.run_ids ?? (data.run_id ? [data.run_id] : [])
      setRunIds(ids)
      setActiveRunId(ids[0] ?? null)
    }
  })

  const clearMutation = useMutation({
    mutationFn: clearDatabase,
    onSuccess: () => {
      setRunIds([])
      setActiveRunId(null)
      setSelectedFile(null)
    }
  })

  const statusQuery = useQuery({
    queryKey: ['status', activeRunId],
    queryFn: () => fetchStatus(activeRunId as string),
    enabled: Boolean(activeRunId),
    refetchInterval: (query) => {
      const current = query.state.data as StatusResponse | undefined
      if (!current) {
        return 2000
      }
      return current.state === 'completed' || current.state === 'failed' ? false : 2000
    }
  })

  const resultQuery = useQuery({
    queryKey: ['result', activeRunId],
    queryFn: () => fetchResult(activeRunId as string),
    enabled: statusQuery.data?.state === 'completed'
  })

  const debugQuery = useQuery({
    queryKey: ['debug', activeRunId],
    queryFn: () => fetchDebug(activeRunId as string),
    enabled: Boolean(activeRunId) && showDebug
  })

  const markdown = resultQuery.data?.markdown ?? ''

  const activeStatus = statusQuery.data

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!selectedFile) {
      return
    }
    uploadMutation.mutate(selectedFile)
  }

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragOver(false)

    const files = Array.from(event.dataTransfer.files)
    const csvFile = files.find(file => file.type === 'text/csv' || file.name.toLowerCase().endsWith('.csv'))

    if (csvFile) {
      setSelectedFile(csvFile)
    }
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const activeBadge = useMemo(() => {
    if (!activeRunId) {
      return 'Awaiting upload'
    }
    return `Active run: ${activeRunId}`
  }, [activeRunId])

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">AI Pipeline Studio</p>
          <h1>Transform raw video transcripts into clean, ready-to-use drafts.</h1>
          <p className="lede">
            Upload a CSV, watch the transcript cleanup, and download the cleaned output for stage 2.
          </p>
        </div>
        <div className="badge">{activeBadge}</div>
      </header>

      <main className="layout">
        <section className="panel upload">
          <div className="panel-header">
            <h2>Upload CSV</h2>
            <p>Each row becomes a dedicated pipeline run.</p>
          </div>
          <form className="panel-body" onSubmit={handleSubmit}>
            <div
              className={`file-input ${isDragOver ? 'drag-over' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById('csv-file-input')?.click()}
            >
              <input
                id="csv-file-input"
                type="file"
                accept=".csv"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
              <span>
                {selectedFile
                  ? selectedFile.name
                  : isDragOver
                    ? 'Drop CSV file here'
                    : 'Choose a CSV file or drag and drop'
                }
              </span>
            </div>
            <div className="button-row">
              <button type="submit" disabled={!selectedFile || uploadMutation.isPending}>
                {uploadMutation.isPending ? 'Uploading...' : 'Start pipeline'}
              </button>
              <button
                type="button"
                className="clear-btn"
                onClick={() => clearMutation.mutate()}
                disabled={clearMutation.isPending}
              >
                {clearMutation.isPending ? 'Clearing...' : 'Clear DB'}
              </button>
            </div>
            {uploadMutation.isError ? (
              <p className="error">Upload failed. Check the backend logs.</p>
            ) : null}
            {clearMutation.isSuccess ? (
              <p className="success">Database cleared!</p>
            ) : null}
            {runIds.length > 1 ? (
              <div className="run-list">
                {runIds.map((runId) => (
                  <button
                    type="button"
                    key={runId}
                    className={runId === activeRunId ? 'run active' : 'run'}
                    onClick={() => setActiveRunId(runId)}
                  >
                    {runId}
                  </button>
                ))}
              </div>
            ) : null}
          </form>
        </section>

        {activeStatus ? (
          <section>
            <StatusPanel status={activeStatus} />
          </section>
        ) : (
          <section className="panel empty">
            <h2>No run yet</h2>
            <p>Upload a CSV to initialize the pipeline.</p>
          </section>
        )}

        <section className="panel result">
          <div className="panel-header">
            <h2>Cleaned transcript</h2>
            <p>Markdown-ready transcript output for the next stage.</p>
          </div>
          <div className="panel-body">
            {resultQuery.isFetching ? <p>Cleaning transcript...</p> : null}
            {resultQuery.data ? (
              <>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
                {activeRunId ? (
                  <a className="download" href={resultDownloadUrl(activeRunId)}>
                    Download transcript
                  </a>
                ) : null}
              </>
            ) : (
              <p className="placeholder">No transcript yet. Finish Stage 1 to see results.</p>
            )}
          </div>
        </section>

        {activeRunId ? (
          <section className="panel debug">
            <div className="panel-header">
              <h2>Debug View</h2>
              <button
                type="button"
                className="toggle-btn"
                onClick={() => setShowDebug(!showDebug)}
              >
                {showDebug ? 'Hide' : 'Show'} Stage Data
              </button>
            </div>
            {showDebug && debugQuery.data ? (
              <div className="panel-body debug-content">
                <div className="stage-box">
                  <h3>Stage 0: Raw Input</h3>
                  <pre>{JSON.stringify((debugQuery.data.stages as Record<string, {data?: unknown}>)?.stage_0?.data ?? {}, null, 2)}</pre>
                </div>
                <div className="stage-box">
                  <h3>Stage 1: Transcript cleaned</h3>
                  <pre>{JSON.stringify((debugQuery.data.stages as Record<string, {data?: unknown}>)?.stage_1?.data ?? {}, null, 2)}</pre>
                </div>
              </div>
            ) : showDebug ? (
              <div className="panel-body">
                <p>Loading debug data...</p>
              </div>
            ) : null}
          </section>
        ) : null}
      </main>
    </div>
  )
}
