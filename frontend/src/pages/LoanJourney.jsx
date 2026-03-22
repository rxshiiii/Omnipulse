import { useParams } from 'react-router-dom'
import { useQuery } from 'react-query'
import { endpoints } from '../api/client'

const BANK_ID = process.env.REACT_APP_BANK_ID || 'union_bank_demo'

function statusTone(status) {
  if (status === 'complete') return 'bg-green-100 text-green-700'
  if (status === 'issue') return 'bg-red-100 text-red-700'
  return 'bg-gray-100 text-gray-600'
}

function LoanJourney() {
  const { customerId } = useParams()

  const customerQuery = useQuery(['loan-customer', customerId], () => endpoints.getCustomer(customerId, BANK_ID), {
    enabled: !!customerId,
  })

  const threadQuery = useQuery(['loan-thread', customerId], () => endpoints.getThread(customerId, BANK_ID), {
    enabled: !!customerId,
  })

  const journey = customerQuery.data?.data?.loan_journey || []
  const messages = threadQuery.data?.data?.messages || []

  return (
    <div className="p-4 md:p-6">
      <h1 className="text-2xl font-semibold text-gray-900 mb-4">Loan Journey Timeline</h1>
      <div className="space-y-4">
        {journey.map((step) => (
          <div key={step.id} className="bg-white border rounded-lg p-4">
            <div className="flex flex-wrap gap-2 items-center justify-between">
              <h3 className="font-semibold text-gray-800">{step.stage}</h3>
              <span className={`text-xs px-2 py-1 rounded-full ${statusTone(step.status)}`}>{step.status}</span>
            </div>
            <p className="text-sm text-gray-600 mt-2">Department: {step.department}</p>
            <p className="text-sm text-gray-600">Agent: {step.agent_id || 'UB-4421'}</p>
            <p className="text-sm text-gray-600">Action: {step.action_taken}</p>
            <p className="text-sm text-gray-600">Notes: {step.notes}</p>
            <p className="text-xs text-gray-400 mt-1">{new Date(step.created_at).toLocaleString()}</p>

            <div className="mt-3 border-t pt-3 space-y-2">
              <p className="text-xs font-medium text-gray-500 uppercase">Related messages</p>
              {messages.slice(0, 3).map((msg) => (
                <div key={msg.id} className="bg-gray-50 rounded-md p-2">
                  <p className="text-xs text-gray-500">{msg.channel} · {msg.direction}</p>
                  <p className="text-sm text-gray-700">{msg.translated_content || msg.content}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default LoanJourney
