import { useEffect, useRef, useState } from 'react'
import './App.css'

type RuntimeInfo = {
  runtime: string
  available: boolean
  time: number | null
  error: string | null
}

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [transcript, setTranscript] = useState<
    { start: number; text: string }[]
  >([])

  const [runtime, setRuntime] = useState('')
  const [runtimes, setRuntimes] = useState<RuntimeInfo[]>([])
  const [isDetectingRuntimes, setIsDetectingRuntimes] = useState(true)
  const [isCopied, setIsCopied] = useState(false)
  const [transcriptionError, setTranscriptionError] = useState('')

  const fileInputRef = useRef<HTMLInputElement>(null)

  const runtimeLabels: Record<string, string> = {
    cuda: 'NVIDIA GPU',
    vulkan: 'Vulkan GPU',
    cpu: 'CPU',
  }

  useEffect(() => {
    async function initializeRuntime() {
      try {
        const [runtimesResponse, settingsResponse] = await Promise.all([
          fetch('http://127.0.0.1:8000/runtimes'),
          fetch('http://127.0.0.1:8000/settings/runtime'),
        ])

        const runtimesData = await runtimesResponse.json()
        const settingsData = await settingsResponse.json()

        const detectedRuntimes: RuntimeInfo[] = runtimesData.runtimes

        setRuntimes(detectedRuntimes)

        const availableRuntimes = detectedRuntimes.filter(
          (item) => item.available && item.time !== null
        )

        const fastestRuntime = [...availableRuntimes].sort(
          (a, b) => (a.time ?? Infinity) - (b.time ?? Infinity)
        )[0]

        const savedRuntime = settingsData.runtime

        const savedRuntimeIsAvailable = detectedRuntimes.some(
          (item) =>
            item.runtime === savedRuntime && item.available
        )

        if (savedRuntimeIsAvailable) {
          setRuntime(savedRuntime)
        } else if (fastestRuntime) {
          setRuntime(fastestRuntime.runtime)
        }
      } catch (error) {
        console.error('Runtime initialization failed:', error)
      } finally {
        setIsDetectingRuntimes(false)
      }
    }

    initializeRuntime()
  }, [])

  const fastestRuntime = runtimes
    .filter((item) => item.available && item.time !== null)
    .sort((a, b) => (a.time ?? Infinity) - (b.time ?? Infinity))[0]

  const selectedRuntime = runtimes.find(
    (item) => item.runtime === runtime
  )

  async function copyTranscript() {
    if (transcript.length === 0) return

    const text = transcript
      .map((segment) => {
        return `${segment.start.toFixed(2)}\t${segment.text}`
      })
      .join('\n')

    try {
      await navigator.clipboard.writeText(text)

      setIsCopied(true)

      setTimeout(() => {
        setIsCopied(false)
      }, 1500)
    } catch (error) {
      console.error('Failed to copy transcript:', error)
    }
  }

  return (
    <main className="app">
      <header className="app-header">
        <h1>Nemo Note</h1>
      </header>

      <div className="workspace">
        <section className="audio-section">
          <div className="section-heading">
            <p>Choose an audio file to transcribe.</p>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept=".wav,audio/wav,audio/x-wav"
            hidden
            onChange={(event) => {
              const selectedFile = event.target.files?.[0]

              if (selectedFile) {
                setFile(selectedFile)
              }
            }}
          />

          <button
            className="browse-button"
            onClick={() => fileInputRef.current?.click()}
          >
            Browse files
          </button>

          {file && (
            <div className="selected-file">
              <span className="selected-file-label">Selected</span>
              <span className="selected-file-name">
                {file.name}
              </span>
            </div>
          )}
        </section>

        <section className="runtime-section">
          <div className="runtime-heading">
            <h2>Processing engine</h2>

            {!isDetectingRuntimes && fastestRuntime && (
              <span className="fastest-runtime">
                Fastest available: {runtimeLabels[fastestRuntime.runtime]}
              </span>
            )}
          </div>

          {isDetectingRuntimes ? (
            <div className="runtime-loading">
              Checking available processing options...
            </div>
          ) : (
            <>
              <select
                className="runtime-select"
                value={runtime}
                onChange={async (event) => {
                  const selectedRuntime = event.target.value

                  setRuntime(selectedRuntime)

                  try {
                    const formData = new FormData()
                    formData.append('runtime', selectedRuntime)

                    await fetch(
                      'http://127.0.0.1:8000/settings/runtime',
                      {
                        method: 'POST',
                        body: formData,
                      }
                    )
                  } catch (error) {
                    console.error(
                      'Failed to save runtime preference:',
                      error
                    )
                  }
                }}
              >
                {runtimes.map((item) => (
                  <option
                    key={item.runtime}
                    value={item.runtime}
                    disabled={!item.available}
                  >
                    {runtimeLabels[item.runtime] ?? item.runtime}
                    {!item.available ? ' — Not available' : ''}
                  </option>
                ))}
              </select>

              {!isDetectingRuntimes &&
                selectedRuntime &&
                fastestRuntime &&
                selectedRuntime.runtime !== fastestRuntime.runtime && (
                  <p className="runtime-note">
                    Your selected engine will be used for transcription.
                  </p>
                )}
            </>
          )}
        </section>

        <div className="transcribe-action">
          <button
            className="transcribe-button"
            disabled={!file || isTranscribing || !runtime}
            onClick={async () => {
              if (!file) return

              setIsTranscribing(true)
              setTranscript([])
              setTranscriptionError('')

              const formData = new FormData()
              formData.append('file', file)
              formData.append('runtime', runtime)

              try {
                const response = await fetch(
                  'http://127.0.0.1:8000/transcribe',
                  {
                    method: 'POST',
                    body: formData,
                  }
                )

                const data = await response.json()

                console.log('Transcription response:', data)

                if (!response.ok || data.error) {
                  console.error('Transcription failed:', data.error)

                  setTranscriptionError(
                    data.error?.includes('ErrorOutOfDeviceMemory')
                      ? 'The selected processing engine ran out of GPU memory while processing this audio. Try another engine'
                      : 'The transcription could not be completed. Please try again.'
                  )

                  return
                }

                setTranscript(data.transcription.segments)

              } catch (error) {
                console.error('Transcription failed:', error)

                setTranscriptionError(
                  'Could not connect to the transcription service. Please try again.'
                )
              } finally {
                setIsTranscribing(false)
              }
            }}
          >
            {isTranscribing ? 'Transcribing...' : 'Transcribe'}
          </button>
        </div>
        {transcriptionError && (
          <p className="transcription-error">
            {transcriptionError}
          </p>
        )}


        <section className="transcript-section">
          <div className="transcript">
            <button
              className="copy-button"
              disabled={transcript.length === 0}
              onClick={copyTranscript}
              aria-label={
                isCopied
                  ? 'Transcript copied'
                  : 'Copy transcript'
              }
              title={
                isCopied
                  ? 'Copied'
                  : 'Copy transcript'
              }
            >
              {isCopied ? (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M20 6 9 17l-5-5" />
                </svg>
              ) : (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <rect
                    width="8"
                    height="4"
                    x="8"
                    y="2"
                    rx="1"
                    ry="1"
                  />
                  <path d="M8 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
                  <path d="M16 4h2a2 2 0 0 1 2 2v4" />
                  <path d="M21 14H11" />
                  <path d="m15 10-4 4 4 4" />
                </svg>
              )}
            </button>

            <div className="transcript-content">
              {transcript.length === 0 ? (
                <div className="transcript-empty">
                  No transcription yet.
                </div>
              ) : (
                transcript.map((segment, index) => (
                  <div
                    className="transcript-row"
                    key={index}
                  >
                    <span className="transcript-time">
                      {segment.start.toFixed(2)}
                    </span>

                    <span className="transcript-text">
                      {segment.text}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>




      </div>
    </main>
  )
}

export default App

