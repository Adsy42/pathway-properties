'use client'

import Image from 'next/image'
import { Home, Bed, Bath, Car, Ruler } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { PropertyDetails } from '@/lib/api'
import { formatCurrency, formatPercent } from '@/lib/utils'

interface PropertyCardProps {
  property: PropertyDetails
}

export function PropertyCard({ property }: PropertyCardProps) {
  const corelogic = property.corelogic

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-start gap-2">
          <Home className="h-5 w-5 mt-0.5 text-primary shrink-0" />
          <span>{property.address}</span>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Property Image */}
        {property.images[0] && (
          <div className="relative h-48 rounded-lg overflow-hidden bg-slate-100">
            <Image
              src={property.images[0]}
              alt={property.address}
              fill
              className="object-cover"
              unoptimized
            />
          </div>
        )}

        {/* Features */}
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          {property.bedrooms && (
            <div className="flex items-center gap-1">
              <Bed className="h-4 w-4" />
              <span>{property.bedrooms}</span>
            </div>
          )}
          {property.bathrooms && (
            <div className="flex items-center gap-1">
              <Bath className="h-4 w-4" />
              <span>{property.bathrooms}</span>
            </div>
          )}
          {property.parking && (
            <div className="flex items-center gap-1">
              <Car className="h-4 w-4" />
              <span>{property.parking}</span>
            </div>
          )}
          {property.land_size && (
            <div className="flex items-center gap-1">
              <Ruler className="h-4 w-4" />
              <span>{property.land_size}m²</span>
            </div>
          )}
          {property.property_type && (
            <Badge variant="outline" className="ml-auto capitalize">
              {property.property_type}
            </Badge>
          )}
        </div>

        {/* Pricing */}
        <div className="bg-slate-50 rounded-lg p-4 space-y-3">
          {property.listing_price && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Listing Price</span>
              <span className="font-semibold">{property.listing_price}</span>
            </div>
          )}

          {corelogic?.avm && (
            <>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">CoreLogic AVM</span>
                <div className="text-right">
                  <span className="font-semibold">{formatCurrency(corelogic.avm)}</span>
                  {corelogic.avm_confidence && (
                    <Badge variant="outline" className="ml-2 text-xs">
                      {corelogic.avm_confidence}
                    </Badge>
                  )}
                </div>
              </div>

              {corelogic.last_sold_price && (
                <div className="flex justify-between items-center text-sm">
                  <span className="text-muted-foreground">
                    Last Sold {corelogic.last_sold_date}
                  </span>
                  <span>{formatCurrency(corelogic.last_sold_price)}</span>
                </div>
              )}

              {corelogic.rental_estimate?.mid && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Est. Rent</span>
                  <span className="font-medium">
                    ${corelogic.rental_estimate.mid}/week
                  </span>
                </div>
              )}

              {corelogic.gross_yield_estimate && (
                <div className="flex justify-between items-center border-t pt-2">
                  <span className="text-sm text-muted-foreground">Gross Yield</span>
                  <span className="font-semibold text-primary">
                    {formatPercent(corelogic.gross_yield_estimate)}
                  </span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Agent */}
        {property.agent?.name && (
          <div className="text-sm text-muted-foreground">
            Agent: {property.agent.name}
            {property.agent.agency && ` - ${property.agent.agency}`}
          </div>
        )}
      </CardContent>
    </Card>
  )
}







