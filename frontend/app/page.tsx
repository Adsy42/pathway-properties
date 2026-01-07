'use client'

import { useState } from 'react'
import { Building2 } from 'lucide-react'
import { PropertyInput } from '@/components/PropertyInput'
import { PropertyCard } from '@/components/PropertyCard'
import { StreetLevelCard } from '@/components/StreetLevelCard'
import { DocumentUpload } from '@/components/DocumentUpload'
import { AnalysisDashboard } from '@/components/AnalysisDashboard'
import { PropertyAnalyzeResponse } from '@/lib/api'

type Stage = 'input' | 'street-level' | 'documents' | 'analysis'

export default function Home() {
  const [stage, setStage] = useState<Stage>('input')
  const [analysisData, setAnalysisData] = useState<PropertyAnalyzeResponse | null>(null)

  const handleAnalysisComplete = (data: PropertyAnalyzeResponse) => {
    setAnalysisData(data)
    setStage('street-level')
  }

  const handleProceedToDocuments = () => {
    setStage('documents')
  }

  const handleProceedToAnalysis = () => {
    setStage('analysis')
  }

  const handleStartOver = () => {
    setStage('input')
    setAnalysisData(null)
  }

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div 
              className="flex items-center gap-2 cursor-pointer" 
              onClick={handleStartOver}
            >
              <Building2 className="h-8 w-8 text-primary" />
              <span className="text-xl font-bold">Pathway Property</span>
            </div>
            
            {/* Stage Indicator */}
            {stage !== 'input' && (
              <div className="hidden sm:flex items-center gap-2 text-sm">
                <span className={stage === 'street-level' ? 'font-semibold text-primary' : 'text-muted-foreground'}>
                  1. Street Level
                </span>
                <span className="text-muted-foreground">→</span>
                <span className={stage === 'documents' ? 'font-semibold text-primary' : 'text-muted-foreground'}>
                  2. Documents
                </span>
                <span className="text-muted-foreground">→</span>
                <span className={stage === 'analysis' ? 'font-semibold text-primary' : 'text-muted-foreground'}>
                  3. Analysis
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {/* Input Stage */}
        {stage === 'input' && (
          <div className="max-w-4xl mx-auto pt-20">
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold mb-4">
                AI-Powered Property Due Diligence
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Analyze any Australian property in minutes. Get comprehensive risk 
                assessment, legal analysis, and investment insights powered by AI.
              </p>
            </div>
            
            <PropertyInput onAnalysisComplete={handleAnalysisComplete} />
            
            {/* Features */}
            <div className="grid md:grid-cols-3 gap-6 mt-16">
              <div className="text-center p-6">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">🏠</span>
                </div>
                <h3 className="font-semibold mb-2">Street Level Analysis</h3>
                <p className="text-sm text-muted-foreground">
                  Instant checks for social housing, flood risk, flight paths, and zoning
                </p>
              </div>
              <div className="text-center p-6">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">📄</span>
                </div>
                <h3 className="font-semibold mb-2">Document Intelligence</h3>
                <p className="text-sm text-muted-foreground">
                  AI reads Section 32s, contracts, and reports to extract key risks
                </p>
              </div>
              <div className="text-center p-6">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">💰</span>
                </div>
                <h3 className="font-semibold mb-2">Investment Analysis</h3>
                <p className="text-sm text-muted-foreground">
                  Yield calculations, value-add opportunities, and sweat equity potential
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Street Level Stage */}
        {stage === 'street-level' && analysisData && (
          <div className="max-w-5xl mx-auto">
            <div className="grid lg:grid-cols-2 gap-6">
              <PropertyCard property={analysisData.property} />
              <StreetLevelCard 
                analysis={analysisData.street_level_analysis}
                verdict={analysisData.verdict}
                killReasons={analysisData.kill_reasons}
              />
            </div>
            
            {/* Action Buttons */}
            <div className="mt-6 flex justify-center gap-4">
              <button
                onClick={handleStartOver}
                className="px-6 py-2 text-sm border rounded-lg hover:bg-slate-50"
              >
                Start Over
              </button>
              
              <button
                onClick={handleProceedToDocuments}
                className={`px-6 py-2 text-sm text-white rounded-lg ${
                  analysisData.verdict === 'REJECT' 
                    ? 'bg-yellow-500 hover:bg-yellow-600' 
                    : 'bg-primary hover:bg-primary/90'
                }`}
              >
                Continue to Document Upload →
                {analysisData.verdict === 'REJECT' && (
                  <span className="ml-2 text-xs opacity-75">(Kill criteria triggered)</span>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Documents Stage */}
        {stage === 'documents' && analysisData && (
          <div className="max-w-3xl mx-auto">
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2">Upload Documents</h2>
              <p className="text-muted-foreground">
                Upload property documents for AI analysis. Supported: Section 32, 
                contracts, building reports, pest reports, strata documents.
              </p>
            </div>
            
            <DocumentUpload 
              propertyId={analysisData.id}
              onComplete={handleProceedToAnalysis}
            />
            
            <div className="mt-4 flex justify-between">
              <button
                onClick={() => setStage('street-level')}
                className="px-6 py-2 text-sm border rounded-lg hover:bg-slate-50"
              >
                ← Back
              </button>
              <button
                onClick={handleProceedToAnalysis}
                className="px-6 py-2 text-sm text-muted-foreground hover:text-foreground"
              >
                Skip documents →
              </button>
            </div>
          </div>
        )}

        {/* Analysis Stage */}
        {stage === 'analysis' && analysisData && (
          <div className="max-w-4xl mx-auto">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-1">Analysis Dashboard</h2>
                <p className="text-muted-foreground">{analysisData.property.address}</p>
              </div>
              <button
                onClick={handleStartOver}
                className="px-4 py-2 text-sm border rounded-lg hover:bg-slate-50"
              >
                New Analysis
              </button>
            </div>
            
            <AnalysisDashboard 
              propertyId={analysisData.id}
              propertyAddress={analysisData.property.address}
            />
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="border-t mt-auto py-6 bg-white">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>
            This tool provides preliminary analysis only. Always seek independent 
            legal, financial, and building advice before purchasing property.
          </p>
        </div>
      </footer>
    </main>
  )
}




