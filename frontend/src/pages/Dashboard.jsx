import { useEffect, useMemo, useState } from 'react'
import { useQuery } from 'react-query'
import { connectWebSocket, endpoints } from '../api/client'
import AgentQueue from '../components/AgentQueue'
import AIDraftBox from '../components/AIDraftBox'
import ConversationThread from '../components/ConversationThread'
import CustomerSidebar from '../components/CustomerSidebar'
import LoanJourneyTimeline from '../components/LoanJourneyTimeline'
import { useDashboardStore } from '../store/dashboardStore'

const BANK_ID = process.env.REACT_APP_BANK_ID || 'union_bank_demo'

function Dashboard() {
  const [wsRef, setWsRef] = useState(null)
  const setQueue = useDashboardStore((s) => s.setQueue)
  const queue = useDashboardStore((s) => s.queue)
  const activeCustomerId = useDashboardStore((s) => s.activeCustomerId)
  const setActiveCustomer = useDashboardStore((s) => s.setActiveCustomer)
  const setWsConnected = useDashboardStore((s) => s.setWsConnected)
  const setUrgentCount = useDashboardStore((s) => s.setUrgentCount)

  const queueQuery = useQuery(['queue', BANK_ID], () => endpoints.getQueue(BANK_ID), {
    refetchInterval: 15000,
  })

  useEffect(() => {
    const items = queueQuery.data?.data?.items || []
    setQueue(items)
    setUrgentCount(items.filter((q) => q.frustration_score > 7).length)
    if (!activeCustomerId && items[0]) setActiveCustomer(items[0].id)
  }, [queueQuery.data, activeCustomerId, setActiveCustomer, setQueue, setUrgentCount])

  const customerQuery = useQuery(
    ['customer', activeCustomerId],
    () => endpoints.getCustomer(activeCustomerId, BANK_ID),
    { enabled: !!activeCustomerId }
  )

  const threadQuery = useQuery(
    ['thread', activeCustomerId],
    () => endpoints.getThread(activeCustomerId, BANK_ID),
    { enabled: !!activeCustomerId, refetchInterval: 10000 }
  )

  useEffect(() => {
    const ws = connectWebSocket('UB-4421', () => {
      queueQuery.refetch()
      threadQuery.refetch()
    })
    ws.onopen = () => setWsConnected(true)
    ws.onclose = () => setWsConnected(false)
    setWsRef(ws)

    return () => {
      ws.close()
    }
  }, [])

  const profile = useMemo(() => {
    const payload = customerQuery.data?.data
    if (!payload) return null
    return {
      ...payload.profile,
      active_channels: payload.active_channels,
      dead_channels: payload.dead_channels,
      compliance_summary: payload.compliance_summary,
    }
  }, [customerQuery.data])

  const messages = threadQuery.data?.data?.messages || []
  const latestDraft = [...messages].reverse().find((m) => m.ai_draft)?.ai_draft || ''

  return (
    <div className="p-3 md:p-5">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <section className="lg:col-span-3">
          <CustomerSidebar customer={profile} />
        </section>

        <section className="lg:col-span-6">
          <ConversationThread messages={messages} />
          <AIDraftBox customerId={activeCustomerId} aiDraft={latestDraft} bankId={BANK_ID} channel={profile?.preferred_channel || 'whatsapp'} />
        </section>

        <section className="lg:col-span-3">
          <AgentQueue queue={queue} activeCustomerId={activeCustomerId} onSelect={setActiveCustomer} />
          <LoanJourneyTimeline journey={customerQuery.data?.data?.loan_journey || []} />
        </section>
      </div>
    </div>
  )
}

export default Dashboard
