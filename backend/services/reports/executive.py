"""
Executive PDF report generation.
"""

from typing import Dict, Any
import os
from datetime import datetime

from database import Property, Analysis
from config import get_settings

settings = get_settings()


async def generate_executive_report(
    property_data: Property,
    analysis: Analysis
) -> str:
    """
    Generate PDF executive report.
    
    Returns path to generated PDF.
    """
    
    # Create reports directory
    reports_dir = os.path.join(settings.cache_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pathway_report_{property_data.id[:8]}_{timestamp}.pdf"
    filepath = os.path.join(reports_dir, filename)
    
    try:
        # Try to use WeasyPrint for HTML-to-PDF
        return await generate_with_weasyprint(filepath, property_data, analysis)
    except ImportError:
        # Fallback to simple text report
        return await generate_simple_report(filepath, property_data, analysis)


async def generate_with_weasyprint(
    filepath: str,
    property_data: Property,
    analysis: Analysis
) -> str:
    """Generate PDF using WeasyPrint."""
    
    from weasyprint import HTML
    
    html_content = generate_html_report(property_data, analysis)
    
    HTML(string=html_content).write_pdf(filepath)
    
    return filepath


def generate_html_report(property_data: Property, analysis: Analysis) -> str:
    """Generate HTML content for report."""
    
    address = property_data.address or "Unknown Address"
    verdict = property_data.verdict or "REVIEW"
    summary = analysis.summary or {}
    legal = analysis.legal_analysis or {}
    financial = analysis.financial_analysis or {}
    sweat_equity = analysis.sweat_equity or {}
    
    # Verdict color
    verdict_colors = {
        "PROCEED": "#22c55e",
        "REVIEW": "#eab308",
        "REJECT": "#ef4444"
    }
    verdict_color = verdict_colors.get(verdict, "#eab308")
    
    # Risk color
    risk = summary.get("overall_risk", "MEDIUM")
    risk_colors = {"LOW": "#22c55e", "MEDIUM": "#eab308", "HIGH": "#ef4444"}
    risk_color = risk_colors.get(risk, "#eab308")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 11pt;
                line-height: 1.5;
                color: #1f2937;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid #3b82f6;
            }}
            .header h1 {{
                color: #3b82f6;
                font-size: 24pt;
                margin: 0;
            }}
            .header h2 {{
                color: #6b7280;
                font-size: 14pt;
                font-weight: normal;
                margin: 10px 0 0 0;
            }}
            .verdict-box {{
                background: {verdict_color};
                color: white;
                padding: 15px 25px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
            }}
            .verdict-box h3 {{
                margin: 0;
                font-size: 18pt;
            }}
            .section {{
                margin: 25px 0;
            }}
            .section h3 {{
                color: #3b82f6;
                border-bottom: 1px solid #e5e7eb;
                padding-bottom: 5px;
                margin-bottom: 15px;
            }}
            .risk-badge {{
                display: inline-block;
                padding: 3px 10px;
                border-radius: 4px;
                font-size: 10pt;
                font-weight: bold;
            }}
            .risk-high {{ background: #fef2f2; color: #dc2626; }}
            .risk-medium {{ background: #fefce8; color: #ca8a04; }}
            .risk-low {{ background: #f0fdf4; color: #16a34a; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }}
            th, td {{
                text-align: left;
                padding: 8px 12px;
                border-bottom: 1px solid #e5e7eb;
            }}
            th {{
                background: #f9fafb;
                font-weight: 600;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
                font-size: 9pt;
                color: #9ca3af;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>PATHWAY PROPERTY</h1>
            <h2>Investment Analysis Report</h2>
        </div>
        
        <div class="section">
            <h3>Property Details</h3>
            <table>
                <tr><th>Address</th><td>{address}</td></tr>
                <tr><th>Analysis Date</th><td>{datetime.now().strftime('%d %B %Y')}</td></tr>
                <tr><th>Street Level Verdict</th><td>{verdict}</td></tr>
            </table>
        </div>
        
        <div class="verdict-box" style="background: {risk_color};">
            <h3>OVERALL ASSESSMENT: {risk}</h3>
            <p style="margin: 10px 0 0 0;">Recommendation: {summary.get('recommendation', 'PROCEED_WITH_CAUTION')}</p>
        </div>
        
        <div class="section">
            <h3>Executive Summary</h3>
            <p>{summary.get('executive_summary', 'Analysis pending.')}</p>
        </div>
        
        <div class="section">
            <h3>Key Risks</h3>
            <table>
                <tr><th>Category</th><th>Issue</th><th>Severity</th><th>Mitigation</th></tr>
    """
    
    for risk in summary.get("top_risks", [])[:5]:
        severity = risk.get("severity", "MEDIUM")
        severity_class = f"risk-{severity.lower()}"
        html += f"""
                <tr>
                    <td>{risk.get('category', '-')}</td>
                    <td>{risk.get('issue', '-')}</td>
                    <td><span class="risk-badge {severity_class}">{severity}</span></td>
                    <td>{risk.get('mitigation', '-')}</td>
                </tr>
        """
    
    if not summary.get("top_risks"):
        html += "<tr><td colspan='4' style='text-align:center;color:#9ca3af;'>No significant risks identified</td></tr>"
    
    html += """
            </table>
        </div>
        
        <div class="section">
            <h3>Value-Add Opportunities</h3>
            <table>
                <tr><th>Type</th><th>Description</th><th>Est. Value Add</th></tr>
    """
    
    for opp in summary.get("top_opportunities", [])[:3]:
        html += f"""
                <tr>
                    <td>{opp.get('type', '-')}</td>
                    <td>{opp.get('description', '-')}</td>
                    <td>${opp.get('value', 0):,}</td>
                </tr>
        """
    
    if not summary.get("top_opportunities"):
        html += "<tr><td colspan='3' style='text-align:center;color:#9ca3af;'>No opportunities identified</td></tr>"
    
    html += """
            </table>
        </div>
        
        <div class="section">
            <h3>Financial Summary</h3>
            <table>
    """
    
    yield_data = financial.get("yield_analysis", {})
    if yield_data.get("gross"):
        html += f"<tr><th>Gross Yield</th><td>{yield_data['gross']:.1f}%</td></tr>"
    if yield_data.get("net"):
        html += f"<tr><th>Net Yield</th><td>{yield_data['net']:.1f}%</td></tr>"
    if yield_data.get("cashflow_monthly"):
        html += f"<tr><th>Monthly Cashflow (80% LVR)</th><td>${yield_data['cashflow_monthly']:,.0f}</td></tr>"
    
    outgoings = financial.get("outgoings", {})
    if outgoings.get("total_annual"):
        html += f"<tr><th>Total Annual Outgoings</th><td>${outgoings['total_annual']:,}</td></tr>"
    
    html += """
            </table>
        </div>
        
        <div class="footer">
            <p>This report is generated by AI and serves as a preliminary guide only.<br>
            It does not constitute legal, financial, or professional advice.<br>
            Always seek independent professional advice before making investment decisions.</p>
            <p>Generated: """ + datetime.now().strftime('%d/%m/%Y %H:%M') + """</p>
        </div>
    </body>
    </html>
    """
    
    return html


async def generate_simple_report(
    filepath: str,
    property_data: Property,
    analysis: Analysis
) -> str:
    """Generate simple text report as fallback."""
    
    # Create a simple text file instead
    text_path = filepath.replace(".pdf", ".txt")
    
    content = f"""
PATHWAY PROPERTY - INVESTMENT ANALYSIS REPORT
{'=' * 50}

Property: {property_data.address or 'Unknown'}
Date: {datetime.now().strftime('%d %B %Y')}
Verdict: {property_data.verdict or 'REVIEW'}

SUMMARY
{'-' * 50}
{(analysis.summary or {}).get('executive_summary', 'Analysis pending.')}

Overall Risk: {(analysis.summary or {}).get('overall_risk', 'MEDIUM')}
Recommendation: {(analysis.summary or {}).get('recommendation', 'PROCEED_WITH_CAUTION')}

{'=' * 50}
This report is AI-generated and serves as a preliminary guide only.
It does not constitute legal, financial, or professional advice.
"""
    
    with open(text_path, "w") as f:
        f.write(content)
    
    return text_path







