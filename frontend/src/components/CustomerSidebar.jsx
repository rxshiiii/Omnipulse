import ChannelBadge from './ChannelBadge'
import ComplianceChecks from './ComplianceChecks'
import FrustrationMeter from './FrustrationMeter'

function CustomerSidebar({ customer }) {
  if (!customer) {
    return <div className="bg-white rounded-lg border p-4 text-sm text-gray-500">Select a customer.</div>
  }

  const attrs = customer.attributes || {}
  const checks = customer.compliance_summary?.[0] || {}

  return (
    <div className="bg-white rounded-lg border p-4 space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900">{customer.name}</h3>
        <p className="text-xs text-gray-500">Account #{customer.id?.slice(0, 8)}</p>
      </div>

      <div className="flex items-center gap-2">
        <span className={`text-xs px-2 py-1 rounded-full ${attrs.kcc_status === 'blocked' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
          KCC {attrs.kcc_status === 'blocked' ? 'BLOCKED' : 'ACTIVE'}
        </span>
      </div>

      <p className="text-sm text-gray-600">Loan stage: {attrs.loan_stage || 'N/A'}</p>
      <FrustrationMeter score={customer.frustration_score || 0} />

      <div>
        <span className={`text-xs px-2 py-1 rounded-full ${customer.exit_risk === 'high' ? 'bg-red-100 text-red-700' : customer.exit_risk === 'medium' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}`}>
          Exit risk: {customer.exit_risk}
        </span>
      </div>

      <div>
        <p className="text-xs text-gray-500 mb-2">Active channels</p>
        <div className="flex flex-wrap gap-2">
          {(customer.active_channels || []).map((ch) => (
            <ChannelBadge key={ch} channel={ch} />
          ))}
        </div>
      </div>

      <div>
        <p className="text-xs text-gray-500 mb-2">Dead channels</p>
        <div className="space-y-1">
          {(customer.dead_channels || []).map((d) => (
            <p key={`${d.channel}-${d.buried_at}`} className="text-xs text-gray-400 line-through">{d.channel}</p>
          ))}
        </div>
      </div>

      <div>
        <p className="text-xs text-gray-500 mb-2">Compliance checks</p>
        <ComplianceChecks checks={checks} />
      </div>
    </div>
  )
}

export default CustomerSidebar
