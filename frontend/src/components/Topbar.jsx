import { useDashboardStore } from '../store/dashboardStore'

function Topbar() {
  const wsConnected = useDashboardStore((s) => s.wsConnected)
  const urgentCount = useDashboardStore((s) => s.urgentCount)

  return (
    <header className="w-full bg-ubBlue text-white px-4 py-3 shadow-sm">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div className="font-semibold tracking-wide">OmniPulse | Union Bank Agent Dashboard</div>
        <div className="flex items-center gap-2 text-sm">
          <span className="opacity-80">WebSocket</span>
          <span className={`px-2 py-1 rounded-full text-xs ${wsConnected ? 'bg-ubGreen' : 'bg-ubRed'}`}>
            {wsConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span>Priya Sharma</span>
          <span className="bg-ubRed px-2 py-1 rounded-full text-xs font-semibold">{urgentCount} urgent</span>
        </div>
      </div>
    </header>
  )
}

export default Topbar
