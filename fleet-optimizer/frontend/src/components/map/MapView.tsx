/**
 * Tela de Mapa com localização dos motoristas, rotas e incidentes em tempo real.
 */
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet';
import L from 'leaflet';
import { useStore } from '../../store/useStore';

// Ícones customizados
const driverIcon = (status: string) => L.divIcon({
  className: 'custom-marker',
  html: `<div class="w-8 h-8 rounded-full border-2 border-white shadow-lg flex items-center justify-center text-white text-xs font-bold ${
    status === 'en_route' ? 'bg-blue-600' :
    status === 'delivering' ? 'bg-green-600' :
    'bg-gray-500'
  }">🚛</div>`,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const deliveryIcon = (priority: string, isCompleted: boolean) => L.divIcon({
  className: 'custom-marker',
  html: `<div class="w-6 h-6 rounded-full border-2 border-white shadow flex items-center justify-center text-xs ${
    isCompleted ? 'bg-green-500 text-white' :
    priority === 'critical' ? 'bg-red-500 text-white' :
    priority === 'high' ? 'bg-orange-500 text-white' :
    'bg-blue-500 text-white'
  }">${isCompleted ? '✓' : '📦'}</div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

const incidentIcon = L.divIcon({
  className: 'custom-marker',
  html: '<div class="w-6 h-6 rounded-full bg-red-600 border-2 border-white shadow flex items-center justify-center text-xs">⚠️</div>',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

// Centro padrão (São Paulo)
const DEFAULT_CENTER: [number, number] = [-23.5505, -46.6333];

export default function MapView() {
  const { drivers, deliveries, incidents, routes, selectDriver } = useStore();

  const activeDrivers = drivers.filter(d => d.current_lat && d.current_lng);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Mapa em Tempo Real</h2>
        <div className="flex gap-4 text-sm">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-blue-600" /> Motoristas ({activeDrivers.length})
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-orange-500" /> Entregas
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-red-600" /> Incidentes ({incidents.length})
          </span>
        </div>
      </div>

      <div className="h-[calc(100vh-200px)] rounded-xl overflow-hidden border shadow-sm">
        <MapContainer center={DEFAULT_CENTER} zoom={12} className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Motoristas */}
          {activeDrivers.map((driver) => (
            <Marker
              key={driver.id}
              position={[driver.current_lat!, driver.current_lng!]}
              icon={driverIcon(driver.status)}
              eventHandlers={{ click: () => selectDriver(driver.id) }}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-bold">{driver.name}</p>
                  <p className="text-gray-600">{driver.vehicle_plate} - {driver.vehicle_type}</p>
                  <p className="text-xs mt-1">Status: <span className="font-medium">{driver.status}</span></p>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Entregas */}
          {deliveries
            .filter(d => d.status !== 'cancelled')
            .map((delivery) => (
              <Marker
                key={delivery.id}
                position={[delivery.lat, delivery.lng]}
                icon={deliveryIcon(delivery.priority, delivery.status === 'confirmed')}
              >
                <Popup>
                  <div className="text-sm">
                    <p className="font-bold">{delivery.order_number}</p>
                    <p>{delivery.customer_name}</p>
                    <p className="text-xs text-gray-500">{delivery.address}</p>
                    <p className="mt-1">Prioridade: <span className="font-medium">{delivery.priority}</span></p>
                    <p>Status: {delivery.status}</p>
                    {delivery.sequence_order && <p>Sequência: #{delivery.sequence_order}</p>}
                  </div>
                </Popup>
              </Marker>
            ))}

          {/* Incidentes Waze */}
          {incidents.map((inc) => (
            <Circle
              key={inc.id}
              center={[inc.lat, inc.lng]}
              radius={300 + inc.severity * 100}
              pathOptions={{
                color: 'red',
                fillColor: 'red',
                fillOpacity: 0.15,
                weight: 1,
              }}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-bold text-red-600">{inc.incident_type}</p>
                  <p>Severidade: {inc.severity}/5</p>
                  {inc.street && <p className="text-xs">{inc.street}</p>}
                  {inc.delay_seconds > 0 && (
                    <p className="text-red-600">+{Math.round(inc.delay_seconds / 60)} min</p>
                  )}
                </div>
              </Popup>
            </Circle>
          ))}

          {/* Linhas de rota */}
          {routes.map((route) => {
            const routePoints: [number, number][] = [
              [route.origin_lat, route.origin_lng],
              ...route.stops
                .sort((a, b) => a.sequence_order - b.sequence_order)
                .map((stop) => {
                  const del = deliveries.find(d => d.id === stop.delivery_id);
                  return del ? [del.lat, del.lng] as [number, number] : null;
                })
                .filter((p): p is [number, number] => p !== null),
            ];

            return (
              <Polyline
                key={route.id}
                positions={routePoints}
                pathOptions={{ color: '#2563eb', weight: 3, opacity: 0.7, dashArray: '5 10' }}
              />
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
