import { MapContainer, TileLayer, Marker } from 'react-leaflet'
import L from 'leaflet'

const UCI = [33.6405, -117.8443]

function pinIcon(label, cls) {
  return L.divIcon({
    className: '',
    html: `<div class="map-pin ${cls}">${label}</div>`,
    iconSize: [40, 40],
    iconAnchor: [20, 20],
  })
}

function initials(name) {
  return name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
}

export default function MapView({ currentUser, users, onUserClick }) {
  return (
    <MapContainer center={UCI} zoom={15} style={{ height: '100%', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org">OpenStreetMap</a>'
      />

      {currentUser && (
        <Marker
          position={[currentUser.lat, currentUser.lng]}
          icon={pinIcon('ME', 'me')}
        />
      )}

      {users.map((user) => (
        <Marker
          key={user.id}
          position={[user.lat, user.lng]}
          icon={pinIcon(initials(user.displayName), user.status)}
          eventHandlers={{ click: () => onUserClick(user) }}
        />
      ))}
    </MapContainer>
  )
}
