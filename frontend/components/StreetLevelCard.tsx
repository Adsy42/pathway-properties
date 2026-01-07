'use client'

import { CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { StreetLevelAnalysis } from '@/lib/api'

interface StreetLevelCardProps {
  analysis: StreetLevelAnalysis
  verdict: 'PROCEED' | 'REVIEW' | 'REJECT'
  killReasons: string[]
}

const getScoreIcon = (score: 'PASS' | 'WARNING' | 'FAIL') => {
  switch (score) {
    case 'PASS':
      return <CheckCircle className="h-5 w-5 text-green-500" />
    case 'WARNING':
      return <AlertTriangle className="h-5 w-5 text-yellow-500" />
    case 'FAIL':
      return <XCircle className="h-5 w-5 text-red-500" />
  }
}

const getScoreBadge = (score: 'PASS' | 'WARNING' | 'FAIL') => {
  switch (score) {
    case 'PASS':
      return <Badge variant="success">PASS</Badge>
    case 'WARNING':
      return <Badge variant="warning">WARNING</Badge>
    case 'FAIL':
      return <Badge variant="destructive">FAIL</Badge>
  }
}

const getVerdictStyle = (verdict: string) => {
  switch (verdict) {
    case 'PROCEED':
      return 'bg-green-500'
    case 'REVIEW':
      return 'bg-yellow-500'
    case 'REJECT':
      return 'bg-red-500'
    default:
      return 'bg-gray-500'
  }
}

export function StreetLevelCard({ analysis, verdict, killReasons }: StreetLevelCardProps) {
  const checks = [
    {
      name: 'Social Housing',
      check: analysis.social_housing,
      detail: `${analysis.social_housing.density_percent.toFixed(1)}% in area`,
    },
    {
      name: 'Flight Path',
      check: analysis.flight_path,
      detail: `ANEF: ${analysis.flight_path.anef}, N70: ${analysis.flight_path.n70}`,
    },
    {
      name: 'Flood Risk',
      check: analysis.flood_risk,
      detail: analysis.flood_risk.aep_1_percent ? '1% AEP Zone' : 'Not in flood zone',
    },
    {
      name: 'Bushfire Risk',
      check: analysis.bushfire_risk,
      detail: analysis.bushfire_risk.bal_rating || 'Not in BAL zone',
    },
    {
      name: 'Zoning',
      check: analysis.zoning,
      detail: `${analysis.zoning.code}${analysis.zoning.overlays.length > 0 ? ` + ${analysis.zoning.overlays.length} overlays` : ''}`,
    },
  ]

  return (
    <Card className="overflow-hidden">
      {/* Verdict Banner */}
      <div className={`${getVerdictStyle(verdict)} px-6 py-4 text-white`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Street Level Verdict</h3>
            <p className="text-white/80 text-sm">Gatekeeper Analysis</p>
          </div>
          <div className="text-3xl font-bold">{verdict}</div>
        </div>
      </div>

      <CardContent className="pt-6">
        {/* Kill Reasons */}
        {killReasons.length > 0 && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <h4 className="font-semibold text-red-700 mb-2">Kill Criteria Triggered</h4>
            <ul className="space-y-1">
              {killReasons.map((reason, i) => (
                <li key={i} className="text-red-600 text-sm flex items-start gap-2">
                  <XCircle className="h-4 w-4 mt-0.5 shrink-0" />
                  {reason}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Checks Grid */}
        <div className="space-y-3">
          {checks.map((item) => (
            <div
              key={item.name}
              className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                {getScoreIcon(item.check.score)}
                <div>
                  <p className="font-medium">{item.name}</p>
                  <p className="text-sm text-muted-foreground">{item.detail}</p>
                </div>
              </div>
              {getScoreBadge(item.check.score)}
            </div>
          ))}
        </div>

        {/* Details Expandable */}
        <details className="mt-4">
          <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground flex items-center gap-1">
            <Info className="h-4 w-4" />
            View detailed analysis
          </summary>
          <div className="mt-3 p-4 bg-slate-50 rounded-lg text-sm space-y-2">
            {checks.map((item) => (
              <div key={item.name}>
                <span className="font-medium">{item.name}:</span>{' '}
                <span className="text-muted-foreground">{item.check.details}</span>
              </div>
            ))}
          </div>
        </details>
      </CardContent>
    </Card>
  )
}







