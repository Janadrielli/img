import { useStore } from '../../store/useStore';

const priorityColors = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  normal: 'bg-blue-100 text-blue-800 border-blue-200',
  low: 'bg-gray-100 text-gray-800 border-gray-200',
};

export default function Dashboard() {
  const { stats, deliveries, drivers, incidents } = useStore();

  const statCards = [
    { label: 'Motoristas Ativos', value: stats?.active_drivers ?? 0, total: stats?.total_drivers ?? 0, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Entregas Pendentes', value: stats?.pending_deliveries ?? 0, color: 'text-orange-600', bg: 'bg-orange-50' },
    { label: 'Em Progresso', value: stats?.in_progress_deliveries ?? 0, color: 'text-yellow-600', bg: 'bg-yellow-50' },
    { label: 'Concluídas Hoje', value: stats?.completed_deliveries ?? 0, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Incidentes Ativos', value: stats?.active_incidents ?? 0, color: 'text-red-600', bg: 'bg-red-50' },
  ];

  const recentDeliveries = deliveries
    .filter(d => d.status !== 'confirmed' && d.status !== 'cancelled')
    .slice(0, 10);

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {statCards.map((card) => (
          <div key={card.label} className={`${card.bg} rounded-xl p-4 border`}>
            <p className="text-sm text-gray-600">{card.label}</p>
            <p className={`text-2xl font-bold ${card.color}`}>
              {card.value}
              {card.total !== undefined && (
                <span className="text-sm font-normal text-gray-500">/{card.total}</span>
              )}
            </p>
          </div>
        ))}
      </div>

      {/* Active Deliveries */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4">Entregas Ativas</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left">Pedido</th>
                <th className="px-4 py-2 text-left">Cliente</th>
                <th className="px-4 py-2 text-left">Endereço</th>
                <th className="px-4 py-2 text-center">Prioridade</th>
                <th className="px-4 py-2 text-center">Status</th>
                <th className="px-4 py-2 text-center">Sequência</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {recentDeliveries.map((d) => (
                <tr key={d.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 font-mono text-xs">{d.order_number}</td>
                  <td className="px-4 py-2">{d.customer_name}</td>
                  <td className="px-4 py-2 max-w-[200px] truncate">{d.address}</td>
                  <td className="px-4 py-2 text-center">
                    <span className={`px-2 py-0.5 rounded-full text-xs border ${priorityColors[d.priority]}`}>
                      {d.priority}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-center">
                    <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100">{d.status}</span>
                  </td>
                  <td className="px-4 py-2 text-center">{d.sequence_order ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Active Incidents */}
      {incidents.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4 text-red-600">Incidentes Ativos (Waze)</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {incidents.slice(0, 6).map((inc) => (
              <div key={inc.id} className="flex items-start gap-3 p-3 bg-red-50 rounded-lg border border-red-100">
                <span className="text-lg">
                  {inc.incident_type === 'accident' ? '🚗' :
                   inc.incident_type === 'jam' ? '🚦' :
                   inc.incident_type === 'road_closed' ? '🚧' : '⚠️'}
                </span>
                <div>
                  <p className="font-medium text-sm">{inc.incident_type} - Severidade {inc.severity}/5</p>
                  <p className="text-xs text-gray-600">{inc.street ?? 'Localização desconhecida'}</p>
                  {inc.delay_seconds > 0 && (
                    <p className="text-xs text-red-600">+{Math.round(inc.delay_seconds / 60)} min de atraso</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
