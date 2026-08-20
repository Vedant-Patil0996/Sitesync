'use client';

import * as React from 'react';
import { MapPin, Navigation, ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface SiteMapProps {
  name: string;
  location?: string;
  latitude?: number | null;
  longitude?: number | null;
  status?: string;
}

export function SiteMap({ name, location, latitude, longitude, status = 'active' }: SiteMapProps) {
  // Default to Mumbai coordinates if coordinates are null
  const lat = latitude || 19.0760;
  const lng = longitude || 72.8777;

  // OpenStreetMap embed URL with marker
  const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${lng - 0.01}%2C${lat - 0.01}%2C${lng + 0.01}%2C${lat + 0.01}&layer=mapnik&marker=${lat}%2C${lng}`;
  const externalMapUrl = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}#map=15/${lat}/${lng}`;

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <CardTitle className="flex items-center gap-2 text-base font-bold">
            <MapPin className="h-5 w-5 text-primary" />
            {name} Site Location
          </CardTitle>
          {location && <p className="text-xs text-muted-foreground mt-1 font-medium">{location}</p>}
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={status === 'active' ? 'success' : 'default'} className="text-[10px] uppercase">
            {status}
          </Badge>
          <a
            href={externalMapUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs text-primary font-bold hover:underline"
          >
            Open <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </CardHeader>
      <CardContent className="p-0 relative">
        <div className="h-64 w-full relative bg-muted border-t-2 border-border">
          <iframe
            title={`Site Map - ${name}`}
            width="100%"
            height="100%"
            frameBorder="0"
            scrolling="no"
            marginHeight={0}
            marginWidth={0}
            src={mapUrl}
            className="w-full h-full filter contrast-105 brightness-95"
          />
          {/* Overlay info box */}
          <div className="absolute bottom-3 left-3 bg-card border-2 border-border p-2.5 shadow-brutal-sm text-xs flex items-center gap-2 z-10">
            <Navigation className="h-4 w-4 text-primary shrink-0" />
            <div>
              <span className="font-bold block">{lat.toFixed(4)}° N, {lng.toFixed(4)}° E</span>
              <span className="text-[10px] text-muted-foreground">Interactive OpenStreetMap Tile</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
