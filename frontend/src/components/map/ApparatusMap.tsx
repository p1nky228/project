import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import { useApparatuses } from '../../hooks/useApparatuses'
import type { Apparatus } from '../../api/types'
import { Spin } from 'antd'

const statusIcons: Record<string, string> = {
  operational: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  maintenance: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  out_of_order: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  decommissioned: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png',
}

function CustomMarker({ apparatus, onClick }: { apparatus: Apparatus; onClick: () => void }) {
  const icon = L.icon({
    iconUrl: statusIcons[apparatus.status] || statusIcons.operational,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
  })

  return (
    <Marker position={[apparatus.location_lat, apparatus.location_lng]} icon={icon} eventHandlers={{ click: onClick }}>
      <Popup>
        <div style={{ minWidth: 200 }}>
          <h4 style={{ margin: '0 0 8px 0' }}>{apparatus.serial_number}</h4>
          <p style={{ margin: '4px 0' }}><strong>Model:</strong> {apparatus.model}</p>
          <p style={{ margin: '4px 0' }}><strong>Status:</strong> {apparatus.status}</p>
          <p style={{ margin: '4px 0' }}><strong>Address:</strong> {apparatus.address}</p>
          {apparatus.next_maintenance_at && (
            <p style={{ margin: '4px 0' }}><strong>Next Maintenance:</strong> {new Date(apparatus.next_maintenance_at).toLocaleDateString()}</p>
          )}
        </div>
      </Popup>
    </Marker>
  )
}

function MapEvents() {
  const map = useMapEvents({
    click() {
      map.closePopup()
    },
  })
  return null
}

export function ApparatusMap({ onSelectApparatus }: { onSelectApparatus: (apparatus: Apparatus) => void }) {
  const { data, isLoading } = useApparatuses()

  if (isLoading) {
    return (
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spin size="large" />
      </div>
    )
  }

  const center = data?.items.length
    ? [data.items[0].location_lat, data.items[0].location_lng] as [number, number]
    : [55.7558, 37.6173] as [number, number]

  return (
    <MapContainer
      center={center}
      zoom={10}
      style={{ height: '100%', width: '100%', zIndex: 0 }}
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapEvents />
      {data?.items.map((apparatus) => (
        <CustomMarker
          key={apparatus.id}
          apparatus={apparatus}
          onClick={() => onSelectApparatus(apparatus)}
        />
      ))}
    </MapContainer>
  )
}