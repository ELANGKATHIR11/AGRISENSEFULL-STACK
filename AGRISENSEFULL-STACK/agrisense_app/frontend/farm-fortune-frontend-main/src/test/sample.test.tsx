/**
 * Sample Unit Test for AgriSense Components
 * Tests the Dashboard component
 */
import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

// Sample test for a simple component
describe('Component Testing', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )

  it('should render without crashing', () => {
    const TestComponent = () => <div>Hello AgriSense</div>
    render(<TestComponent />, { wrapper })
    expect(screen.getByText('Hello AgriSense')).toBeInTheDocument()
  })

  it('should handle API calls correctly', async () => {
    // Mock API call
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'ok' }),
      } as Response)
    )

    // Test component that makes API calls
    const ApiComponent = () => {
      const [status, setStatus] = React.useState('loading')
      
      React.useEffect(() => {
        fetch('/health')
          .then(r => r.json())
          .then(data => setStatus(data.status))
      }, [])

      return <div>Status: {status}</div>
    }

    render(<ApiComponent />, { wrapper })
    
    await waitFor(() => {
      expect(screen.getByText('Status: ok')).toBeInTheDocument()
    })
  })
})

// Add more test files for specific components:
// - Dashboard.test.tsx
// - Chatbot.test.tsx
// - SoilAnalysis.test.tsx
// etc.
