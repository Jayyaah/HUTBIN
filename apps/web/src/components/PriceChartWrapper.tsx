'use client'
import { Line } from 'react-chartjs-2'
import {
  Chart, CategoryScale, LinearScale, PointElement,
  LineElement, Tooltip, Filler,
} from 'chart.js'
import { PriceEntry } from '@/lib/api'

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler)

export function PriceChartWrapper({ data }: { data: PriceEntry[] }) {
  return (
    <Line
      data={{
        labels: data.map(d => new Date(d.recordedAt).toLocaleDateString('fr-CA', { month: 'short', day: 'numeric' })),
        datasets: [{
          label: 'Prix moyen',
          data: data.map(d => d.priceAvg),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59,130,246,0.08)',
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6,
        }],
      }}
      options={{
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: {
            ticks: { color: '#6b7280', callback: v => `${Number(v) >= 1000 ? `${(Number(v)/1000).toFixed(0)}K` : v}` },
            grid: { color: 'rgba(255,255,255,0.05)' },
          },
          x: { ticks: { color: '#6b7280' }, grid: { display: false } },
        },
      }}
    />
  )
}
