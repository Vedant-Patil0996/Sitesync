'use client';

import * as React from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Badge } from '@/components/ui/badge';

// Fix default icon issue with webpack
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
});

function MapBoundsHelper({ sites }: { sites: any[] }) {
  const map = useMap();

  React.useEffect(() => {
    if (sites && sites.length > 0) {
      const bounds = L.latLngBounds(sites.map(s => [Number(s.latitude), Number(s.longitude)]));
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [map, sites]);

  return null;
}

export default function MapWrapper({ center, zoom, validSites, isMulti }: any) {
  return (
    <MapContainer 
      center={center} 
      zoom={zoom} 
      scrollWheelZoom={true} 
      style={{ height: '100%', width: '100%', zIndex: 0 }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {validSites.map((site: any, i: number) => (
        <Marker key={site.id || i} position={[Number(site.latitude), Number(site.longitude)]}>
          <Popup>
            <div className="text-sm">
              <strong className="block mb-1 font-bold">{site.name}</strong>
              {site.location && <span className="text-xs text-muted-foreground block mb-2">{site.location}</span>}
              <Badge variant={site.status === 'active' ? 'success' : 'default'} className="text-[10px] uppercase">
                {site.status || 'active'}
              </Badge>
            </div>
          </Popup>
        </Marker>
      ))}
      {isMulti && <MapBoundsHelper sites={validSites} />}
    </MapContainer>
  );
}
