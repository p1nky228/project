import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import type { DashboardStats } from '../../api/types'

interface TaskStatusChartProps {
  stats: DashboardStats | undefined
}

const COLORS = ['#52c41a', '#1890ff', '#faad14', '#f5222d', '#722ed1', '#13c2c2']

const statusData = [
  { name: 'Completed', value: 0, color: COLORS[0] },
  { name: 'In Progress', value: 0, color: COLORS[1] },
  { name: 'Pending', value: 0, color: COLORS[2] },
  { name: 'Cancelled', value: 0, color: COLORS[3] },
  { name: 'Rejected', value: 0, color: COLORS[4] },
  { name: 'Assigned', value: 0, color: COLORS[5] },
]

export function TaskStatusChart({ stats }: TaskStatusChartProps) {
  const data = stats
    ? [
        { name: 'Completed', value: stats.total_tasks - (stats.pending_tasks + stats.in_progress_tasks), color: COLORS[0] },
        { name: 'In Progress', value: stats.in_progress_tasks, color: COLORS[1] },
        { name: 'Pending', value: stats.pending_tasks, color: COLORS[2] },
        { name: 'Other', value: Math.max(0, stats.total_tasks - stats.pending_tasks - stats.in_progress_tasks - (stats.total_tasks - stats.pending_tasks - stats.in_progress_tasks)), color: COLORS[3] },
      ]
    : statusData

  const filteredData = data.filter((d) => d.value > 0)

  if (filteredData.length === 0) {
    return (
      <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
        No data available
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={filteredData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          fill="#8884d8"
          paddingAngle={2}
          dataKey="value"
          nameKey="name"
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          labelLine={false}
        >
          {filteredData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip formatter={(value: number) => [value, 'Tasks']} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}