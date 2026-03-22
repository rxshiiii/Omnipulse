function FrustrationMeter({ score = 0 }) {
  const pct = Math.min(100, Math.max(0, score * 10))
  const color = score > 7 ? 'bg-ubRed' : score > 4 ? 'bg-ubAmber' : 'bg-ubGreen'

  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>Frustration</span>
        <span>{score.toFixed(1)}/10</span>
      </div>
      <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default FrustrationMeter
