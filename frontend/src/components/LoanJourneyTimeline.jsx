const steps = ['Application', 'KYC', 'Legal', 'Valuation', 'Sanctioning', 'Disbursement']

function dotColor(status) {
  if (status === 'complete') return 'bg-green-500'
  if (status === 'issue') return 'bg-red-500'
  return 'bg-gray-300'
}

function LoanJourneyTimeline({ journey = [] }) {
  const stageMap = Object.fromEntries(journey.map((j) => [j.stage, j]))

  return (
    <div className="bg-white border rounded-lg p-4 mt-4">
      <h3 className="font-semibold text-gray-800 mb-3">Loan Journey</h3>
      <div className="space-y-3">
        {steps.map((step) => {
          const item = stageMap[step] || {}
          return (
            <div key={step} className="flex gap-3 items-start">
              <div className={`w-3 h-3 mt-1 rounded-full ${dotColor(item.status)}`} />
              <div>
                <p className="text-sm font-medium text-gray-700">{step}</p>
                <p className="text-xs text-gray-500">{item.department || 'Pending'} · {item.status || 'pending'}</p>
                <p className="text-[10px] text-gray-400">{item.created_at ? new Date(item.created_at).toLocaleString() : ''}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default LoanJourneyTimeline
