/**
 * Utilitários gerais.
 */

export function formatDistance(km: number): string {
  if (km < 1) return `${Math.round(km * 1000)}m`;
  return `${km.toFixed(1)}km`;
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${Math.round(minutes)}min`;
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  return `${h}h${m > 0 ? `${m}min` : ''}`;
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: 'Pendente',
    assigned: 'Atribuída',
    en_route: 'Em Rota',
    arrived: 'No Local',
    delivered: 'Entregue',
    confirmed: 'Confirmada',
    failed: 'Falhou',
    cancelled: 'Cancelada',
  };
  return labels[status] || status;
}
