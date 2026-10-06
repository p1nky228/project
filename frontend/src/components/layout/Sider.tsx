import { Menu, Layout } from 'antd'
import {
  DashboardOutlined,
  GlobalOutlined,
  FileTextOutlined,
  UsergroupAddOutlined,
  ShopOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useLocation } from 'react-router-dom'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'

const { Sider } = Layout

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/map', icon: <GlobalOutlined />, label: 'Map View' },
  { key: '/tasks', icon: <FileTextOutlined />, label: 'Tasks' },
  { key: '/technicians', icon: <UsergroupAddOutlined />, label: 'Technicians' },
  { key: '/apparatuses', icon: <ShopOutlined />, label: 'Apparatuses' },
  { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
]

export default function SiderComponent() {
  const { sidebarCollapsed } = useUIStore()
  const location = useLocation()
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return null
  }

  return (
    <Sider
      trigger={null}
      collapsible
      collapsed={sidebarCollapsed}
      breakpoint="lg"
      collapsedWidth={80}
      style={{
        height: 'calc(100vh - 64px)',
        position: 'sticky',
        top: 64,
        overflow: 'auto',
        background: '#fff',
        borderRight: '1px solid #f0f0f0',
      }}
    >
      <Menu
        mode="inline"
        theme="light"
        selectedKeys={[location.pathname]}
        items={menuItems.map((item) => ({
          key: item.key,
          icon: item.icon,
          label: item.label,
        }))}
        onClick={({ key }) => {
          if (key !== location.pathname) {
            window.location.href = key
          }
        }}
      />
    </Sider>
  )
}