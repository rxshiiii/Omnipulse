import { create } from 'zustand'

export const useDashboardStore = create((set) => ({
  activeCustomerId: null,
  setActiveCustomer: (id) => set({ activeCustomerId: id }),
  queue: [],
  setQueue: (queue) => set({ queue }),
  wsConnected: false,
  setWsConnected: (v) => set({ wsConnected: v }),
  urgentCount: 0,
  setUrgentCount: (n) => set({ urgentCount: n }),
}))
