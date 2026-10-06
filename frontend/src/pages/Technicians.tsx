import { useState } from 'react'
import { Table, Tag, Button, Form, Input, Select, Card, Space } from 'antd'
import { SearchOutlined, ReloadOutlined, UserOutlined, StarOutlined } from '@ant-design/icons'
import { useTechnicians } from '../hooks/useTechnicians'
import type { Technician } from '../api/types'
import { formatRelativeTime } from '../utils/formatters'

export default function Technicians() {
  const [filters, setFilters] = useState({
    page: 1,
    page_size: 20,
    is_active: undefined as boolean | undefined,
    search: '',
    min_rating: undefined as number | undefined,
  })

  const { data, isLoading, refetch } = useTechnicians(filters)

  const columns = [
    {
      title: 'Technician',
      dataIndex: 'full_name',
      key: 'full_name',
      width: 200,
      render: (text: string, record: Technician) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <UserOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          <div>
            <div style={{ fontWeight: 500 }}>{text}</div>
            <div style={{ fontSize: 12, color: '#999' }}>{record.email}</div>
          </div>
        </div>
      ),
    },
    {
      title: 'Phone',
      dataIndex: 'phone',
      key: 'phone',
      width: 150,
      render: (text: string) => text || '-',
    },
    {
      title: 'Rating',
      dataIndex: 'rating',
      key: 'rating',
      width: 100,
      render: (value: number) => (
        <Space>
          <StarOutlined style={{ color: '#faad14' }} />
          <span style={{ fontWeight: 500 }}>{value.toFixed(1)}</span>
        </Space>
      ),
      sorter: (a: Technician, b: Technician) => b.rating - a.rating,
    },
    {
      title: 'Completed Tasks',
      dataIndex: 'completed_tasks',
      key: 'completed_tasks',
      width: 140,
      sorter: (a: Technician, b: Technician) => b.completed_tasks - a.completed_tasks,
    },
    {
      title: 'Active Tasks',
      dataIndex: 'active_tasks',
      key: 'active_tasks',
      width: 120,
      sorter: (a: Technician, b: Technician) => b.active_tasks - a.active_tasks,
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (value: boolean) => (
        <Tag color={value ? 'success' : 'default'}>
          {value ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Joined',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text: string) => formatRelativeTime(text),
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
            placeholder="Search technicians..."
            prefix={<SearchOutlined />}
            allowClear
            style={{ width: 250 }}
            onPressEnter={(e) => setFilters((prev) => ({ ...prev, search: (e.target as HTMLInputElement).value, page: 1 }))}
          />
        </Form.Item>
        <Form.Item name="is_active">
          <Select
            placeholder="Status"
            style={{ width: 150 }}
            options={[
              { label: 'Active', value: true },
              { label: 'Inactive', value: false },
            ]}
            onChange={(value) => setFilters((prev) => ({ ...prev, is_active: value as boolean | undefined, page: 1 }))}
          />
        </Form.Item>
        <Form.Item name="min_rating">
          <Select
            placeholder="Min Rating"
            style={{ width: 150 }}
            options={[
              { label: '4.0+', value: 4 },
              { label: '3.5+', value: 3.5 },
              { label: '3.0+', value: 3 },
            ]}
            onChange={(value) => setFilters((prev) => ({ ...prev, min_rating: value as number | undefined, page: 1 }))}
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
          showTotal: (total) => `Total ${total} technicians`,
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