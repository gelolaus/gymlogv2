import React from 'react'
import { Link } from 'react-router-dom'

export default class ErrorBoundaryClass extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    // You could also log to an external service here
    // console.error('Uncaught error:', error, info)
  }

  render() {
    if (this.state.hasError) {
      const { error } = this.state
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
            {error ? String(error) : 'No details available.'}
          </details>
        </div>
      )
    }

    return this.props.children
  }
}
