import ChannelBadge from './ChannelBadge'

function ConversationThread({ messages = [] }) {
  return (
    <div className="bg-white border rounded-lg p-4 h-[420px] overflow-auto space-y-3">
      {messages.map((m) => {
        const isAgent = m.direction === 'outbound'
        const bubbleClass = isAgent
          ? 'ml-auto bg-blue-50 border border-blue-200'
          : 'mr-auto bg-gray-100'

        return (
          <div key={m.id} className={`max-w-[85%] rounded-lg px-3 py-2 ${bubbleClass}`}>
            <div className="flex items-center gap-2 text-[10px] text-gray-500 mb-1">
              <ChannelBadge channel={m.channel} />
              <span>{new Date(m.created_at).toLocaleString()}</span>
              <span>{m.direction}</span>
            </div>
            <p className="text-sm text-gray-700">{m.translated_content || m.content}</p>
            {m.original_language && m.original_language !== 'en' && (
              <p className="text-[10px] mt-1 text-gray-500">Translated from {m.original_language}</p>
            )}
            {m.audio_url && (
              <p className="text-[10px] mt-1 inline-block bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full">
                Transcribed by Whisper · Marathi → English
              </p>
            )}
          </div>
        )
      })}
      <div className="text-center text-xs text-gray-400">AI pipeline status updates appear here in real time.</div>
    </div>
  )
}

export default ConversationThread
