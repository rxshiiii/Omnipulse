function colorFor(channel) {
  const c = (channel || '').toLowerCase()
  if (c === 'whatsapp') return 'bg-green-100 text-green-700'
  if (c === 'sms') return 'bg-blue-100 text-blue-700'
  if (c === 'email') return 'bg-amber-100 text-amber-700'
  if (c === 'voice') return 'bg-purple-100 text-purple-700'
  return 'bg-gray-100 text-gray-600'
}

function ChannelBadge({ channel }) {
  return <span className={`text-[10px] px-2 py-1 rounded-full uppercase ${colorFor(channel)}`}>{channel}</span>
}

export default ChannelBadge
