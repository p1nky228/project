import { useState } from 'react'
import { Form, Input, Button, Card, Alert, message } from 'antd'
import { LockOutlined, KeyOutlined, SettingOutlined } from '@ant-design/icons'
import { useAuthStore } from '../store/authStore'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const [loading, setLoading] = useState(false)
  const { setAdminKey } = useAuthStore()
  const navigate = useNavigate()

  const onFinish = async (values: { adminKey: string }) => {
    setLoading(true)
    try {
      // Validate the admin key by making a test request
      const response = await fetch('/admin/stats', {
        headers: {
          'X-Admin-Key': values.adminKey,
        },
      })

      if (response.ok) {
        setAdminKey(values.adminKey)
        message.success('Login successful!')
        navigate('/')
      } else {
        message.error('Invalid admin key')
      }
    } catch (error) {
      message.error('Connection error. Please check your API URL.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f5f5f5',
        padding: 24,
      }}
    >
      <Card style={{ width: '100%', maxWidth: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <SettingOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>Vending Maintenance Admin</h1>
          <p style={{ marginTop: 8, color: '#999' }}>Enter your admin API key to continue</p>
        </div>

        <Form
          layout="vertical"
          onFinish={onFinish}
          initialValues={{ adminKey: localStorage.getItem('admin_key') || '' }}
        >
          <Form.Item
            name="adminKey"
            label="Admin API Key"
            rules={[{ required: true, message: 'Please enter your admin key' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              suffix={<KeyOutlined />}
              placeholder="Enter admin key"
              visibilityToggle
              autoComplete="off"
            />
          </Form.Item>

          <Alert
            message="Your admin key is stored locally and sent with each request as X-Admin-Key header."
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />

          <Button
            type="primary"
            htmlType="submit"
            block
            size="large"
            loading={loading}
            style={{ marginBottom: 16 }}
          >
            Sign In
          </Button>

          <div style={{ textAlign: 'center', color: '#999', fontSize: 14 }}>
            Don't have an admin key? Contact your system administrator.
          </div>
        </Form>
      </Card>
    </div>
  )
}