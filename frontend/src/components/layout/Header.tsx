import { MenuOutlined, UserOutlined, LogoutOutlined, BellOutlined } from '@ant-design/icons'
import { Avatar, Dropdown, Badge, Tooltip } from 'antd'
import { useAuthStore } from '../../store/authStore'
import { useUIStore } from '../../store/uiStore'
import { useNavigate } from 'react-router-dom'

export default function Header() {
  const { logout } = useAuthStore()
  const { notifications, removeNotification } = useUIStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const menuItems = [
    { label: 'Profile', key: 'profile', icon: <UserOutlined /> },
    { type: 'divider' as const },
    { label: 'Logout', key: 'logout', icon: <LogoutOutlined />, danger: true, onClick: handleLogout },
  ]

  return (
    <header
      style={{
        height: 64,
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#fff',
        borderBottom: '1px solid #f0f0f0',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <Tooltip title="Toggle Menu">
          <MenuOutlined
            style={{ fontSize: 20, cursor: 'pointer', color: '#666' }}
            onClick={() => useUIStore.getState().toggleSidebar()}
          />
        </Tooltip>
        <h1 style={{ margin: 0, fontSize: 20, fontWeight: 600, color: '#1f1f1f' }}>
          Vending Maintenance Admin
        </h1>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <Dropdown
          menu={{
            items: [
              {
                label: (
                  <div style={{ padding: '8px 0' }}>
                    <div style={{ fontWeight: 600 }}>Notifications</div>
                    {notifications.length === 0 && (
                      <div style={{ color: '#999', padding: '8px 0' }}>No notifications</div>
                    )}
                    {notifications.map((n) => (
                      <div
                        key={n.id}
                        style={{
                          padding: '8px 0',
                          borderBottom: '1px solid #f0f0f0',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <span>{n.message}</span>
                        <span
                          onClick={() => removeNotification(n.id)}
                          style={{ cursor: 'pointer', color: '#999' }}
                        >
                          ×
                        </span>
                      </div>
                    ))}
                  </div>
                ),
                key: 'notifications',
              },
            ],
          }}
        >
          <Badge count={notifications.length} showZero={false}>
            <Tooltip title="Notifications">
              <BellOutlined style={{ fontSize: 20, cursor: 'pointer', color: '#666' }} />
            </Tooltip>
          </Badge>
        </Dropdown>

        <Dropdown menu={{ items: menuItems }}>
          <Tooltip title="Account">
            <Avatar
              style={{ cursor: 'pointer', background: '#1890ff' }}
              icon={<UserOutlined />}
            />
          </Tooltip>
        </Dropdown>
      </div>
    </header>
  )
}