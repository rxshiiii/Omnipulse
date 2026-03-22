function AgentQueue({ queue = [], activeCustomerId, onSelect }) {
  return (
    <div className="bg-white border rounded-lg p-4">
      <h3 className="font-semibold text-gray-800 mb-3">Queue (urgent first)</h3>
      <div className="space-y-2 max-h-72 overflow-auto">
        {queue.map((item) => {
          const tone = item.frustration_score > 7 ? 'border-red-300' : item.frustration_score > 4 ? 'border-amber-300' : 'border-gray-200'
          return (
            <button
              key={item.id}
              onClick={() => onSelect(item.id)}
              className={`w-full text-left border rounded-md p-3 ${tone} ${activeCustomerId === item.id ? 'bg-blue-50' : 'bg-white'}`}
            >
              <div className="flex justify-between text-sm">
                <span className="font-medium">{item.name || 'Customer'}</span>
                <span className="text-xs text-gray-500">{item.wait_minutes}m</span>
              </div>
              <p className="text-xs text-gray-600 mt-1">{item.issue_summary}</p>
              <p className="text-xs mt-1 text-gray-500">Frustration {item.frustration_score?.toFixed(1)}</p>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default AgentQueue
