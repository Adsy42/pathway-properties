'use client'

import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { 
  FileText, Scale, Hammer, DollarSign, Sparkles, Download, Loader2,
  AlertTriangle, CheckCircle, TrendingUp
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { runAnalysis, getAnalysis, generateReport, AnalysisResponse } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'

interface AnalysisDashboardProps {
  propertyId: string
  propertyAddress: string
}

export function AnalysisDashboard({ propertyId, propertyAddress }: AnalysisDashboardProps) {
  const [activeTab, setActiveTab] = useState<'summary' | 'legal' | 'physical' | 'financial' | 'sweat'>('summary')

  // Fetch or run analysis
  const { data: analysis, isLoading, refetch } = useQuery({
    queryKey: ['analysis', propertyId],
    queryFn: () => getAnalysis(propertyId).catch(() => null),
    retry: false,
  })

  const runMutation = useMutation({
    mutationFn: () => runAnalysis(propertyId),
    onSuccess: () => refetch(),
  })

  const reportMutation = useMutation({
    mutationFn: () => generateReport(propertyId),
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `pathway-report-${propertyId.slice(0, 8)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    },
  })

  if (isLoading) {
    return (
      <Card className="p-8">
        <div className="flex items-center justify-center gap-3">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading analysis...</span>
        </div>
      </Card>
    )
  }

  if (!analysis) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Asset Analysis</CardTitle>
        </CardHeader>
        <CardContent className="text-center py-8">
          <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground mb-4">
            No analysis found. Run full analysis on uploaded documents.
          </p>
          <Button 
            onClick={() => runMutation.mutate()} 
            disabled={runMutation.isPending}
          >
            {runMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              'Run Full Analysis'
            )}
          </Button>
        </CardContent>
      </Card>
    )
  }

  const summary = analysis.summary
  const riskColor = {
    LOW: 'text-green-600 bg-green-50 border-green-200',
    MEDIUM: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    HIGH: 'text-red-600 bg-red-50 border-red-200',
  }[summary?.overall_risk || 'MEDIUM']

  const tabs = [
    { id: 'summary', label: 'Summary', icon: FileText },
    { id: 'legal', label: 'Legal', icon: Scale },
    { id: 'physical', label: 'Physical', icon: Hammer },
    { id: 'financial', label: 'Financial', icon: DollarSign },
    { id: 'sweat', label: 'Sweat Equity', icon: Sparkles },
  ] as const

  return (
    <div className="space-y-4">
      {/* Summary Banner */}
      <Card className={`border-2 ${riskColor}`}>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium opacity-75">Overall Assessment</p>
              <p className="text-2xl font-bold">{summary?.overall_risk || 'N/A'} RISK</p>
              <p className="text-sm mt-1">{summary?.recommendation?.replace(/_/g, ' ')}</p>
            </div>
            <Button 
              variant="outline" 
              onClick={() => reportMutation.mutate()}
              disabled={reportMutation.isPending}
            >
              {reportMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              Download Report
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tab Navigation */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {tabs.map((tab) => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveTab(tab.id)}
            className="shrink-0"
          >
            <tab.icon className="h-4 w-4 mr-2" />
            {tab.label}
          </Button>
        ))}
      </div>

      {/* Tab Content */}
      <Card>
        <CardContent className="pt-6">
          {activeTab === 'summary' && (
            <div className="space-y-6">
              <div>
                <h3 className="font-semibold mb-2">Executive Summary</h3>
                <p className="text-muted-foreground">
                  {summary?.executive_summary || 'Analysis complete.'}
                </p>
              </div>

              {summary?.top_risks && summary.top_risks.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                    Key Risks
                  </h3>
                  <div className="space-y-2">
                    {summary.top_risks.map((risk, i) => (
                      <div key={i} className="flex items-start gap-3 p-3 bg-red-50 rounded-lg">
                        <Badge variant={risk.severity === 'HIGH' ? 'destructive' : 'warning'}>
                          {risk.severity}
                        </Badge>
                        <div>
                          <p className="font-medium">{risk.issue}</p>
                          <p className="text-sm text-muted-foreground">{risk.category}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {summary?.top_opportunities && summary.top_opportunities.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-green-500" />
                    Opportunities
                  </h3>
                  <div className="space-y-2">
                    {summary.top_opportunities.map((opp, i) => (
                      <div key={i} className="flex items-start justify-between p-3 bg-green-50 rounded-lg">
                        <div>
                          <p className="font-medium">{opp.type}</p>
                          <p className="text-sm text-muted-foreground">{opp.description}</p>
                        </div>
                        <Badge variant="success">+{formatCurrency(opp.value)}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'legal' && (
            <div className="space-y-4">
              <h3 className="font-semibold">Legal Analysis</h3>
              {analysis.legal ? (
                <div className="grid gap-4">
                  {analysis.legal.title && (
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <p className="font-medium">Title</p>
                      <p className="text-sm text-muted-foreground">
                        Proprietor: {analysis.legal.title.proprietor || 'N/A'}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        {analysis.legal.title.vendor_match ? (
                          <Badge variant="success">Vendor Match ✓</Badge>
                        ) : (
                          <Badge variant="destructive">Vendor Mismatch</Badge>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {analysis.legal.caveats?.length > 0 && (
                    <div className="p-4 bg-yellow-50 rounded-lg">
                      <p className="font-medium text-yellow-700">
                        {analysis.legal.caveats.length} Caveat(s) Found
                      </p>
                    </div>
                  )}

                  {analysis.legal.cooling_off_waived && (
                    <div className="p-4 bg-red-50 rounded-lg">
                      <p className="font-medium text-red-700">
                        ⚠️ Cooling-off period waived (s66W)
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-muted-foreground">No legal documents analyzed</p>
              )}
            </div>
          )}

          {activeTab === 'physical' && (
            <div className="space-y-4">
              <h3 className="font-semibold">Physical Analysis</h3>
              {analysis.physical?.defects_detected?.length > 0 ? (
                <div className="space-y-2">
                  {analysis.physical.defects_detected.map((defect: any, i: number) => (
                    <div key={i} className="p-3 bg-slate-50 rounded-lg">
                      <div className="flex justify-between">
                        <p className="font-medium">{defect.type}</p>
                        <Badge variant={defect.severity === 'Major' ? 'destructive' : 'secondary'}>
                          {defect.severity}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{defect.location}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center gap-2 text-green-600">
                  <CheckCircle className="h-5 w-5" />
                  <span>No significant defects detected</span>
                </div>
              )}
            </div>
          )}

          {activeTab === 'financial' && (
            <div className="space-y-4">
              <h3 className="font-semibold">Financial Analysis</h3>
              {analysis.financial?.yield_analysis && (
                <div className="grid gap-4 sm:grid-cols-2">
                  {analysis.financial.yield_analysis.gross && (
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-muted-foreground">Gross Yield</p>
                      <p className="text-2xl font-bold text-primary">
                        {analysis.financial.yield_analysis.gross.toFixed(1)}%
                      </p>
                    </div>
                  )}
                  {analysis.financial.yield_analysis.net && (
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-muted-foreground">Net Yield</p>
                      <p className="text-2xl font-bold">
                        {analysis.financial.yield_analysis.net.toFixed(1)}%
                      </p>
                    </div>
                  )}
                  {analysis.financial.yield_analysis.cashflow_monthly && (
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-muted-foreground">Monthly Cashflow</p>
                      <p className={`text-2xl font-bold ${analysis.financial.yield_analysis.cashflow_monthly >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(analysis.financial.yield_analysis.cashflow_monthly)}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'sweat' && (
            <div className="space-y-4">
              <h3 className="font-semibold">Sweat Equity Opportunities</h3>
              {analysis.sweat_equity?.opportunities?.length > 0 ? (
                <div className="space-y-3">
                  {analysis.sweat_equity.opportunities.map((opp: any, i: number) => (
                    <div key={i} className="p-4 bg-green-50 border border-green-200 rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <p className="font-semibold">{opp.type}</p>
                        <Badge variant="success">
                          ROI: {opp.roi_months} months
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">{opp.description}</p>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground">Cost</p>
                          <p className="font-medium">{formatCurrency(opp.estimated_cost)}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Value Add</p>
                          <p className="font-medium text-green-600">+{formatCurrency(opp.value_add)}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Rent Increase</p>
                          <p className="font-medium">+${opp.rent_increase_weekly}/wk</p>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  <div className="p-4 bg-primary/5 rounded-lg">
                    <div className="flex justify-between">
                      <span>Total Value Add Potential</span>
                      <span className="font-bold text-primary">
                        {formatCurrency(analysis.sweat_equity.total_value_add_potential)}
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-muted-foreground">No sweat equity opportunities identified</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}







