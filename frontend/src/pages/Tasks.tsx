import { useState } from 'react'
import { Table, Tag, Button, Space, Form, Input, Select, Card, Popconfirm, message } from 'antd'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons'
import { useTasks } from '../hooks/useTasks'
import { useAcceptTask, useRejectTask } from '../hooks/useTasks'
import type { Task, TaskStatus, TaskType, TaskPriority } from '../api/types'
import { formatTaskStatus, formatTaskType, formatTaskPriority, formatRelativeTime } from '../utils/formatters'

const statusOptions: TaskStatus[] = ['pending', 'assigned', 'in_progress', 'completed', 'cancelled', 'rejected']
const typeOptions: TaskType[] = ['maintenance', 'repair', 'restock', 'inspection', 'emergency']
const priorityOptions: TaskPriority[] = ['low', 'medium', 'high', 'critical']

export default function Tasks() {
  const [filters, setFilters] = useState({
    page: 1,
    page_size: 20,
    status: [] as TaskStatus[],
    type: [] as TaskType[],
    priority: [] as TaskPriority[],
    search: '',
  })
  const [selectedRows, setSelectedRows] = useState<string[]>([])

  const { data, isLoading, refetch } = useTasks(filters)
  const acceptMutation = useAcceptTask()
  const rejectMutation = useRejectTask()

  const columns = [
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      render: (text: string, record: Task) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <div style={{ fontSize: 12, color: '#999' }}>
            {record.apparatus?.serial_number || 'Unknown'}
          </div>
        </div>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (text: string) => <Tag>{formatTaskType(text)}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (text: string) => <Tag color={getStatusColor(text)}>{formatTaskStatus(text)}</Tag>,
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (text: string) => <Tag color={getPriorityColor(text)}>{formatTaskPriority(text)}</Tag>,
    },
    {
      title: 'Technician',
      dataIndex: 'technician',
      key: 'technician',
      width: 150,
      render: (technician: Task['technician']) => technician?.full_name || 'Unassigned',
    },
    {
      title: 'Scheduled',
      dataIndex: 'scheduled_at',
      key: 'scheduled_at',
      width: 160,
      render: (text: string) => formatRelativeTime(text),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (_text: string, record: Task) => (
        <Space>
          {record.status === 'pending' || record.status === 'assigned' ? (
            <>
              <Popconfirm
                title="Accept this task?"
                onConfirm={() => handleAccept(record.id)}
                okText="Yes"
                cancelText="No"
              >
                <Button type="primary" size="small" loading={acceptMutation.isPending}>Accept</Button>
              </Popconfirm>
              <Popconfirm
                title="Reject this task?"
                onConfirm={() => handleReject(record.id)}
                okText="Yes"
                cancelText="No"
              >
                <Button danger size="small" loading={rejectMutation.isPending}>Reject</Button>
              </Popconfirm>
            </>
          ) : record.status === 'in_progress' ? (
            <Button type="primary" size="small" disabled>In Progress</Button>
          ) : (
            <Tag color={getStatusColor(record.status)}>{formatTaskStatus(record.status)}</Tag>
          )}
        </Space>
      ),
    },
  ]

  const handleAccept = (taskId: string) => {
    acceptMutation.mutate({ id: taskId, data: { technician_id: 'current-user-id' } }, {
      onSuccess: () => {
        message.success('Task accepted')
        refetch()
      },
      onError: () => {
        message.error('Failed to accept task')
      },
    })
  }

  const handleReject = (taskId: string) => {
    const reason = prompt('Enter rejection reason:')
    if (reason) {
      rejectMutation.mutate({ id: taskId, data: { reason } }, {
        onSuccess: () => {
          message.success('Task rejected')
          refetch()
        },
        onError: () => {
          message.error('Failed to reject task')
        },
      })
    }
  }

  const onTableChange = (pagination: any, _filters: any) => {
    setFilters((prev) => ({
      ...prev,
      page: pagination.current,
      page_size: pagination.pageSize,
    }))
  }

  return (
    <Card>
      <Form layout="inline" style={{ marginBottom: 16 }}>
        <Form.Item name="search">
          <Input
            placeholder="Search tasks..."
            prefix={<SearchOutlined />}
            allowClear
            style={{ width: 250 }}
            onPressEnter={(e) => setFilters((prev) => ({ ...prev, search: (e.target as HTMLInputElement).value, page: 1 }))}
          />
        </Form.Item>
        <Form.Item name="status">
          <Select
            mode="multiple"
            placeholder="Status"
            style={{ width: 180 }}
            options={statusOptions.map((s) => ({ label: formatTaskStatus(s), value: s }))}
            onChange={(value) => setFilters((prev) => ({ ...prev, status: value as TaskStatus[], page: 1 }))}
          />
        </Form.Item>
        <Form.Item name="type">
          <Select
            mode="multiple"
            placeholder="Type"
            style={{ width: 180 }}
            options={typeOptions.map((t) => ({ label: formatTaskType(t), value: t }))}
            onChange={(value) => setFilters((prev) => ({ ...prev, type: value as TaskType[], page: 1 }))}
          />
        </Form.Item>
        <Form.Item name="priority">
          <Select
            mode="multiple"
            placeholder="Priority"
            style={{ width: 180 }}
            options={priorityOptions.map((p) => ({ label: formatTaskPriority(p), value: p }))}
            onChange={(value) => setFilters((prev) => ({ ...prev, priority: value as TaskPriority[], page: 1 }))}
          />
        </Form.Item>
        <Button onClick={() => refetch()} icon={<ReloadOutlined />} style={{ marginLeft: 8 }}>
          Refresh
        </Button>
      </Form>

      <Table
        columns={columns}
        dataSource={data?.items || []}
        pagination={{
          current: data?.page || 1,
          pageSize: data?.page_size || 20,
          total: data?.total || 0,
          showSizeChanger: true,
          showTotal: (total) => `Total ${total} tasks`,
        }}
        onChange={onTableChange}
        loading={isLoading}
        rowKey="id"
        rowSelection={{
          selectedRowKeys: selectedRows,
          onChange: (keys) => setSelectedRows(keys as string[]),
        }}
        size="middle"
        bordered
      />
    </Card>
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

function getPriorityColor(priority: string): string {
  switch (priority) {
    case 'critical':
      return 'red'
    case 'high':
      return 'orange'
    case 'medium':
      return 'gold'
    case 'low':
      return 'green'
    default:
      return 'default'
  }
}