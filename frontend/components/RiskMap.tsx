'use client'

import { useEffect, useRef, useState } from 'react'
import { Layers, Droplets, Flame, Plane, Users } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'

interface RiskMapProps {
  lat?: number
  lng?: number
  address: string
  streetLevel?: {
    flood_risk?: { aep_1_percent: boolean }
    bushfire_risk?: { bal_rating?: string }
    flight_path?: { anef: number }
    social_housing?: { density_percent: number }
  }
}

export function RiskMap({ lat, lng, address, streetLevel }: RiskMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  const [activeLayers, setActiveLayers] = useState<Set<string>>(new Set(['property']))

  // Note: In production, this would use Mapbox GL JS
  // For the demo, we show a placeholder with layer toggles

  const toggleLayer = (layer: string) => {
    const newLayers = new Set(activeLayers)
    if (newLayers.has(layer)) {
      newLayers.delete(layer)
    } else {
      newLayers.add(layer)
    }
    setActiveLayers(newLayers)
  }

  const layers = [
    { 
      id: 'flood', 
      name: 'Flood Zones', 
      icon: Droplets, 
      color: 'text-blue-500',
      active: streetLevel?.flood_risk?.aep_1_percent 
    },
    { 
      id: 'bushfire', 
      name: 'Bushfire', 
      icon: Flame, 
      color: 'text-orange-500',
      active: !!streetLevel?.bushfire_risk?.bal_rating 
    },
    { 
      id: 'flight', 
      name: 'Flight Paths', 
      icon: Plane, 
      color: 'text-purple-500',
      active: streetLevel?.flight_path?.anef && streetLevel.flight_path.anef > 10 
    },
    { 
      id: 'social', 
      name: 'Social Housing', 
      icon: Users, 
      color: 'text-green-500',
      active: streetLevel?.social_housing?.density_percent && streetLevel.social_housing.density_percent > 10 
    },
  ]

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Layers className="h-5 w-5" />
          Risk Map
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Layer Toggles */}
        <div className="flex flex-wrap gap-2 mb-4">
          {layers.map((layer) => (
            <Button
              key={layer.id}
              variant={activeLayers.has(layer.id) ? 'default' : 'outline'}
              size="sm"
              onClick={() => toggleLayer(layer.id)}
              className={`text-xs ${layer.active ? '' : 'opacity-50'}`}
            >
              <layer.icon className={`h-3 w-3 mr-1 ${layer.color}`} />
              {layer.name}
            </Button>
          ))}
        </div>

        {/* Map Container */}
        <div 
          ref={mapContainer}
          className="h-64 bg-slate-100 rounded-lg flex items-center justify-center"
        >
          {lat && lng ? (
            <div className="text-center">
              {/* Static map placeholder - in production use Mapbox */}
              <img
                src={`https://api.mapbox.com/styles/v1/mapbox/streets-v12/static/pin-l+3b82f6(${lng},${lat})/${lng},${lat},14,0/400x256@2x?access_token=${process.env.NEXT_PUBLIC_MAPBOX_TOKEN || 'pk.placeholder'}`}
                alt="Property map"
                className="rounded-lg w-full h-full object-cover"
                onError={(e) => {
                  // Fallback to placeholder on error
                  (e.target as HTMLImageElement).style.display = 'none'
                  e.currentTarget.parentElement!.innerHTML = `
                    <div class="text-muted-foreground text-sm">
                      <p class="font-medium">📍 ${address}</p>
                      <p class="mt-1 text-xs">Lat: ${lat?.toFixed(4)}, Lng: ${lng?.toFixed(4)}</p>
                      <p class="mt-2 text-xs">Add MAPBOX_TOKEN to enable map</p>
                    </div>
                  `
                }}
              />
            </div>
          ) : (
            <div className="text-center text-muted-foreground">
              <p className="font-medium">{address}</p>
              <p className="text-sm mt-1">Location data unavailable</p>
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="mt-3 flex flex-wrap gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span>Flood</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-orange-500" />
            <span>Bushfire</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-purple-500" />
            <span>Flight Path</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span>Social Housing</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}







