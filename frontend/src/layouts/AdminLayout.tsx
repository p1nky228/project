import { Layout, Spin } from 'antd'
import { Outlet } from 'react-router-dom'
import Header from '../components/layout/Header'
import Sider from '../components/layout/Sider'
import { useAuthStore } from '../store/authStore'

const { Content } = Layout

export default function AdminLayout() {
  const { isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Spin size="large" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }} />
      </Layout>
    )
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header />
      <Layout>
        <Sider />
        <Content
          style={{
            marginLeft: 0,
            padding: 24,
            background: '#f5f5f5',
            minHeight: 'calc(100vh - 64px)',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}