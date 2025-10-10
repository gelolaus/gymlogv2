import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import ErrorBoundaryClass from './components/ErrorBoundaryClass.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <ErrorBoundaryClass>
        <App />
      </ErrorBoundaryClass>
    </BrowserRouter>
  </React.StrictMode>,
)
