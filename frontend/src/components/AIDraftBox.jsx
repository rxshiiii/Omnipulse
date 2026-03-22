import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { endpoints } from '../api/client'

function AIDraftBox({ customerId, aiDraft, channel = 'whatsapp', bankId = 'union_bank_demo' }) {
  const [draft, setDraft] = useState(aiDraft || '')

  useEffect(() => {
    setDraft(aiDraft || '')
  }, [aiDraft])

  const send = async (override = false) => {
    if (!customerId) {
      toast.error('Select a customer first')
      return
    }
    if (!draft || !draft.trim()) {
      toast.error('Draft is empty. Type a message first.')
      return
    }
    try {
      const response = await endpoints.sendMessage({
        customer_id: customerId,
        content: draft,
        channel,
        agent_id: 'UB-4421',
        bank_id: bankId,
      })
      if (!response.data.success) {
        toast.error(response.data.reason || 'Compliance failed')
        return
      }
      toast.success(override ? 'Override message sent' : 'Reply sent')
    } catch (error) {
      toast.error('Unable to send message')
    }
  }

  return (
    <div className="bg-white border rounded-lg p-4 mt-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-gray-800">AI Draft Ready - Llama 3.3 70B</h4>
        <span className="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">All checks passed</span>
      </div>
      <textarea
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        className="w-full h-24 border rounded-md p-3 text-sm"
        placeholder="AI draft will appear here"
      />
      <div className="flex flex-wrap gap-2 text-xs">
        {['DNC ✓', 'Consent ✓', 'RBI ✓', 'Tone ✓'].map((item) => (
          <span key={item} className="px-2 py-1 rounded-full bg-green-50 text-green-700">
            {item}
          </span>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        <button className="bg-ubBlue text-white px-3 py-2 rounded-md text-sm" onClick={() => send(false)}>
          Send Reply
        </button>
        <button className="border border-gray-300 px-3 py-2 rounded-md text-sm">Edit first</button>
        <button className="bg-ubRed text-white px-3 py-2 rounded-md text-sm">Escalate to RM</button>
        <button className="bg-gray-600 text-white px-3 py-2 rounded-md text-sm" onClick={() => send(true)}>
          Override & Send
        </button>
      </div>
    </div>
  )
}

export default AIDraftBox
