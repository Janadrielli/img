export type DeliveryStatus =
  | 'pending' | 'assigned' | 'en_route' | 'arrived'
  | 'delivered' | 'confirmed' | 'failed' | 'cancelled';

export type DeliveryPriority = 'critical' | 'high' | 'normal' | 'low';

export type DriverStatus =
  | 'available' | 'en_route' | 'delivering'
  | 'returning' | 'offline' | 'break';

export interface Driver {
  id: string;
  name: string;
  phone: string;
  vehicle_plate: string;
  vehicle_type: string;
  status: DriverStatus;
  current_lat: number | null;
  current_lng: number | null;
  last_location_update: string | null;
  is_active: boolean;
  max_deliveries: number;
}

export interface Delivery {
  id: string;
  order_number: string;
  customer_name: string;
  customer_phone: string | null;
  description: string | null;
  address: string;
  lat: number;
  lng: number;
  weight_kg: number;
  priority: DeliveryPriority;
  priority_score: number;
  status: DeliveryStatus;
  sequence_order: number | null;
  estimated_arrival: string | null;
  confirmed_at: string | null;
  receiver_name: string | null;
  time_window_start: string | null;
  time_window_end: string | null;
  created_at: string;
}

export interface RouteStop {
  id: string;
  delivery_id: string;
  sequence_order: number;
  distance_from_previous_km: number;
  duration_from_previous_min: number;
  eta: string | null;
  is_completed: boolean;
  has_active_incident: boolean;
  waze_incidents_on_path: number;
}

export interface Route {
  id: string;
  driver_id: string;
  status: string;
  origin_lat: number;
  origin_lng: number;
  total_distance_km: number;
  total_duration_minutes: number;
  total_stops: number;
  completed_stops: number;
  optimization_score: number;
  stops: RouteStop[];
  created_at: string;
}

export interface Incident {
  id: string;
  lat: number;
  lng: number;
  incident_type: string;
  severity: number;
  description: string | null;
  delay_seconds: number;
  street: string | null;
  is_active: boolean;
  reported_at: string;
}

export interface DashboardStats {
  total_drivers: number;
  active_drivers: number;
  total_deliveries_today: number;
  pending_deliveries: number;
  in_progress_deliveries: number;
  completed_deliveries: number;
  active_incidents: number;
  avg_eta_minutes: number;
}

export interface WSMessage {
  channel: string;
  data: Record<string, unknown>;
  timestamp: string;
}
