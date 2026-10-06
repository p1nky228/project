import { Table, Tag, Spin } from 'antd'
import { useTasks } from '../../hooks/useTasks'
import { formatRelativeTime, formatTaskStatus, formatTaskType } from '../../utils/formatters'

export function RecentActivity() {
  const { data, isLoading } = useTasks({ page: 1, page_size: 10 })

  const columns = [
    {
      title: 'Task',
      key: 'title',
      dataIndex: 'title',
      render: (text: string, record: any) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <div style={{ fontSize: 12, color: '#999' }}>
            {record.apparatus?.serial_number || 'Unknown Apparatus'}
          </div>
        </div>
      ),
    },
    {
      title: 'Type',
      key: 'type',
      dataIndex: 'type',
      render: (text: string) => <Tag>{formatTaskType(text)}</Tag>,
    },
    {
      title: 'Status',
      key: 'status',
      dataIndex: 'status',
      render: (text: string) => <Tag color={getStatusColor(text)}>{formatTaskStatus(text)}</Tag>,
    },
    {
      title: 'Technician',
      key: 'technician',
      dataIndex: 'technician',
      render: (technician: any) => technician?.full_name || 'Unassigned',
    },
    {
      title: 'Scheduled',
      key: 'scheduled_at',
      dataIndex: 'scheduled_at',
      render: (text: string) => formatRelativeTime(text),
    },
  ]

  if (isLoading) {
    return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', padding: 32 }} />
  }

  return (
    <Table
      columns={columns}
      dataSource={data?.items || []}
      pagination={false}
      rowKey="id"
      size="middle"
      bordered
    />
  )
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'success'
    case 'in_progress':
      return 'blue'
    case 'assigned':
      return 'cyan'
    case 'pending':
      return 'gold'
    case 'rejected':
    case 'cancelled':
      return 'red'
    default:
      return 'default'
  }
}