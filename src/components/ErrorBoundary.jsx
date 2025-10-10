import React from 'react'
import { useRouteError, Link } from 'react-router-dom'

export default function ErrorBoundary(props) {
  // Prefer router-provided error via hook; fall back to prop if present
  const routeError = useRouteError()
  const error = routeError || props.error

  const renderDetails = () => {
    if (!error) return 'No details available.'

    // If the router returned a Response-like error (404, etc.)
    if (error.status) {
      const parts = [`Status: ${error.status} ${error.statusText || ''}`]
      if (error.data) parts.push(JSON.stringify(error.data, null, 2))
      if (error.statusText && !error.data && error.message) parts.push(error.message)
      return parts.join('\n\n')
    }

    if (error.message) return error.message
    return String(error)
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>Unexpected Application Error</h1>
      <p>Sorry — something went wrong while loading this page.</p>

      <div style={{ marginTop: 12 }}>
        <button onClick={() => window.location.reload()} style={{ marginRight: 8 }}>
          Reload
        </button>
        <Link to="/">Go home</Link>
      </div>

      <details style={{ whiteSpace: 'pre-wrap', marginTop: 10 }}>
        {renderDetails()}
      </details>
    </div>
  )
}
