import { useState } from 'react'
import { Table, Tag, Button, Form, Input, Select, Card } from 'antd'
import { SearchOutlined, ReloadOutlined, ShopOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { useApparatuses } from '../hooks/useApparatuses'
import type { Apparatus, ApparatusStatus } from '../api/types'
import { formatDate } from '../utils/formatters'

const statusOptions: ApparatusStatus[] = ['operational', 'maintenance', 'out_of_order', 'decommissioned']

export default function Apparatuses() {
  const [filters, setFilters] = useState({
    page: 1,
    page_size: 20,
    status: [] as ApparatusStatus[],
    search: '',
    needs_maintenance: undefined as boolean | undefined,
  })

  const { data, isLoading, refetch } = useApparatuses(filters)

  const columns = [
    {
      title: 'Apparatus',
      dataIndex: 'serial_number',
      key: 'serial_number',
      width: 180,
      render: (text: string, record: Apparatus) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ShopOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          <div>
            <div style={{ fontWeight: 500 }}>{text}</div>
            <div style={{ fontSize: 12, color: '#999' }}>{record.model}</div>
          </div>
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 130,
      render: (text: string) => <Tag color={getStatusColor(text)}>{text}</Tag>,
    },
    {
      title: 'Address',
      dataIndex: 'address',
      key: 'address',
      width: 250,
      ellipsis: true,
    },
    {
      title: 'Last Maintenance',
      dataIndex: 'last_maintenance_at',
      key: 'last_maintenance_at',
      width: 150,
      render: (text: string | null) => text ? formatDate(text) : '-',
    },
    {
      title: 'Next Maintenance',
      dataIndex: 'next_maintenance_at',
      key: 'next_maintenance_at',
      width: 150,
      render: (text: string | null, _record: Apparatus) => {
        if (!text) return '-'
        const isOverdue = new Date(text) < new Date()
        return (
          <span style={{ color: isOverdue ? '#f5222d' : undefined, fontWeight: isOverdue ? 600 : undefined }}>
            {formatDate(text)}
            {isOverdue && <ClockCircleOutlined style={{ marginLeft: 4, color: '#f5222d' }} />}
          </span>
        )
      },
      sorter: (a: Apparatus, b: Apparatus) => {
        if (!a.next_maintenance_at && !b.next_maintenance_at) return 0
        if (!a.next_maintenance_at) return 1
        if (!b.next_maintenance_at) return -1
        return new Date(a.next_maintenance_at).getTime() - new Date(b.next_maintenance_at).getTime()
      },
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (text: string) => formatDate(text),
    },
  ]

  const onTableChange = (pagination: any) => {
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
            placeholder="Search apparatuses..."
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
            options={statusOptions.map((s) => ({ label: s, value: s }))}
            onChange={(value) => setFilters((prev) => ({ ...prev, status: value as ApparatusStatus[], page: 1 }))}
          />
        </Form.Item>
        <Form.Item name="needs_maintenance">
          <Select
            placeholder="Maintenance"
            style={{ width: 180 }}
            options={[
              { label: 'Overdue', value: true },
              { label: 'Upcoming', value: false },
            ]}
            onChange={(value) => setFilters((prev) => ({ ...prev, needs_maintenance: value as boolean | undefined, page: 1 }))}
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
          showTotal: (total) => `Total ${total} apparatuses`,
        }}
        onChange={onTableChange}
        loading={isLoading}
        rowKey="id"
        size="middle"
        bordered
      />
    </Card>
  )
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'operational':
      return 'success'
    case 'maintenance':
      return 'blue'
    case 'out_of_order':
      return 'red'
    case 'decommissioned':
      return 'default'
    default:
      return 'default'
  }
}