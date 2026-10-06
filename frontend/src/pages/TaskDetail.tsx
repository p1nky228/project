import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Tag, Button, Spin, Divider, Image, Modal, message, Space, Row, Col } from 'antd'
import { ArrowLeftOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { useTask, useAcceptTask, useRejectTask } from '../hooks/useTasks'
import { formatTaskStatus, formatTaskType, formatTaskPriority, formatDateTime } from '../utils/formatters'

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading } = useTask(id || '')
  const acceptMutation = useAcceptTask()
  const rejectMutation = useRejectTask()
  const [previewImage, setPreviewImage] = useState<string | null>(null)
  const [previewVisible, setPreviewVisible] = useState(false)

  if (isLoading) {
    return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', padding: 48 }} />
  }

  if (!data?.task) {
    return (
      <Card style={{ maxWidth: 600, margin: '48px auto' }}>
        <p style={{ color: '#f5222d' }}>Task not found</p>
        <Button icon={<ArrowLeftOutlined />} onClick={() => window.history.back()}>
          Back to Tasks
        </Button>
      </Card>
    )
  }

  const task = data.task
  const photos = data.photos || []

  const handlePreview = (url: string) => {
    setPreviewImage(url)
    setPreviewVisible(true)
  }

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Button icon={<ArrowLeftOutlined />} onClick={() => window.history.back()} style={{ marginRight: 16 }}>
            Back
          </Button>
          <h2 style={{ margin: 0, display: 'inline' }}>{task.title}</h2>
        </div>
        <Space>
          <Tag color={getStatusColor(task.status)}>{formatTaskStatus(task.status)}</Tag>
          <Tag color={getPriorityColor(task.priority)}>{formatTaskPriority(task.priority)}</Tag>
          <Tag>{formatTaskType(task.type)}</Tag>
        </Space>
      </div>

      <Divider style={{ marginBottom: 24 }} />

      <Row gutter={[24, 16]}>
        <Col xs={24} lg={16}>
          <Card title="Description" style={{ marginBottom: 16 }}>
            <p style={{ whiteSpace: 'pre-wrap', color: task.description ? undefined : '#999' }}>
              {task.description || 'No description provided'}
            </p>
          </Card>

          <Card title="Details">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
              <DetailItem label="Task ID" value={task.id} />
              <DetailItem label="Apparatus" value={task.apparatus?.serial_number || 'Unknown'} />
              <DetailItem label="Technician" value={task.technician?.full_name || 'Unassigned'} />
              <DetailItem label="Scheduled" value={formatDateTime(task.scheduled_at)} />
              <DetailItem label="Started" value={task.started_at ? formatDateTime(task.started_at) : 'Not started'} />
              <DetailItem label="Completed" value={task.completed_at ? formatDateTime(task.completed_at) : 'Not completed'} />
              <DetailItem label="Created" value={formatDateTime(task.created_at)} />
              <DetailItem label="Updated" value={formatDateTime(task.updated_at)} />
            </div>
          </Card>

          {photos.length > 0 && (
            <Card title="Photos">
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                {photos.map((photo) => (
                  <div key={photo.id} style={{ width: 150, height: 150, position: 'relative' }}>
                    <Image
                      src={photo.url}
                      alt={photo.caption || 'Task photo'}
                      width={150}
                      height={150}
                      style={{ objectFit: 'cover', borderRadius: 4, cursor: 'pointer' }}
                      preview={false}
                      onClick={() => handlePreview(photo.url)}
                    />
                    {photo.caption && (
                      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, background: 'rgba(0,0,0,0.7)', color: '#fff', padding: '4px 8px', fontSize: 12, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {photo.caption}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </Col>

        <Col xs={24} lg={8}>
          <Card title="Actions" style={{ height: 'fit-content' }}>
            {task.status === 'pending' || task.status === 'assigned' ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button
                  type="primary"
                  block
                  icon={<CheckCircleOutlined />}
                  loading={acceptMutation.isPending}
                  onClick={() => acceptMutation.mutate({ id: task.id, data: { technician_id: 'current-user-id' } }, {
                    onSuccess: () => message.success('Task accepted'),
                    onError: () => message.error('Failed to accept task'),
                  })}
                >
                  Accept Task
                </Button>
                <Button
                  danger
                  block
                  icon={<CloseCircleOutlined />}
                  loading={rejectMutation.isPending}
                  onClick={() => {
                    const reason = prompt('Enter rejection reason:')
                    if (reason) {
                      rejectMutation.mutate({ id: task.id, data: { reason } }, {
                        onSuccess: () => message.success('Task rejected'),
                        onError: () => message.error('Failed to reject task'),
                      })
                    }
                  }}
                >
                  Reject Task
                </Button>
              </Space>
            ) : (
              <p style={{ color: '#999', textAlign: 'center' }}>No actions available for this status</p>
            )}
          </Card>
        </Col>
      </Row>

      <Modal open={previewVisible} footer={null} onCancel={() => setPreviewVisible(false)}>
        <Image src={previewImage!} alt="Preview" />
      </Modal>
    </Card>
  )
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>{label}</div>
      <div style={{ fontWeight: 500 }}>{value}</div>
    </div>
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