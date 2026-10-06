import { Row, Col, Card, Statistic, Spin, Divider } from 'antd'
import { useStats } from '../hooks/useStats'
import { TaskStatusChart } from '../components/charts/TaskStatusChart'
import { TechnicianRatingChart } from '../components/charts/TechnicianRatingChart'
import { RecentActivity } from '../components/tables/RecentActivity'

export default function Dashboard() {
  const { data: stats, isLoading, error } = useStats()

  if (isLoading) {
    return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', padding: 48 }} />
  }

  if (error) {
    return (
      <Card style={{ maxWidth: 600, margin: '48px auto' }}>
        <p style={{ color: '#f5222d' }}>Failed to load dashboard stats</p>
      </Card>
    )
  }

  const statCards = [
    { title: 'Total Tasks', value: stats?.total_tasks || 0, prefix: null },
    { title: 'Pending Tasks', value: stats?.pending_tasks || 0, prefix: null },
    { title: 'In Progress', value: stats?.in_progress_tasks || 0, prefix: null },
    { title: 'Completed Today', value: stats?.completed_today || 0, prefix: null },
    { title: 'Total Technicians', value: stats?.total_technicians || 0, prefix: null },
    { title: 'Active Technicians', value: stats?.active_technicians || 0, prefix: null },
    { title: 'Total Apparatuses', value: stats?.total_apparatuses || 0, prefix: null },
    { title: 'Operational', value: stats?.operational_apparatuses || 0, prefix: null },
  ]

  return (
    <div>
      <Row gutter={[24, 16]} style={{ marginBottom: 24 }}>
        {statCards.map((stat, index) => (
          <Col key={index} xs={24} sm={12} md={6} lg={3}>
            <Card>
              <Statistic title={stat.title} value={stat.value} />
            </Card>
          </Col>
        ))}
      </Row>

      <Divider style={{ marginBottom: 24 }} />

      <Row gutter={[24, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Task Status Distribution">
            <TaskStatusChart stats={stats} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Technician Ratings">
            <TechnicianRatingChart stats={stats} />
          </Card>
        </Col>
      </Row>

      <Card title="Recent Activity">
        <RecentActivity />
      </Card>
    </div>
  )
}