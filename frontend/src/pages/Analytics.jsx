import { useQuery } from 'react-query'
import { Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Cell } from 'recharts'
import { endpoints } from '../api/client'
import StatCard from '../components/StatCard'

const BANK_ID = process.env.REACT_APP_BANK_ID || 'union_bank_demo'
const COLORS = ['#1B4FAD', '#1D9E75', '#BA7517', '#C8102E']

function Analytics() {
  const cost = useQuery(['cost', BANK_ID], () => endpoints.getAnalytics(BANK_ID))
  const attr = useQuery(['attr', BANK_ID], () => endpoints.getAttribution(BANK_ID))
  const exits = useQuery(['exits', BANK_ID], () => endpoints.getFrustrationExits(BANK_ID))
  const perf = useQuery(['perf', BANK_ID], () => endpoints.getChannelPerformance(BANK_ID))

  const costData = cost.data?.data || {}
  const exitData = exits.data?.data || {}
  const perfData = perf.data?.data || {}
  const attribution = attr.data?.data?.items || []

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <StatCard title="INR saved total" value={`₹${costData.cost_saved_inr || 0}`} />
        <StatCard title="Agent time saved" value={`${costData.agent_minutes_saved || 0} min`} />
        <StatCard title="Frustrated exits caught" value={exitData.proactive_outreach_count || 0} />
        <StatCard title="Compliance violations prevented" value={perfData.compliance_violations_prevented || 0} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white border rounded-lg p-3 h-80">
          <h3 className="font-semibold text-sm text-gray-700 mb-2">Channel attribution</h3>
          <ResponsiveContainer width="100%" height="90%">
            <PieChart>
              <Pie data={attribution} dataKey="weight_percentage" nameKey="channel" outerRadius={110} label>
                {attribution.map((entry, idx) => (
                  <Cell key={entry.channel} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white border rounded-lg p-3 h-80">
          <h3 className="font-semibold text-sm text-gray-700 mb-2">Frustration trend (30d)</h3>
          <ResponsiveContainer width="100%" height="90%">
            <LineChart data={perfData.frustration_trend || []}>
              <XAxis dataKey="date" />
              <YAxis domain={[0, 10]} />
              <Tooltip />
              <Line type="monotone" dataKey="score" stroke="#C8102E" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white border rounded-lg overflow-auto">
        <div className="px-4 py-3 border-b">
          <h3 className="font-semibold text-sm text-gray-700">Dead channels</h3>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
            <tr>
              <th className="px-3 py-2 text-left">Customer</th>
              <th className="px-3 py-2 text-left">Channel</th>
              <th className="px-3 py-2 text-left">Buried on</th>
              <th className="px-3 py-2 text-left">Inactive days</th>
              <th className="px-3 py-2 text-left">Reason</th>
            </tr>
          </thead>
          <tbody>
            {(perfData.dead_channels || []).map((d, idx) => (
              <tr key={`${d.channel}-${idx}`} className="border-t">
                <td className="px-3 py-2">{d.customer || 'N/A'}</td>
                <td className="px-3 py-2">{d.channel}</td>
                <td className="px-3 py-2">{d.buried_at ? new Date(d.buried_at).toLocaleDateString() : 'N/A'}</td>
                <td className="px-3 py-2">{d.inactive_days || 0}</td>
                <td className="px-3 py-2">{d.reason || 'Inactive'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Analytics
