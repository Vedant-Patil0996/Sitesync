'use client';

import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';

export function MapBoundsHelper({ sites }: { sites: any[] }) {
  const map = useMap();

  useEffect(() => {
    if (sites && sites.length > 0) {
      const bounds = L.latLngBounds(sites.map(s => [Number(s.latitude), Number(s.longitude)]));
      // Give some padding so markers don't hit the edge
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [map, sites]);

  return null;
}
