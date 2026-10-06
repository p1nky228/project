import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { DashboardStats } from '../../api/types'

interface TechnicianRatingChartProps {
  stats: DashboardStats | undefined
}

export function TechnicianRatingChart({ stats }: TechnicianRatingChartProps) {
  const avgRating = stats?.avg_technician_rating || 0

  const data = [
    { name: 'Avg Rating', value: Number(avgRating.toFixed(1)) },
  ]

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" max={5} />
        <YAxis type="category" dataKey="name" width={80} />
        <Tooltip formatter={(value: number) => [value.toFixed(1), 'Rating']} />
        <Legend />
        <Bar dataKey="value" fill="#1890ff" radius={[0, 4, 4, 0]} maxBarSize={50} />
      </BarChart>
    </ResponsiveContainer>
  )
}