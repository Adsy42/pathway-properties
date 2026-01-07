'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Search, Loader2, PenLine, X } from 'lucide-react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { analyzeProperty, addPropertyManual, PropertyAnalyzeResponse, ManualPropertyInput } from '@/lib/api'

interface PropertyInputProps {
  onAnalysisComplete: (data: PropertyAnalyzeResponse) => void
}

const STATES = ['VIC', 'NSW', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT']
const PROPERTY_TYPES = ['house', 'townhouse', 'unit', 'apartment', 'land', 'rural']

export function PropertyInput({ onAnalysisComplete }: PropertyInputProps) {
  const [url, setUrl] = useState('')
  const [showManualForm, setShowManualForm] = useState(false)
  const [scrapeError, setScrapeError] = useState<string | null>(null)
  
  // Manual form state
  const [manualData, setManualData] = useState<ManualPropertyInput>({
    address: '',
    suburb: '',
    state: 'VIC',
    postcode: '',
    bedrooms: undefined,
    bathrooms: undefined,
    parking: undefined,
    land_size: undefined,
    property_type: 'house',
    price_display: '',
    latitude: undefined,
    longitude: undefined,
    description: '',
    url: '',
  })

  const scrapeMutation = useMutation({
    mutationFn: analyzeProperty,
    onSuccess: (data) => {
      setScrapeError(null)
      onAnalysisComplete(data)
    },
    onError: (error: Error) => {
      setScrapeError(error.message)
      // Pre-fill URL in manual form
      setManualData(prev => ({ ...prev, url }))
    },
  })

  const manualMutation = useMutation({
    mutationFn: addPropertyManual,
    onSuccess: (data) => {
      onAnalysisComplete(data)
    },
  })

  const handleUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (url.trim()) {
      setScrapeError(null)
      scrapeMutation.mutate(url.trim())
    }
  }

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    manualMutation.mutate(manualData)
  }

  const updateManualData = (field: keyof ManualPropertyInput, value: any) => {
    setManualData(prev => ({ ...prev, [field]: value }))
  }

  const isValidUrl = url.includes('domain.com.au') || url.includes('realestate.com.au')
  const isManualValid = manualData.address && manualData.suburb && manualData.postcode

  // Show manual form
  if (showManualForm) {
    return (
      <div className="w-full max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Add Property Manually</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setShowManualForm(false)
              setScrapeError(null)
            }}
          >
            <X className="h-4 w-4 mr-1" />
            Cancel
          </Button>
        </div>

        <form onSubmit={handleManualSubmit} className="space-y-4">
          {/* Address Section */}
          <div className="grid gap-4">
            <div>
              <Label htmlFor="address">Full Address *</Label>
              <Input
                id="address"
                placeholder="e.g. 122 Station Street, Pakenham VIC 3810"
                value={manualData.address}
                onChange={(e) => updateManualData('address', e.target.value)}
                required
              />
            </div>
            
            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label htmlFor="suburb">Suburb *</Label>
                <Input
                  id="suburb"
                  placeholder="Pakenham"
                  value={manualData.suburb}
                  onChange={(e) => updateManualData('suburb', e.target.value)}
                  required
                />
              </div>
              <div>
                <Label htmlFor="state">State</Label>
                <select
                  id="state"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={manualData.state}
                  onChange={(e) => updateManualData('state', e.target.value)}
                >
                  {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <Label htmlFor="postcode">Postcode *</Label>
                <Input
                  id="postcode"
                  placeholder="3810"
                  value={manualData.postcode}
                  onChange={(e) => updateManualData('postcode', e.target.value)}
                  required
                />
              </div>
            </div>
          </div>

          {/* Property Details */}
          <div className="grid grid-cols-4 gap-3">
            <div>
              <Label htmlFor="bedrooms">Beds</Label>
              <Input
                id="bedrooms"
                type="number"
                placeholder="3"
                value={manualData.bedrooms ?? ''}
                onChange={(e) => updateManualData('bedrooms', e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </div>
            <div>
              <Label htmlFor="bathrooms">Baths</Label>
              <Input
                id="bathrooms"
                type="number"
                placeholder="2"
                value={manualData.bathrooms ?? ''}
                onChange={(e) => updateManualData('bathrooms', e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </div>
            <div>
              <Label htmlFor="parking">Parking</Label>
              <Input
                id="parking"
                type="number"
                placeholder="1"
                value={manualData.parking ?? ''}
                onChange={(e) => updateManualData('parking', e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </div>
            <div>
              <Label htmlFor="land_size">Land (m²)</Label>
              <Input
                id="land_size"
                type="number"
                placeholder="500"
                value={manualData.land_size ?? ''}
                onChange={(e) => updateManualData('land_size', e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="property_type">Property Type</Label>
              <select
                id="property_type"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={manualData.property_type}
                onChange={(e) => updateManualData('property_type', e.target.value)}
              >
                {PROPERTY_TYPES.map(t => (
                  <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="price_display">Price</Label>
              <Input
                id="price_display"
                placeholder="$590,000 - $630,000"
                value={manualData.price_display ?? ''}
                onChange={(e) => updateManualData('price_display', e.target.value)}
              />
            </div>
          </div>

          {/* Coordinates (optional) */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="latitude">Latitude (optional)</Label>
              <Input
                id="latitude"
                type="number"
                step="0.0001"
                placeholder="-37.8136"
                value={manualData.latitude ?? ''}
                onChange={(e) => updateManualData('latitude', e.target.value ? parseFloat(e.target.value) : undefined)}
              />
            </div>
            <div>
              <Label htmlFor="longitude">Longitude (optional)</Label>
              <Input
                id="longitude"
                type="number"
                step="0.0001"
                placeholder="144.9631"
                value={manualData.longitude ?? ''}
                onChange={(e) => updateManualData('longitude', e.target.value ? parseFloat(e.target.value) : undefined)}
              />
            </div>
          </div>

          <div>
            <Label htmlFor="url">Listing URL (optional)</Label>
            <Input
              id="url"
              type="url"
              placeholder="https://www.domain.com.au/..."
              value={manualData.url ?? ''}
              onChange={(e) => updateManualData('url', e.target.value)}
            />
          </div>

          {manualMutation.isError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              Error: {(manualMutation.error as Error).message}
            </div>
          )}

          <Button
            type="submit"
            size="lg"
            className="w-full"
            disabled={!isManualValid || manualMutation.isPending}
          >
            {manualMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              'Analyze Property'
            )}
          </Button>
        </form>
      </div>
    )
  }

  // Show URL input (default view)
  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleUrlSubmit} className="flex gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <Input
            type="url"
            placeholder="Paste Domain or RealEstate.com.au property URL..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="pl-10 h-12 text-lg"
            disabled={scrapeMutation.isPending}
          />
        </div>
        <Button
          type="submit"
          size="lg"
          disabled={!isValidUrl || scrapeMutation.isPending}
          className="h-12 px-8"
        >
          {scrapeMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            'Analyze'
          )}
        </Button>
      </form>
      
      {scrapeError && (
        <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-amber-800 font-medium">Couldn't fetch listing automatically</p>
          <p className="text-amber-700 text-sm mt-1">{scrapeError}</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-3"
            onClick={() => setShowManualForm(true)}
          >
            <PenLine className="mr-2 h-4 w-4" />
            Add Property Manually
          </Button>
        </div>
      )}
      
      <div className="flex items-center justify-center gap-4 mt-4">
        <p className="text-sm text-muted-foreground">
          Supports Domain.com.au and RealEstate.com.au listings
        </p>
        <span className="text-muted-foreground">•</span>
        <button
          type="button"
          onClick={() => setShowManualForm(true)}
          className="text-sm text-primary hover:underline"
        >
          Or add manually
        </button>
      </div>
    </div>
  )
}
