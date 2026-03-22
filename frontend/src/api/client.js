import axios from 'axios'

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL: BASE_URL })

export const connectWebSocket = (agentId, onMessage) => {
  const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000'
  const ws = new WebSocket(`${WS_URL}/api/agents/ws/${agentId}`)
  ws.onmessage = (event) => onMessage(JSON.parse(event.data))
  ws.onopen = () => console.log('WebSocket connected')
  ws.onclose = () => console.log('WebSocket disconnected')
  return ws
}

export const endpoints = {
  getQueue: (bankId) => api.get(`/api/agents/queue?bank_id=${bankId}`),
  getCustomer: (id, bankId) => api.get(`/api/agents/customer/${id}?bank_id=${bankId}`),
  getThread: (id, bankId) => api.get(`/api/agents/customer/${id}/thread?bank_id=${bankId}`),
  sendMessage: (data) => api.post('/api/agents/message/send', data),
  overrideMessage: (id, data) => api.post(`/api/agents/message/${id}/override`, data),
  getPassport: (bankId, params) => api.get(`/api/compliance/passport/${bankId}`, { params }),
  verifyAuditToken: (token) => api.get(`/api/compliance/verify/${token}`),
  getComplianceStats: (bankId) => api.get(`/api/compliance/stats/${bankId}`),
  getAnalytics: (bankId) => api.get(`/api/analytics/cost-savings/${bankId}`),
  getAttribution: (bankId) => api.get(`/api/analytics/attribution/${bankId}`),
  getFrustrationExits: (bankId) => api.get(`/api/analytics/frustration-exits/${bankId}`),
  getChannelPerformance: (bankId) => api.get(`/api/analytics/channel-performance/${bankId}`),
}
