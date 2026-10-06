import { useState } from 'react'
import { Card, Form, Input, Button, Alert, message, Space } from 'antd'
import { SettingOutlined, KeyOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useAuthStore } from '../store/authStore'

export default function Settings() {
  const { adminKey, setAdminKey, logout } = useAuthStore()
  const [newKey, setNewKey] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!newKey.trim()) {
      message.error('Please enter an admin key')
      return
    }

    setSaving(true)
    try {
      // Validate the new key
      const response = await fetch('/admin/stats', {
        headers: {
          'X-Admin-Key': newKey,
        },
      })

      if (response.ok) {
        setAdminKey(newKey)
        message.success('Admin key updated successfully!')
      } else {
        message.error('Invalid admin key')
      }
    } catch (error) {
      message.error('Connection error. Please check your API URL.')
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  return (
    <div style={{ maxWidth: 600 }}>
      <Card title={<SettingOutlined />} style={{ marginBottom: 24 }}>
        <Alert
          message="API Key Management"
          description="Your admin API key is used to authenticate requests to the backend. It is stored locally in your browser and sent as the X-Admin-Key header with each request."
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Form layout="vertical">
          <Form.Item
            label="Current Admin Key"
            labelCol={{ span: 6 }}
            wrapperCol={{ span: 18 }}
          >
            <Input.Password
              value={adminKey || ''}
              disabled
              suffix={<KeyOutlined />}
              visibilityToggle
            />
          </Form.Item>

          <Form.Item
            label="New Admin Key"
            labelCol={{ span: 6 }}
            wrapperCol={{ span: 18 }}
          >
            <Input.Password
              value={newKey}
              onChange={(e) => setNewKey(e.target.value)}
              placeholder="Enter new admin key"
              suffix={<KeyOutlined />}
              visibilityToggle
            />
          </Form.Item>

          <Form.Item wrapperCol={{ offset: 6, span: 18 }} style={{ marginTop: 16 }}>
            <Space>
              <Button
                type="primary"
                icon={<CheckCircleOutlined />}
                loading={saving}
                onClick={handleSave}
              >
                Save Changes
              </Button>
              <Button danger onClick={handleLogout}>
                Logout
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card title={<SettingOutlined />} style={{ marginBottom: 24 }}>
        <Alert
          message="Application Settings"
          description="Configure application-wide settings here."
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Form layout="vertical">
          <Form.Item label="API Base URL" labelCol={{ span: 6 }} wrapperCol={{ span: 18 }}>
            <Input
              value={import.meta.env.VITE_API_URL || 'http://localhost:8000'}
              disabled
              placeholder="Set via VITE_API_URL environment variable"
            />
          </Form.Item>

          <Form.Item label="Theme" labelCol={{ span: 6 }} wrapperCol={{ span: 18 }}>
            <p style={{ margin: 0, color: '#999' }}>Theme customization available via Ant Design ConfigProvider in main.tsx</p>
          </Form.Item>
        </Form>
      </Card>

      <Card title={<SettingOutlined />}>
        <Alert
          message="About"
          description="Vending Machine Maintenance Admin Panel v1.0.0"
          type="info"
          showIcon
        />
      </Card>
    </div>
  )
}