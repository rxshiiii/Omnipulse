import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Toaster } from 'react-hot-toast'
import Dashboard from './pages/Dashboard'
import CompliancePassport from './pages/CompliancePassport'
import Analytics from './pages/Analytics'
import LoanJourney from './pages/LoanJourney'
import CustomerProfile from './pages/CustomerProfile'
import Topbar from './components/Topbar'
import Sidebar from './components/Sidebar'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="flex flex-col min-h-screen bg-gray-50">
          <Topbar />
          <div className="flex flex-1 min-h-0">
            <Sidebar />
            <main className="flex-1 overflow-auto">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/customer/:customerId" element={<CustomerProfile />} />
                <Route path="/compliance" element={<CompliancePassport />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/loan-journey/:customerId" element={<LoanJourney />} />
              </Routes>
            </main>
          </div>
        </div>
        <Toaster position="top-right" />
      </Router>
    </QueryClientProvider>
  )
}

export default App
