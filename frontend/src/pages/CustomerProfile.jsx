import { useParams } from 'react-router-dom'
import { useQuery } from 'react-query'
import { endpoints } from '../api/client'

const BANK_ID = process.env.REACT_APP_BANK_ID || 'union_bank_demo'

function CustomerProfile() {
  const { customerId } = useParams()
  const { data, isLoading } = useQuery(['customer-profile', customerId], () => endpoints.getCustomer(customerId, BANK_ID), {
    enabled: !!customerId,
  })

  if (isLoading) return <div className="p-6">Loading...</div>

  const profile = data?.data?.profile
  if (!profile) return <div className="p-6">Customer not found.</div>

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold text-gray-900">{profile.name}</h1>
      <p className="text-sm text-gray-500">{profile.phone || profile.email}</p>
      <pre className="bg-white border rounded-lg p-4 mt-4 text-xs overflow-auto">
        {JSON.stringify(data.data, null, 2)}
      </pre>
    </div>
  )
}

export default CustomerProfile
