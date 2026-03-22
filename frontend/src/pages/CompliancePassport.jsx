import { useState } from 'react'
import { useQuery } from 'react-query'
import toast from 'react-hot-toast'
import { endpoints } from '../api/client'
import StatCard from '../components/StatCard'

const BANK_ID = process.env.REACT_APP_BANK_ID || 'union_bank_demo'

function CompliancePassport() {
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')

  const passportQuery = useQuery(['passport', BANK_ID, fromDate, toDate], () =>
    endpoints.getPassport(BANK_ID, { from_date: fromDate || undefined, to_date: toDate || undefined, format: 'json' })
  )

  const statsQuery = useQuery(['compliance-stats', BANK_ID], () => endpoints.getComplianceStats(BANK_ID))

  const records = passportQuery.data?.data?.records || []
  const stats = statsQuery.data?.data || {}

  const exportCsv = async () => {
    const res = await endpoints.getPassport(BANK_ID, {
      from_date: fromDate || undefined,
      to_date: toDate || undefined,
      format: 'csv',
    })
    const blob = new Blob([res.data], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `compliance_passport_${BANK_ID}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const verifyToken = async (token) => {
    try {
      const res = await endpoints.verifyAuditToken(token)
      toast.success(res.data.valid ? 'Hash chain valid' : 'Hash chain mismatch')
    } catch {
      toast.error('Failed to verify token')
    }
  }

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div className="flex flex-wrap gap-2 items-end">
        <div>
          <label className="text-xs text-gray-500">From</label>
          <input className="block border rounded-md px-2 py-1" type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
        </div>
        <div>
          <label className="text-xs text-gray-500">To</label>
          <input className="block border rounded-md px-2 py-1" type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
        </div>
        <button className="bg-ubBlue text-white px-3 py-2 rounded-md text-sm" onClick={() => passportQuery.refetch()}>
          Apply
        </button>
        <button className="border border-gray-300 px-3 py-2 rounded-md text-sm" onClick={exportCsv}>
          Export CSV
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <StatCard title="Total checked" value={records.length} />
        <StatCard title="Pass rate" value={`${stats.pass_rate || 0}%`} />
        <StatCard title="Violations prevented" value={stats.violations_prevented || 0} />
        <StatCard title="DNC blocked" value={stats.dnc_blocked || 0} />
      </div>

      <div className="bg-white border rounded-lg overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
            <tr>
              <th className="px-3 py-2 text-left">Audit Token</th>
              <th className="px-3 py-2 text-left">Customer</th>
              <th className="px-3 py-2 text-left">Channel</th>
              <th className="px-3 py-2 text-left">DNC</th>
              <th className="px-3 py-2 text-left">Consent</th>
              <th className="px-3 py-2 text-left">RBI</th>
              <th className="px-3 py-2 text-left">Tone</th>
              <th className="px-3 py-2 text-left">Safety</th>
              <th className="px-3 py-2 text-left">Result</th>
              <th className="px-3 py-2 text-left">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={r.audit_token} className="border-t">
                <td className="px-3 py-2 text-blue-700 cursor-pointer" onClick={() => verifyToken(r.audit_token)}>
                  {r.audit_token}
                </td>
                <td className="px-3 py-2">{r.customer}</td>
                <td className="px-3 py-2">{r.channel}</td>
                <td className="px-3 py-2">{r.dnc}</td>
                <td className="px-3 py-2">{String(r.consent)}</td>
                <td className="px-3 py-2">{String(r.rbi)}</td>
                <td className="px-3 py-2">{String(r.tone)}</td>
                <td className="px-3 py-2">{String(r.safety)}</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-1 rounded-full text-xs ${r.result === 'PASS' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {r.result}
                  </span>
                </td>
                <td className="px-3 py-2 text-xs">{new Date(r.timestamp).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default CompliancePassport
