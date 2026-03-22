function StatCard({ title, value, hint }) {
  return (
    <div className="bg-white border rounded-lg p-4">
      <p className="text-xs uppercase tracking-wide text-gray-500">{title}</p>
      <p className="text-2xl font-semibold text-gray-900 mt-1">{value}</p>
      {hint && <p className="text-xs text-gray-400 mt-1">{hint}</p>}
    </div>
  )
}

export default StatCard
