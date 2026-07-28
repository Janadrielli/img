/**
 * Serviço de API REST para comunicação com o backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export const api = {
  // Dashboard
  getStats: () => request<import('../types').DashboardStats>('/dashboard/stats'),
  getIncidents: () => request<import('../types').Incident[]>('/dashboard/incidents'),

  // Drivers
  getDrivers: (activeOnly = false) =>
    request<import('../types').Driver[]>(`/drivers/?active_only=${activeOnly}`),
  updateDriverLocation: (id: string, lat: number, lng: number) =>
    request(`/drivers/${id}/location`, {
      method: 'PATCH',
      body: JSON.stringify({ lat, lng }),
    }),

  // Deliveries
  getDeliveries: (status?: string, priority?: string) => {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    if (priority) params.set('priority', priority);
    return request<import('../types').Delivery[]>(`/deliveries/?${params}`);
  },
  updateDelivery: (id: string, data: Record<string, unknown>) =>
    request(`/deliveries/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  confirmDelivery: (id: string, data: { receiver_name: string; notes?: string; lat: number; lng: number }) =>
    request(`/deliveries/${id}/confirm`, { method: 'POST', body: JSON.stringify(data) }),

  // Routes
  getRoutes: (activeOnly = true) =>
    request<import('../types').Route[]>(`/routes/?active_only=${activeOnly}`),
  getDriverActiveRoute: (driverId: string) =>
    request<import('../types').Route>(`/routes/driver/${driverId}/active`),
  optimizeRoute: (driverId: string, deliveryIds?: string[]) =>
    request<import('../types').Route>('/routes/optimize', {
      method: 'POST',
      body: JSON.stringify({ driver_id: driverId, delivery_ids: deliveryIds }),
    }),
  overridePriority: (routeId: string, orderedIds: string[], reason: string) =>
    request(`/routes/${routeId}/override-priority`, {
      method: 'POST',
      body: JSON.stringify({ delivery_ids_ordered: orderedIds, reason }),
    }),
};
