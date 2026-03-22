function ComplianceChecks({ checks = {} }) {
  const rows = [
    ['DNC', checks.dnc_checked ?? true],
    ['Consent', checks.consent_valid ?? true],
    ['RBI', checks.rbi_content_passed ?? true],
    ['Tone', checks.tone_fit_passed ?? true],
  ]

  return (
    <div className="space-y-2">
      {rows.map(([label, ok]) => (
        <div key={label} className="flex justify-between text-xs">
          <span className="text-gray-500">{label}</span>
          <span className={ok ? 'text-ubGreen' : 'text-ubRed'}>{ok ? '✓' : '✕'}</span>
        </div>
      ))}
    </div>
  )
}

export default ComplianceChecks
