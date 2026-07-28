/**
 * Zustand store global para estado da aplicação.
 */
import { create } from 'zustand';
import type { Driver, Delivery, Route, Incident, DashboardStats } from '../types';

interface AppState {
  // Data
  drivers: Driver[];
  deliveries: Delivery[];
  routes: Route[];
  incidents: Incident[];
  stats: DashboardStats | null;

  // UI
  selectedDriverId: string | null;
  selectedDeliveryId: string | null;
  sidebarOpen: boolean;

  // Actions
  setDrivers: (drivers: Driver[]) => void;
  setDeliveries: (deliveries: Delivery[]) => void;
  setRoutes: (routes: Route[]) => void;
  setIncidents: (incidents: Incident[]) => void;
  setStats: (stats: DashboardStats) => void;
  updateDriverLocation: (id: string, lat: number, lng: number) => void;
  updateDeliveryStatus: (id: string, status: Delivery['status']) => void;
  selectDriver: (id: string | null) => void;
  selectDelivery: (id: string | null) => void;
  toggleSidebar: () => void;
}

export const useStore = create<AppState>((set) => ({
  drivers: [],
  deliveries: [],
  routes: [],
  incidents: [],
  stats: null,
  selectedDriverId: null,
  selectedDeliveryId: null,
  sidebarOpen: true,

  setDrivers: (drivers) => set({ drivers }),
  setDeliveries: (deliveries) => set({ deliveries }),
  setRoutes: (routes) => set({ routes }),
  setIncidents: (incidents) => set({ incidents }),
  setStats: (stats) => set({ stats }),

  updateDriverLocation: (id, lat, lng) =>
    set((state) => ({
      drivers: state.drivers.map((d) =>
        d.id === id ? { ...d, current_lat: lat, current_lng: lng } : d
      ),
    })),

  updateDeliveryStatus: (id, status) =>
    set((state) => ({
      deliveries: state.deliveries.map((d) =>
        d.id === id ? { ...d, status } : d
      ),
    })),

  selectDriver: (id) => set({ selectedDriverId: id }),
  selectDelivery: (id) => set({ selectedDeliveryId: id }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}));
