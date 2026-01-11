import { NextResponse } from 'next/server'

export async function POST() {
  try {
    const collectorUrl = process.env.COLLECTOR_URL || 'http://collector:8000'

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 15000)  // 15-second timeout

    const res = await fetch(`${collectorUrl}/stop`, {
      method: 'POST',
      cache: 'no-store',
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    const data = await res.json()

    if (!res.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to stop collection' },
        { status: res.status }
      )
    }

    return NextResponse.json(data)
  } catch (error) {
    // Check if error is due to timeout (AbortError)
    if (error instanceof Error && error.name === 'AbortError') {
      console.warn('Stop request timed out after 15s, but collection may have stopped successfully')

      // Return success since timeout doesn't mean failure
      // The UI will refresh and show the actual state
      return NextResponse.json({
        status: 'stopped',
        message: 'Stop request sent (may take a moment to complete)'
      })
    }

    // Handle other errors normally
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    console.error('API /stop error:', errorMessage)

    return NextResponse.json(
      { error: `Failed to stop collection: ${errorMessage}` },
      { status: 500 }
    )
  }
}
