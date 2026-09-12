import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { ApiKeyGate } from './components/ApiKeyGate.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ApiKeyGate>
      <App />
    </ApiKeyGate>
  </StrictMode>,
)
