'use client';

import * as React from 'react';
import { MapPin, Navigation } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import dynamic from 'next/dynamic';
import 'leaflet/dist/leaflet.css';

// Dynamically import the map wrapper to avoid SSR issues with Leaflet
const DynamicMap = dynamic(
  () => import('./map-wrapper'),
  { 
    ssr: false,
    loading: () => (
      <div className="h-96 w-full bg-muted flex items-center justify-center border-t-2 border-border text-muted-foreground font-bold">
        Loading Map...
      </div>
    )
  }
);

interface SiteLocation {
  id?: string | number;
  name: string;
  location?: string;
  latitude?: number | null;
  longitude?: number | null;
  status?: string;
}

interface SiteMapProps {
  // Support either single site...
  name?: string;
  location?: string;
  latitude?: number | null;
  longitude?: number | null;
  status?: string;
  // ...or multiple sites
  sites?: SiteLocation[];
}

export function SiteMap(props: SiteMapProps) {
  // Normalize into an array of sites
  let mapSites: SiteLocation[] = [];
  if (props.sites && props.sites.length > 0) {
    mapSites = props.sites;
  } else if (props.name) {
    mapSites = [{
      name: props.name,
      location: props.location,
      latitude: props.latitude,
      longitude: props.longitude,
      status: props.status
    }];
  }

  // Filter out sites without valid coordinates
  const validSites = mapSites.filter(s => s.latitude != null && s.longitude != null);
  
  // Default to Mumbai
  const defaultCenter: [number, number] = [19.0760, 72.8777];
  const center: [number, number] = validSites.length > 0
    ? [Number(validSites[0].latitude), Number(validSites[0].longitude)]
    : defaultCenter;

  const isMulti = mapSites.length > 1;

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <CardTitle className="flex items-center gap-2 text-base font-bold">
            <MapPin className="h-5 w-5 text-primary" />
            {isMulti ? "All Site Locations" : `${props.name} Site Location`}
          </CardTitle>
          {!isMulti && props.location && <p className="text-xs text-muted-foreground mt-1 font-medium">{props.location}</p>}
        </div>
        {!isMulti && (
          <div className="flex items-center gap-2">
            <Badge variant={props.status === 'active' ? 'success' : 'default'} className="text-[10px] uppercase">
              {props.status || 'active'}
            </Badge>
          </div>
        )}
      </CardHeader>
      <CardContent className="p-0 relative">
        <div className="h-96 w-full relative bg-muted border-t-2 border-border z-0">
          <DynamicMap 
            center={center} 
            zoom={isMulti ? 11 : 15} 
            validSites={validSites} 
            isMulti={isMulti} 
          />
          
          {/* Overlay info box for single site */}
          {!isMulti && validSites.length === 1 && (
            <div className="absolute bottom-3 left-3 bg-card border-2 border-border p-2.5 shadow-brutal-sm text-xs flex items-center gap-2 z-[400]">
              <Navigation className="h-4 w-4 text-primary shrink-0" />
              <div>
                <span className="font-bold block">{Number(validSites[0].latitude).toFixed(4)}° N, {Number(validSites[0].longitude).toFixed(4)}° E</span>
                <span className="text-[10px] text-muted-foreground">Interactive OpenStreetMap Tile</span>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
