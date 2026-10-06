import { useState } from 'react'
import { Card, Row, Col, Tag, List, Spin, Divider, Button } from 'antd'
import { ApparatusMap } from '../components/map/ApparatusMap'
import { useApparatuses } from '../hooks/useApparatuses'
import type { Apparatus } from '../api/types'

export default function MapView() {
  const [selectedApparatus, setSelectedApparatus] = useState<Apparatus | null>(null)
  const { data, isLoading } = useApparatuses()

  const handleSelectApparatus = (apparatus: Apparatus) => {
    setSelectedApparatus(apparatus)
  }

  const clearSelection = () => {
    setSelectedApparatus(null)
  }

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="Apparatus Map" style={{ height: 'calc(100vh - 160px)' }}>
            <ApparatusMap
              onSelectApparatus={handleSelectApparatus}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Apparatus List" style={{ height: 'calc(100vh - 160px)', display: 'flex', flexDirection: 'column' }}>
            {selectedApparatus && (
              <div style={{ marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid #f0f0f0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h4 style={{ margin: 0 }}>{selectedApparatus.serial_number}</h4>
                  <Button type="text" size="small" onClick={clearSelection}>Close</Button>
                </div>
                <Divider />
                <div style={{ marginTop: 12 }}>
                  <p><strong>Model:</strong> {selectedApparatus.model}</p>
                  <p><strong>Status:</strong> <Tag color={getStatusColor(selectedApparatus.status)}>{selectedApparatus.status}</Tag></p>
                  <p><strong>Address:</strong> {selectedApparatus.address}</p>
                  {selectedApparatus.last_maintenance_at && (
                    <p><strong>Last Maintenance:</strong> {new Date(selectedApparatus.last_maintenance_at).toLocaleDateString()}</p>
                  )}
                  {selectedApparatus.next_maintenance_at && (
                    <p><strong>Next Maintenance:</strong> {new Date(selectedApparatus.next_maintenance_at).toLocaleDateString()}</p>
                  )}
                </div>
              </div>
            )}
            <div style={{ flex: 1, overflow: 'auto' }}>
              {isLoading ? (
                <Spin size="large" style={{ display: 'flex', justifyContent: 'center', padding: 32 }} />
              ) : (
                <List
                  itemLayout="horizontal"
                  dataSource={data?.items || []}
                  renderItem={(apparatus) => (
                    <List.Item
                      actions={[
                        <Button
                          type="text"
                          size="small"
                          onClick={() => handleSelectApparatus(apparatus)}
                        >
                          View
                        </Button>,
                      ]}
                    >
                      <List.Item.Meta
                        title={apparatus.serial_number}
                        description={
                          <>
                            <div>{apparatus.model}</div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                              <Tag color={getStatusColor(apparatus.status)}>{apparatus.status}</Tag>
                              {apparatus.next_maintenance_at && (
                                <span style={{ fontSize: 12, color: '#f5222d' }}>
                                  Maintenance due: {new Date(apparatus.next_maintenance_at).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                          </>
                        }
                      />
                    </List.Item>
                  )}
                />
              )}
            </div>
          </Card>
        </Col>
      </Row>
    </div>
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