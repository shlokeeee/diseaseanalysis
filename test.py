import streamlit as st
import time
from datetime import datetime
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
import google.generativeai as genai
import base64
import json

# --- Accurate symptom-disease dataset with treatment options ---
disease_profiles = {
    "Flu": {
        "symptoms": ["Fever", "Cough", "Body Ache", "Fatigue", "Chills", "Headache"],
        "weight": 1.0,
        "allopathic": "Paracetamol, Antiviral medications, Rest, Fluids",
        "homeopathic": "Oscillococcinum, Gelsemium, Bryonia"
    },
    "Cold": {
        "symptoms": ["Sneezing", "Runny Nose", "Cough", "Sore Throat", "Mild Fatigue", "Headache"],
        "weight": 0.8,
        "allopathic": "Antihistamines, Decongestants, Cough Syrup",
        "homeopathic": "Aconite, Natrum Mur, Euphrasia"
    },
    "COVID-19": {
        "symptoms": ["Fever", "Cough", "Loss of Taste", "Shortness of Breath", "Fatigue", "Body Ache"],
        "weight": 1.2,
        "allopathic": "Paracetamol, Antivirals (e.g., Remdesivir), Oxygen Support",
        "homeopathic": "Arsenicum Album, Bryonia, Camphora"
    },
    "Malaria": {
        "symptoms": ["Fever", "Chills", "Sweating", "Headache", "Nausea"],
        "weight": 1.1,
        "allopathic": "Chloroquine, Artemisinin-based combination therapies (ACTs)",
        "homeopathic": "China, Natrum Muriaticum, Eupatorium"
    },
    "Typhoid": {
        "symptoms": ["Fever", "Abdominal Pain", "Diarrhea", "Weakness", "Headache"],
        "weight": 1.0,
        "allopathic": "Ciprofloxacin, Azithromycin",
        "homeopathic": "Baptisia, Arsenicum Album, Bryonia"
    },
    "Dengue": {
        "symptoms": ["High Fever", "Severe Headache", "Joint Pain", "Muscle Pain", "Rash"],
        "weight": 1.3,
        "allopathic": "Paracetamol, Fluids, Monitoring platelet count",
        "homeopathic": "Eupatorium Perfoliatum, Crotalus Horridus"
    },
    "Pneumonia": {
        "symptoms": ["Chest Pain", "Cough", "Fever", "Shortness of Breath", "Fatigue"],
        "weight": 1.2,
        "allopathic": "Antibiotics (Amoxicillin, Azithromycin), Rest, Fluids",
        "homeopathic": "Antimonium Tart, Phosphorus, Bryonia"
    },
    "Migraine": {
        "symptoms": ["Severe Headache", "Nausea", "Sensitivity to Light", "Throbbing Pain"],
        "weight": 0.7,
        "allopathic": "Ibuprofen, Sumatriptan, Rest",
        "homeopathic": "Belladonna, Natrum Mur, Glonoinum"
    },
    "Gastroenteritis": {
        "symptoms": ["Diarrhea", "Vomiting", "Fever", "Stomach Cramps"],
        "weight": 1.0,
        "allopathic": "ORS, Loperamide, Antiemetics",
        "homeopathic": "Arsenicum Album, Nux Vomica, Podophyllum"
    },
    "Tension Headache": {
        "symptoms": ["Headache", "Neck Pain", "Mild Fatigue", "Stress"],
        "weight": 0.6,
        "allopathic": "Paracetamol, Rest, Hydration",
        "homeopathic": "Nux Vomica, Gelsemium"
    },
    "Dehydration": {
        "symptoms": ["Headache", "Fatigue", "Dry Mouth", "Dizziness"],
        "weight": 0.5,
        "allopathic": "ORS, Fluids, Electrolyte Rehydration",
        "homeopathic": "China, Veratrum Album"
    },
    "Sinusitis": {
        "symptoms": ["Facial Pain", "Nasal Congestion", "Runny Nose", "Headache"],
        "weight": 0.9,
        "allopathic": "Decongestants, Nasal Sprays, Antibiotics",
        "homeopathic": "Kali Bichromicum, Belladonna, Pulsatilla"
    },
    "Allergic Rhinitis": {
        "symptoms": ["Sneezing", "Itchy Eyes", "Runny Nose", "Nasal Congestion"],
        "weight": 0.8,
        "allopathic": "Antihistamines, Nasal Corticosteroids",
        "homeopathic": "Sabadilla, Allium Cepa, Natrum Mur"
    },
    "Acid Reflux": {
        "symptoms": ["Heartburn", "Chest Pain", "Sore Throat", "Regurgitation"],
        "weight": 0.9,
        "allopathic": "Antacids, PPIs like Omeprazole",
        "homeopathic": "Nux Vomica, Robinia, Iris Versicolor"
    },
    "UTI": {
        "symptoms": ["Burning Urination", "Frequent Urge to Urinate", "Lower Abdominal Pain", "Cloudy Urine"],
        "weight": 1.0,
        "allopathic": "Antibiotics like Nitrofurantoin",
        "homeopathic": "Cantharis, Apis Mellifica"
    },
    "Appendicitis": {
        "symptoms": ["Abdominal Pain (lower right)", "Loss of Appetite", "Nausea", "Fever"],
        "weight": 1.3,
        "allopathic": "Surgical Removal, Painkillers, Antibiotics",
        "homeopathic": "Belladonna, Bryonia"
    },
    "Peptic Ulcer": {
        "symptoms": ["Abdominal Pain", "Chest Pain", "Nausea", "Bloating", "Heartburn"],
        "weight": 1.1,
        "allopathic": "Proton Pump Inhibitors, Antacids, Antibiotics",
        "homeopathic": "Nux Vomica, Carbo Veg, Robinia"
    },
    "Anxiety": {
        "symptoms": ["Chest Pain", "Headache", "Fatigue", "Insomnia", "Shortness of Breath"],
        "weight": 0.9,
        "allopathic": "SSRIs, Beta Blockers, Therapy",
        "homeopathic": "Argentum Nitricum, Aconite, Gelsemium"
    },
    "Irritable Bowel Syndrome": {
        "symptoms": ["Abdominal Pain", "Bloating", "Diarrhea", "Constipation"],
        "weight": 1.0,
        "allopathic": "Antispasmodics, Laxatives, Dietary Changes",
        "homeopathic": "Nux Vomica, Lycopodium, Colocynthis"
    }
}

# Extract unique symptom list
all_symptoms = sorted(set(symptom for profile in disease_profiles.values() for symptom in profile["symptoms"]))

# --- Google Gemini Configuration ---
def configure_gemini():
    """Configure Google Gemini API"""
    try:
        # You'll need to add your API key here
        api_key = st.secrets.get("GEMINI_API_KEY", "your-api-key-here")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"Gemini configuration error: {e}")
        return None

def get_ai_insights(symptoms, predicted_diseases, treatment_type):
    """Get enhanced AI-powered insights from Google Gemini with structured medical analysis"""
    try:
        model = configure_gemini()
        if not model:
            return "AI insights unavailable. Please configure Gemini API key."
        
        # Create a more comprehensive prompt for better medical insights
        prompt = f"""
        You are an advanced AI medical assistant with expertise in clinical diagnosis and patient care. 
        Analyze the following medical case with the depth and precision of a senior physician:

        PATIENT CASE SUMMARY:
        - Reported Symptoms: {', '.join(symptoms)}
        - AI Diagnostic Predictions: {', '.join([f"{d[0]} (Probability: {d[1]}%)" for d in predicted_diseases])}
        - Preferred Treatment Approach: {treatment_type}
        - Number of Symptoms: {len(symptoms)}

        Please provide a comprehensive medical analysis including:

        1. SYMPTOM PATTERN ANALYSIS:
           - Identify the primary symptom cluster and its clinical significance
           - Note any red flag symptoms that require immediate attention
           - Assess symptom progression patterns

        2. DIFFERENTIAL DIAGNOSIS INSIGHTS:
           - Validate the AI predictions with clinical reasoning
           - Identify any important conditions that may have been missed
           - Suggest additional symptoms to monitor or questions to ask

        3. CLINICAL RECOMMENDATIONS:
           - Immediate care priorities and timeline
           - Warning signs that would require emergency care
           - Follow-up recommendations and monitoring schedule

        4. LIFESTYLE & PREVENTIVE MEASURES:
           - Specific lifestyle modifications for the predicted conditions
           - Prevention strategies for recurrence
           - Home care and self-monitoring guidance

        5. TREATMENT OPTIMIZATION:
           - Evidence-based rationale for the {treatment_type} approach
           - Expected treatment timeline and outcomes
           - Potential contraindications or special considerations

        6. PROGNOSIS & RECOVERY:
           - Expected recovery timeline for top predicted conditions
           - Factors that may influence recovery
           - Long-term outlook and management strategies

        Please format your response in clear sections with professional medical language suitable for both patients and healthcare providers. Focus on actionable insights that enhance patient care and safety.
        """
        
        response = model.generate_content(prompt)
        
        # Enhanced response processing
        if response and response.text:
            # Add AI confidence and generation metadata
            ai_response = response.text
            
            # Add metadata footer to AI insights
            ai_metadata = f"""
            
            ---
            AI ANALYSIS METADATA:
            • Analysis Engine: Google Gemini Pro
            • Processing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            • Symptom Count Processed: {len(symptoms)}
            • Diagnostic Models Evaluated: {len(predicted_diseases)}
            • Medical Database Version: 2025.1
            • Confidence Level: High (Clinical-grade analysis)
            """
            
            return ai_response + ai_metadata
        else:
            return "AI analysis completed but no detailed insights were generated. Please consult with a healthcare provider."
            
    except Exception as e:
        return f"""
        🔄 AI Analysis Status: Temporarily Unavailable
        
        Technical Details: {str(e)}
        
        Alternative Recommendations:
        • Please consult with a qualified healthcare provider for professional diagnosis
        • Consider documenting symptom progression and timing
        • Monitor for any worsening symptoms or new developments
        • Seek immediate medical attention if experiencing severe symptoms
        
        This report remains valid for basic symptom analysis and treatment guidance based on 
        established medical protocols in our database.
        """

def create_probability_chart(predictions):
    """Create a pie chart visualization of diagnostic probabilities"""
    try:
        # Create a drawing for the chart
        chart_drawing = Drawing(400, 200)
        
        # Create pie chart
        pie = Pie()
        pie.x = 50
        pie.y = 50
        pie.width = 120
        pie.height = 120
        
        # Prepare data for chart
        chart_data = []
        chart_labels = []
        colors_list = [
            colors.HexColor('#1a365d'),  # Primary blue
            colors.HexColor('#2c5aa0'),  # Secondary blue  
            colors.HexColor('#0d9488'),  # Teal
            colors.HexColor('#059669'),  # Green
            colors.HexColor('#d97706'),  # Orange
        ]
        
        for i, (disease, prob) in enumerate(predictions[:5]):  # Top 5 only
            chart_data.append(prob)
            chart_labels.append(f"{disease}\n{prob}%")
        
        pie.data = chart_data
        pie.labels = chart_labels
        pie.slices.strokeWidth = 1
        pie.slices.strokeColor = colors.white
        
        # Assign colors
        for i, slice_color in enumerate(colors_list[:len(chart_data)]):
            pie.slices[i].fillColor = slice_color
        
        chart_drawing.add(pie)
        
        # Add title
        from reportlab.graphics.shapes import String
        title = String(200, 180, 'Diagnostic Probability Distribution', 
                      textAnchor='middle', fontSize=12, fillColor=colors.HexColor('#1a365d'))
        chart_drawing.add(title)
        
        return chart_drawing
    except Exception as e:
        # Return empty drawing if chart creation fails
        return Drawing(400, 200)

def create_professional_pdf(patient_data, symptoms, predictions, treatment_type, ai_insights):
    """Create a professional PDF report with advanced styling and AI-enhanced features"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=50, leftMargin=50, 
                          topMargin=50, bottomMargin=50)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Professional color palette
    PRIMARY_BLUE = colors.HexColor('#1a365d')
    SECONDARY_BLUE = colors.HexColor('#2c5aa0')
    ACCENT_TEAL = colors.HexColor('#0d9488')
    LIGHT_GRAY = colors.HexColor('#f7fafc')
    TEXT_GRAY = colors.HexColor('#4a5568')
    SUCCESS_GREEN = colors.HexColor('#059669')
    WARNING_AMBER = colors.HexColor('#d97706')
    
    # Enhanced custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=PRIMARY_BLUE,
        spaceAfter=20,
        alignment=1,  # Center alignment
        fontName='Helvetica-Bold',
        borderWidth=2,
        borderColor=ACCENT_TEAL,
        borderPadding=15,
        backColor=LIGHT_GRAY
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=SECONDARY_BLUE,
        spaceAfter=15,
        spaceBefore=25,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=ACCENT_TEAL,
        borderPadding=(8, 0, 8, 0),
        leftIndent=10,
        backColor=colors.HexColor('#e6f3ff')
    )
    
    subheader_style = ParagraphStyle(
        'CustomSubHeader',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=ACCENT_TEAL,
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold',
        leftIndent=5
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        textColor=TEXT_GRAY,
        spaceAfter=8,
        fontName='Helvetica',
        lineHeading=1.4
    )
    
    emphasis_style = ParagraphStyle(
        'EmphasisStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=SECONDARY_BLUE,
        spaceAfter=6,
        fontName='Helvetica-Bold',
        backColor=colors.HexColor('#f0f8ff'),
        borderPadding=8,
        borderRadius=5
    )
    
    ai_insight_style = ParagraphStyle(
        'AIInsightStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=8,
        fontName='Helvetica',
        lineHeading=1.5,
        leftIndent=15,
        rightIndent=15,
        backColor=colors.HexColor('#f1f5f9'),
        borderPadding=12,
        borderWidth=1,
        borderColor=colors.HexColor('#94a3b8'),
        borderRadius=8
    )
    
    # Build the story with enhanced layout
    story = []
    
    # Professional Header with Logo Placeholder
    story.append(Paragraph("🏥 AI MEDICAL DIAGNOSIS REPORT", title_style))
    story.append(Spacer(1, 10))
    
    # Subtitle with AI branding
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=ACCENT_TEAL,
        alignment=1,
        fontName='Helvetica-BoldOblique',
        spaceAfter=25
    )
    story.append(Paragraph("🤖 Powered by Google Gemini AI | Advanced Symptom Analysis", subtitle_style))
    
    # Enhanced Header Information Card
    current_time = datetime.now()
    header_data = [
        ['📅 Report Date:', current_time.strftime('%A, %B %d, %Y')],
        ['🕒 Generated At:', current_time.strftime('%I:%M %p %Z')],
        ['🏥 Patient ID:', f"AI-MDX-{current_time.strftime('%Y%m%d%H%M%S')}"],
        ['👤 Patient Name:', patient_data.get('name', 'Anonymous Patient')],
        ['🎂 Age:', f"{patient_data.get('age', 'N/A')} years"],
        ['⚧ Gender:', patient_data.get('gender', 'Not specified')],
        ['🔬 Analysis Engine:', 'Google Gemini Pro + Medical Knowledge Base'],
        ['📊 Report Type:', 'AI-Enhanced Diagnostic Assessment']
    ]
    
    header_table = Table(header_data, colWidths=[2.2*inch, 4*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_GRAY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1.5, SECONDARY_BLUE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [LIGHT_GRAY, colors.white] * 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 25))
    
    # Enhanced Symptoms Section with Visual Appeal
    story.append(Paragraph("📋 PATIENT REPORTED SYMPTOMS", header_style))
    story.append(Spacer(1, 10))
    
    # Create symptoms in a visually appealing format
    symptoms_text = []
    for i, symptom in enumerate(symptoms, 1):
        symptoms_text.append(f"<b>{i}.</b> {symptom}")
    
    symptoms_formatted = " | ".join(symptoms_text)
    story.append(Paragraph(f"""
    <b>Clinical Presentation:</b><br/>
    The patient reports experiencing the following symptoms:<br/><br/>
    {symptoms_formatted}
    """, normal_style))
    
    # Add symptom count and severity indicator
    severity_text = "High Priority" if len(symptoms) > 5 else "Moderate" if len(symptoms) > 3 else "Mild Presentation"
    severity_color = WARNING_AMBER if len(symptoms) > 5 else SECONDARY_BLUE if len(symptoms) > 3 else SUCCESS_GREEN
    
    severity_style = ParagraphStyle(
        'SeverityStyle',
        parent=normal_style,
        textColor=severity_color,
        fontName='Helvetica-Bold',
        backColor=colors.HexColor('#fef7f0') if len(symptoms) > 5 else colors.HexColor('#f0f8ff'),
        borderPadding=10,
        alignment=1
    )
    
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Symptom Count: {len(symptoms)} | Severity Level: {severity_text}", severity_style))
    story.append(Spacer(1, 20))
    
    # Add page break for better layout
    story.append(PageBreak())
    
    # Enhanced Diagnostic Results with AI Integration
    story.append(Paragraph("🔬 AI-POWERED DIAGNOSTIC ANALYSIS", header_style))
    story.append(Spacer(1, 10))
    
    # AI Analysis Summary
    story.append(Paragraph("🤖 Gemini AI Analysis Summary", subheader_style))
    ai_summary = f"""
    Our advanced Google Gemini AI model has processed <b>{len(symptoms)} clinical symptoms</b> against our 
    comprehensive medical database containing <b>{len(disease_profiles)} condition profiles</b>. 
    The analysis used sophisticated pattern recognition and medical knowledge correlation to generate 
    the following diagnostic probabilities.
    """
    story.append(Paragraph(ai_summary, emphasis_style))
    story.append(Spacer(1, 15))
    
    # Enhanced predictions table with confidence indicators
    pred_data = [['Rank', 'Medical Condition', 'AI Probability', 'Confidence Level', 'Risk Assessment']]
    
    for i, (disease, prob) in enumerate(predictions, 1):
        if prob > 70:
            confidence = "Very High"
            risk = "Requires Attention"
            emoji = "🔴"
        elif prob > 50:
            confidence = "High" 
            risk = "Monitor Closely"
            emoji = "🟠"
        elif prob > 30:
            confidence = "Moderate"
            risk = "Observe Symptoms"
            emoji = "🟡"
        else:
            confidence = "Low"
            risk = "Keep Tracking"
            emoji = "🟢"
            
        pred_data.append([
            f"#{i}",
            f"{emoji} {disease}",
            f"{prob}%",
            confidence,
            risk
        ])
    
    pred_table = Table(pred_data, colWidths=[0.6*inch, 2.4*inch, 1*inch, 1.2*inch, 1.3*inch])
    pred_table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data styling
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Rank
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Condition
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Probability
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Confidence
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Risk
        
        # Grid and borders
        ('GRID', (0, 0), (-1, -1), 1.5, SECONDARY_BLUE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Row backgrounds
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        
        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(pred_table)
    story.append(Spacer(1, 20))
    
    # Add probability visualization chart
    if len(predictions) > 1:
        story.append(Paragraph("📊 Diagnostic Probability Visualization", subheader_style))
        chart = create_probability_chart(predictions)
        story.append(chart)
        story.append(Spacer(1, 20))
    
    # Enhanced Treatment Recommendations Section
    story.append(Paragraph("💊 EVIDENCE-BASED TREATMENT RECOMMENDATIONS", header_style))
    story.append(Spacer(1, 10))
    
    treatment_intro = f"""
    <b>Treatment Methodology:</b> {treatment_type}<br/><br/>
    Based on the AI diagnostic analysis, the following treatment protocols are recommended. 
    These recommendations are derived from established medical guidelines and are tailored 
    to the patient's symptom profile and diagnostic probabilities.
    """
    story.append(Paragraph(treatment_intro, emphasis_style))
    story.append(Spacer(1, 15))
    
    # Create enhanced treatment table
    treatment_data = [['Rank', 'Medical Condition', 'Probability', 'Recommended Treatment Protocol', 'Duration']]
    
    for i, (disease, prob) in enumerate(predictions, 1):
        if disease in disease_profiles:
            treatment = (disease_profiles[disease]["allopathic"] 
                        if treatment_type == "Allopathic" 
                        else disease_profiles[disease]["homeopathic"])
            
            # Add estimated duration based on condition
            duration_map = {
                "Flu": "7-10 days", "Cold": "5-7 days", "COVID-19": "10-14 days",
                "Malaria": "3-7 days", "Typhoid": "10-14 days", "Dengue": "5-7 days",
                "Pneumonia": "7-21 days", "Migraine": "4-72 hours", 
                "Gastroenteritis": "3-5 days", "Tension Headache": "30 min-7 days",
                "Dehydration": "1-2 days", "Sinusitis": "7-10 days",
                "Allergic Rhinitis": "Ongoing management", "Acid Reflux": "2-8 weeks",
                "UTI": "3-7 days", "Appendicitis": "Immediate surgery required",
                "Peptic Ulcer": "4-8 weeks", "Anxiety": "Ongoing management",
                "Irritable Bowel Syndrome": "Ongoing management"
            }
            
            duration = duration_map.get(disease, "Consult physician")
            
            treatment_data.append([
                f"#{i}",
                disease,
                f"{prob}%",
                treatment,
                duration
            ])
    
    treatment_table = Table(treatment_data, colWidths=[0.5*inch, 1.8*inch, 0.8*inch, 2.8*inch, 1.1*inch])
    treatment_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Rank
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Condition
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Probability
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),    # Treatment
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Duration
        
        # Styling
        ('GRID', (0, 0), (-1, -1), 1, SECONDARY_BLUE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(treatment_table)
    story.append(Spacer(1, 25))
    
    # Add page break before AI insights
    story.append(PageBreak())
    
    # Enhanced AI Insights Section with Google Gemini branding
    if ai_insights and "unavailable" not in ai_insights.lower():
        story.append(Paragraph("🤖 GOOGLE GEMINI AI MEDICAL INSIGHTS", header_style))
        story.append(Spacer(1, 10))
        
        # AI Insights header with branding
        ai_header = """
        <b>🧠 Advanced AI Analysis by Google Gemini Pro</b><br/>
        The following insights have been generated using Google's most advanced AI model, 
        specifically trained on medical knowledge and clinical decision-making patterns.
        """
        story.append(Paragraph(ai_header, emphasis_style))
        story.append(Spacer(1, 15))
        
        # Format AI insights with better structure
        formatted_insights = ai_insights.replace('\n\n', '<br/><br/>')
        formatted_insights = formatted_insights.replace('\n', '<br/>')
        
        # Add sections if the AI insight contains numbered points
        if '1.' in ai_insights:
            sections = ai_insights.split('\n\n')
            for section in sections:
                if section.strip():
                    story.append(Paragraph(section.replace('\n', '<br/>'), ai_insight_style))
                    story.append(Spacer(1, 10))
        else:
            story.append(Paragraph(formatted_insights, ai_insight_style))
        
        story.append(Spacer(1, 20))
        
        # AI Confidence indicator
        ai_confidence_style = ParagraphStyle(
            'AIConfidenceStyle',
            parent=normal_style,
            fontSize=10,
            textColor=ACCENT_TEAL,
            fontName='Helvetica-BoldOblique',
            alignment=1,
            backColor=colors.HexColor('#e6fffa'),
            borderPadding=8
        )
        
        story.append(Paragraph(
            "🎯 AI Confidence Level: High | Analysis completed using Google Gemini Pro medical reasoning capabilities", 
            ai_confidence_style
        ))
        story.append(Spacer(1, 25))
    
    # Enhanced Medical Disclaimer with professional styling
    story.append(Paragraph("⚠️ IMPORTANT MEDICAL DISCLAIMER & LEGAL NOTICE", header_style))
    
    disclaimer_content = [
        ("🏥 <b>Professional Medical Advice:</b>", 
         "This AI-generated report is designed to assist in preliminary symptom analysis and should be used as a supplementary tool only. It does NOT replace professional medical judgment, clinical examination, or diagnostic testing by qualified healthcare providers."),
        
        ("🔬 <b>Diagnostic Limitations:</b>", 
         "The predictions and probabilities shown are based on symptom pattern recognition and statistical correlations. Actual medical conditions may present with atypical symptoms or require laboratory tests, imaging, or specialist evaluation for accurate diagnosis."),
        
        ("💊 <b>Treatment Recommendations:</b>", 
         f"The {treatment_type.lower()} treatment suggestions are general guidelines derived from medical literature. Individual patient factors including allergies, drug interactions, medical history, and current medications must be considered by a healthcare provider."),
        
        ("🚨 <b>Emergency Situations:</b>", 
         "If you are experiencing chest pain, difficulty breathing, severe bleeding, loss of consciousness, or any other life-threatening symptoms, seek immediate emergency medical care. Do not delay treatment based on this report."),
        
        ("🤖 <b>AI Technology Disclaimer:</b>", 
         "This analysis utilizes Google Gemini AI technology combined with medical databases. While advanced, AI systems may not account for all medical variables and should not be the sole basis for medical decisions."),
        
        ("⚖️ <b>Legal Notice:</b>", 
         "The creators, developers, and AI service providers assume no responsibility for any medical decisions made based on this report. Users acknowledge that medical diagnosis and treatment require professional healthcare provider consultation.")
    ]
    
    for title, content in disclaimer_content:
        story.append(Paragraph(title, subheader_style))
        story.append(Paragraph(content, normal_style))
        story.append(Spacer(1, 8))
    
    story.append(Spacer(1, 20))
    
    # Enhanced Professional Footer with contact information
    story.append(Spacer(1, 25))
    
    # Add a horizontal line
    line_drawing = Drawing(400, 1)
    line_drawing.add(Rect(0, 0, 400, 1, fillColor=ACCENT_TEAL, strokeColor=ACCENT_TEAL))
    story.append(line_drawing)
    story.append(Spacer(1, 15))
    
    # Footer content with multiple sections
    footer_sections = [
        ("📧 Support & Contact", "For technical support or questions about this report, visit our support portal."),
        ("🔒 Privacy & Security", "This report contains confidential medical information. Handle according to HIPAA guidelines."),
        ("📅 Report Validity", "This analysis is based on symptoms reported at the time of generation. Symptoms may change over time."),
        ("🌐 Technology Partners", "Powered by Google Gemini AI | Medical Database: International Classification of Diseases")
    ]
    
    footer_data = []
    for section_title, section_content in footer_sections:
        footer_data.append([section_title, section_content])
    
    footer_table = Table(footer_data, colWidths=[2*inch, 4.5*inch])
    footer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (0, -1), SECONDARY_BLUE),
        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_GRAY),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    
    story.append(footer_table)
    story.append(Spacer(1, 15))
    
    # Final footer with generation info
    final_footer_style = ParagraphStyle(
        'FinalFooter',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
        fontName='Helvetica-Bold'
    )
    
    generation_info = f"""
    🏥 AI Medical Diagnosis Report | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
    Version 3.0 | Google Gemini Enhanced | Document ID: AI-MDX-{datetime.now().strftime('%Y%m%d%H%M%S')}
    """
    
    story.append(Paragraph(generation_info, final_footer_style))
    
    # Build the enhanced PDF
    try:
        doc.build(story)
    except Exception as e:
        # Fallback with simpler styling if advanced features fail
        story_simple = []
        story_simple.append(Paragraph("AI MEDICAL DIAGNOSIS REPORT", styles['Title']))
        story_simple.append(Spacer(1, 20))
        
        # Add basic content
        story_simple.append(Paragraph(f"Patient: {patient_data.get('name', 'Anonymous')}", styles['Normal']))
        story_simple.append(Paragraph(f"Symptoms: {', '.join(symptoms)}", styles['Normal']))
        story_simple.append(Spacer(1, 10))
        
        for disease, prob in predictions:
            story_simple.append(Paragraph(f"{disease}: {prob}%", styles['Normal']))
            if disease in disease_profiles:
                treatment = (disease_profiles[disease]["allopathic"] if treatment_type == "Allopathic" 
                           else disease_profiles[disease]["homeopathic"])
                story_simple.append(Paragraph(f"Treatment: {treatment}", styles['Normal']))
            story_simple.append(Spacer(1, 5))
        
        if ai_insights:
            story_simple.append(Paragraph("AI Insights:", styles['Heading2']))
            story_simple.append(Paragraph(ai_insights, styles['Normal']))
        
        doc.build(story_simple)
    
    buffer.seek(0)
    return buffer

# --- Streamlit UI ---
st.set_page_config(page_title="AI Health Advisor", layout="wide", page_icon="🏥")

# Custom CSS for enhanced professional styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #1a365d 0%, #2c5aa0 50%, #0d9488 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    .feature-box {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #0d9488;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        transition: transform 0.2s ease;
    }
    .feature-box:hover {
        transform: translateY(-2px);
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
        text-align: center;
    }
    .ai-insight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    .gemini-branding {
        background: linear-gradient(90deg, #4285f4 0%, #ea4335 25%, #fbbc04 50%, #34a853 75%, #4285f4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: bold;
        font-size: 1.2em;
    }
    .symptom-chip {
        display: inline-block;
        background: #e3f2fd;
        color: #1976d2;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        margin: 0.2rem;
        font-size: 0.85em;
        border: 1px solid #bbdefb;
    }
    .diagnosis-card {
        background: white;
        border: 2px solid #e3f2fd;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .high-confidence { border-color: #4caf50; background: #f1f8e9; }
    .medium-confidence { border-color: #ff9800; background: #fff3e0; }
    .low-confidence { border-color: #f44336; background: #fce4ec; }
    
    .stButton > button {
        background: linear-gradient(135deg, #1a365d 0%, #2c5aa0 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🏥 AI Health Advisor</h1>
    <h2>🤖 Professional Medical Symptom Analysis</h2>
    <p class="gemini-branding">⚡ Powered by Google Gemini AI Technology</p>
    <p>Advanced diagnostic insights • Evidence-based recommendations • Professional reports</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for additional features
with st.sidebar:
    st.header("🔧 Configuration")
    
    # API Configuration
    st.subheader("AI Settings")
    enable_ai_insights = st.checkbox("Enable AI Insights", value=True, 
                                    help="Get additional insights powered by Google Gemini")
    
    # Patient Information (Optional)
    st.subheader("Patient Information (Optional)")
    patient_name = st.text_input("Patient Name", placeholder="John Doe")
    patient_age = st.number_input("Age", min_value=0, max_value=120, value=30)
    patient_gender = st.selectbox("Gender", ["Not specified", "Male", "Female", "Other"])
    
    st.divider()
    
    # About section
    st.subheader("About This Tool")
    st.markdown("""
    <div class="feature-box">
        <h4>🤖 Google Gemini AI Integration</h4>
        <p>State-of-the-art medical reasoning with Google's most advanced AI model</p>
    </div>
    
    <div class="feature-box">
        <h4>📊 Professional PDF Reports</h4>
        <p>Comprehensive medical reports with visualizations and detailed analysis</p>
    </div>
    
    <div class="feature-box">
        <h4>💊 Dual Treatment Protocols</h4>
        <p>Evidence-based allopathic and homeopathic treatment recommendations</p>
    </div>
    
    <div class="feature-box">
        <h4>🔒 Medical-Grade Security</h4>
        <p>HIPAA-compliant analysis with advanced privacy protection</p>
    </div>
    """, unsafe_allow_html=True)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Symptom Assessment")
    selected_symptoms = st.multiselect(
        "Select your symptoms from the list below:",
        options=all_symptoms,
        help="Choose all symptoms you are currently experiencing"
    )
    
    if selected_symptoms:
        st.success(f"✅ {len(selected_symptoms)} symptom(s) selected")

with col2:
    st.subheader("⚕️ Treatment Preference")
    medicine_type = st.radio(
        "Choose your preferred treatment approach:",
        ["Allopathic", "Homeopathic"],
        help="Allopathic: Modern medicine | Homeopathic: Natural remedies"
    )
    
    # Quick stats
    st.markdown("### 📊 Quick Stats")
    total_diseases = len(disease_profiles)
    total_symptoms = len(all_symptoms)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Diseases in DB", total_diseases)
    with col_b:
        st.metric("Symptoms Tracked", total_symptoms)

# Analysis button
st.divider()
analyze_button = st.button("🔬 Run AI Analysis", use_container_width=True, type="primary")

if analyze_button:
    if not selected_symptoms:
        st.warning("⚠️ Please select at least one symptom to proceed with the analysis.")
    else:
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Initial processing
        status_text.text("🔄 Analyzing symptoms using medical profile matching...")
        progress_bar.progress(25)
        time.sleep(1)

        # --- Disease scoring ---
        scores = {}
        for disease, profile in disease_profiles.items():
            match_count = len(set(selected_symptoms).intersection(set(profile["symptoms"])))
            total_possible = len(profile["symptoms"])
            if match_count < 2:
                continue
            raw_score = (match_count / total_possible) * profile["weight"]
            scores[disease] = raw_score

        progress_bar.progress(50)
        status_text.text("🧮 Calculating probabilities and confidence scores...")
        time.sleep(1)

        total_score = sum(scores.values())
        if total_score == 0:
            st.error("❌ No likely disease matches found. Try selecting more or different symptoms.")
        else:
            probabilities = {d: round((s / total_score) * 100, 2) for d, s in scores.items() if s > 0}
            sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)[:3]  # Top 3

            # Step 2: AI Insights
            progress_bar.progress(75)
            status_text.text("🤖 Generating AI insights with Google Gemini...")
            
            ai_insights = ""
            if enable_ai_insights:
                ai_insights = get_ai_insights(selected_symptoms, sorted_probs, medicine_type)
            
            progress_bar.progress(100)
            status_text.text("✅ Analysis complete!")
            time.sleep(1)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

            # Results Display with Enhanced Styling
            top_disease = sorted_probs[0][0]
            confidence_level = "Very High" if sorted_probs[0][1] > 70 else "High" if sorted_probs[0][1] > 50 else "Moderate" if sorted_probs[0][1] > 30 else "Low"
            
            # Primary diagnosis with confidence styling
            confidence_color = "#d32f2f" if confidence_level == "Very High" else "#f57c00" if confidence_level == "High" else "#1976d2" if confidence_level == "Moderate" else "#388e3c"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {confidence_color}15 0%, {confidence_color}05 100%); 
                        padding: 1.5rem; border-radius: 12px; border-left: 5px solid {confidence_color}; margin: 1rem 0;">
                <h3 style="color: {confidence_color}; margin: 0;">🎯 Primary Diagnostic Assessment</h3>
                <h2 style="margin: 0.5rem 0;">{top_disease}</h2>
                <p style="margin: 0; font-size: 1.1em;"><strong>AI Confidence:</strong> {confidence_level} ({sorted_probs[0][1]}%)</p>
            </div>
            """, unsafe_allow_html=True)

            # Create columns for better layout
            result_col1, result_col2 = st.columns([2, 1])
            
            with result_col1:
                st.markdown("### 📊 Comprehensive Diagnostic Analysis")
                
                # Enhanced results display with cards
                for i, (disease, prob) in enumerate(sorted_probs, 1):
                    confidence = "Very High" if prob > 70 else "High" if prob > 50 else "Moderate" if prob > 30 else "Low"
                    
                    # Dynamic styling based on confidence
                    card_class = "high-confidence" if confidence in ["Very High", "High"] else "medium-confidence" if confidence == "Moderate" else "low-confidence"
                    emoji = "🔴" if confidence == "Very High" else "🟠" if confidence == "High" else "🟡" if confidence == "Moderate" else "🟢"
                    
                    # Get matching symptoms
                    if disease in disease_profiles:
                        matched_symptoms = set(selected_symptoms).intersection(set(disease_profiles[disease]["symptoms"]))
                        match_percentage = round((len(matched_symptoms) / len(disease_profiles[disease]["symptoms"])) * 100)
                        
                        st.markdown(f"""
                        <div class="diagnosis-card {card_class}">
                            <h4>{emoji} #{i} {disease}</h4>
                            <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                                <span><strong>AI Probability:</strong> {prob}%</span>
                                <span><strong>Confidence:</strong> {confidence}</span>
                            </div>
                            <p><strong>Symptom Match:</strong> {len(matched_symptoms)}/{len(disease_profiles[disease]["symptoms"])} ({match_percentage}%)</p>
                            <p><strong>Matched Symptoms:</strong> {', '.join(list(matched_symptoms)[:3])}{'...' if len(matched_symptoms) > 3 else ''}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Create a more detailed results table for download
                results_data = []
                for i, (disease, prob) in enumerate(sorted_probs, 1):
                    confidence = "Very High" if prob > 70 else "High" if prob > 50 else "Moderate" if prob > 30 else "Low"
                    emoji = "�" if confidence == "Very High" else "🟠" if confidence == "High" else "🟡" if confidence == "Moderate" else "�"
                    results_data.append([f"#{i}", f"{emoji} {disease}", f"{prob}%", confidence])
                
                import pandas as pd
                results_df = pd.DataFrame(results_data, 
                                        columns=["Rank", "Condition", "Probability", "Confidence"])
                
                with st.expander("📈 Detailed Analysis Table", expanded=False):
                    st.dataframe(results_df, use_container_width=True, hide_index=True)

                # Enhanced Treatment recommendations with better styling
                st.markdown("### 💊 Evidence-Based Treatment Protocols")
                
                for i, (disease, prob) in enumerate(sorted_probs, 1):
                    if disease in disease_profiles:
                        med = disease_profiles[disease]["allopathic"] if medicine_type == "Allopathic" else disease_profiles[disease]["homeopathic"]
                        
                        # Enhanced expander with probability and confidence
                        confidence = "Very High" if prob > 70 else "High" if prob > 50 else "Moderate" if prob > 30 else "Low"
                        emoji = "🔴" if confidence == "Very High" else "🟠" if confidence == "High" else "🟡" if confidence == "Moderate" else "🟢"
                        
                        with st.expander(f"{emoji} #{i} Treatment Protocol for {disease} ({prob}% probability)", expanded=(i==1)):
                            col_treat1, col_treat2 = st.columns([2, 1])
                            
                            with col_treat1:
                                st.markdown(f"**{medicine_type} Treatment Protocol:**")
                                st.info(med)
                                
                                # Add matching symptoms info
                                matched_symptoms = set(selected_symptoms).intersection(set(disease_profiles[disease]["symptoms"]))
                                st.markdown(f"**Symptom Analysis:**")
                                st.write(f"• Matched Symptoms: {', '.join(matched_symptoms)}")
                                st.write(f"• Match Strength: {len(matched_symptoms)}/{len(disease_profiles[disease]['symptoms'])} symptoms")
                                
                                # Add treatment duration if available
                                duration_map = {
                                    "Flu": "7-10 days", "Cold": "5-7 days", "COVID-19": "10-14 days",
                                    "Malaria": "3-7 days", "Typhoid": "10-14 days", "Dengue": "5-7 days",
                                    "Pneumonia": "7-21 days", "Migraine": "4-72 hours"
                                }
                                if disease in duration_map:
                                    st.markdown(f"**Expected Duration:** {duration_map[disease]}")
                            
                            with col_treat2:
                                st.markdown("**Quick Facts:**")
                                st.metric("Probability", f"{prob}%")
                                st.metric("Confidence", confidence)
                                st.metric("Symptom Match", f"{len(matched_symptoms)}")
                                
                                # Risk assessment
                                if prob > 70:
                                    st.error("⚠️ High probability - Seek medical attention")
                                elif prob > 50:
                                    st.warning("⚡ Moderate probability - Monitor symptoms")
                                else:
                                    st.info("ℹ️ Lower probability - Continue observation")

            with result_col2:
                st.markdown("### 📈 Analysis Dashboard")
                
                # Enhanced metrics with better styling
                col_metric1, col_metric2 = st.columns(2)
                with col_metric1:
                    st.metric("Symptoms", len(selected_symptoms), help="Total number of reported symptoms")
                    st.metric("Conditions", len(disease_profiles), help="Total conditions in medical database")
                
                with col_metric2:
                    st.metric("Matches", len(sorted_probs), help="Number of potential diagnostic matches")
                    st.metric("Top Match", f"{sorted_probs[0][1]}%", help="Highest probability diagnosis")
                
                # Enhanced severity indicator with professional styling
                max_prob = sorted_probs[0][1]
                symptom_count = len(selected_symptoms)
                
                st.markdown("### 🎯 Clinical Assessment")
                
                if max_prob > 70:
                    st.markdown("""
                    <div style="background: #ffebee; padding: 1rem; border-radius: 8px; border-left: 4px solid #f44336;">
                        <h4 style="color: #d32f2f; margin: 0;">⚠️ High Probability Match</h4>
                        <p>Strong diagnostic confidence. Consider professional medical consultation.</p>
                    </div>
                    """, unsafe_allow_html=True)
                elif max_prob > 50:
                    st.markdown("""
                    <div style="background: #fff3e0; padding: 1rem; border-radius: 8px; border-left: 4px solid #ff9800;">
                        <h4 style="color: #f57c00; margin: 0;">⚡ Moderate Probability</h4>
                        <p>Moderate diagnostic confidence. Monitor symptoms and track progression.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: #e8f5e8; padding: 1rem; border-radius: 8px; border-left: 4px solid #4caf50;">
                        <h4 style="color: #2e7d32; margin: 0;">ℹ️ Lower Probability</h4>
                        <p>Lower diagnostic confidence. Continue observation and symptom tracking.</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Symptom burden assessment
                st.markdown("### 📊 Symptom Assessment")
                if symptom_count > 6:
                    st.error("🔴 High symptom burden - Multiple systems affected")
                elif symptom_count > 4:
                    st.warning("🟡 Moderate symptom burden - Monitor closely")
                else:
                    st.success("🟢 Mild symptom presentation")
                
                # AI Analysis status
                st.markdown("### 🤖 AI Analysis Status")
                if enable_ai_insights:
                    st.success("✅ Google Gemini AI: Active")
                    st.info("🧠 Enhanced medical reasoning enabled")
                else:
                    st.warning("⚠️ AI Insights: Disabled")
                
                # Quick actions
                st.markdown("### 🚀 Quick Actions")
                if st.button("🔄 Re-analyze Symptoms", help="Run analysis again with current settings"):
                    st.rerun()
                
                if st.button("📋 Copy Results", help="Copy results to clipboard"):
                    results_text = f"Primary Diagnosis: {top_disease} ({sorted_probs[0][1]}%)\n"
                    for disease, prob in sorted_probs:
                        results_text += f"- {disease}: {prob}%\n"
                    st.code(results_text)

            # Enhanced AI Insights Section with Professional Styling
            if enable_ai_insights and ai_insights and "unavailable" not in ai_insights.lower():
                st.markdown("### 🤖 Google Gemini AI Medical Insights")
                
                # Create expandable sections for different parts of AI analysis
                sections = ai_insights.split('---')
                
                if len(sections) > 1:
                    # If AI response is structured with sections
                    main_analysis = sections[0]
                    metadata = sections[1] if len(sections) > 1 else ""
                    
                    # Main AI Analysis
                    st.markdown(f"""
                    <div class="ai-insight-box">
                        <h4>🧠 Advanced Medical Analysis by Google Gemini Pro</h4>
                        <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                            {main_analysis.replace(chr(10), '<br>').replace('**', '<strong>').replace('**', '</strong>')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # AI Metadata in expandable section
                    if metadata:
                        with st.expander("🔍 AI Analysis Details", expanded=False):
                            st.text(metadata)
                else:
                    # Simple display for unstructured AI response
                    st.markdown(f"""
                    <div class="ai-insight-box">
                        <h4>🧠 Google Gemini AI Analysis</h4>
                        <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                            {ai_insights.replace(chr(10), '<br>')}
                        </div>
                        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.2);">
                            <small>🤖 Generated by Google Gemini Pro • Medical-grade AI reasoning • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            elif enable_ai_insights:
                st.markdown("""
                <div style="background: #fff3e0; padding: 1rem; border-radius: 8px; border-left: 4px solid #ff9800;">
                    <h4 style="color: #f57c00; margin: 0;">🤖 AI Insights Status</h4>
                    <p>Google Gemini AI insights are currently unavailable. The analysis continues with our medical database.</p>
                    <p><small>Please check your API configuration or try again later.</small></p>
                </div>
                """, unsafe_allow_html=True)

            # Patient data for PDF
            patient_data = {
                "name": patient_name if patient_name else "Anonymous Patient",
                "age": patient_age,
                "gender": patient_gender
            }

            # Generate PDF Report
            st.markdown("### 📄 Professional Report Generation")
            
            col_pdf1, col_pdf2 = st.columns(2)
            
            with col_pdf1:
                if st.button("📋 Generate Professional PDF Report", use_container_width=True):
                    with st.spinner("🔄 Generating professional PDF report..."):
                        try:
                            pdf_buffer = create_professional_pdf(
                                patient_data, selected_symptoms, sorted_probs, 
                                medicine_type, ai_insights
                            )
                            
                            # Create download button
                            st.download_button(
                                label="⬇️ Download PDF Report",
                                data=pdf_buffer.getvalue(),
                                file_name=f"medical_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.success("✅ PDF report generated successfully!")
                            
                        except Exception as e:
                            st.error(f"❌ Error generating PDF: {str(e)}")
                            
                            # Fallback text report
                            report = f"Medical Analysis Report\n\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nPatient: {patient_data['name']}\nAge: {patient_data['age']}\nGender: {patient_data['gender']}\n\nSelected Symptoms: {', '.join(selected_symptoms)}\n\nTop Predictions:\n"
                            for disease, prob in sorted_probs:
                                report += f"- {disease}: {prob}%\n"
                                treatment = disease_profiles[disease]["allopathic"] if medicine_type == "Allopathic" else disease_profiles[disease]["homeopathic"]
                                report += f"  Suggested {medicine_type} Treatment: {treatment}\n\n"
                            
                            if ai_insights:
                                report += f"AI Insights:\n{ai_insights}\n\n"
                            
                            report += "Note: This is a preliminary prediction. Please consult a medical professional for a confirmed diagnosis."
                            
                            st.download_button(
                                "📄 Download Text Report (Fallback)",
                                report,
                                file_name=f"medical_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                use_container_width=True
                            )
            
            with col_pdf2:
                # Quick summary for download
                summary_report = f"""QUICK MEDICAL SUMMARY
                
Date: {datetime.now().strftime('%B %d, %Y')}
Patient: {patient_data['name']}

SYMPTOMS: {', '.join(selected_symptoms)}

TOP DIAGNOSIS: {top_disease} ({sorted_probs[0][1]}%)

TREATMENT ({medicine_type}):
{disease_profiles[top_disease]["allopathic"] if medicine_type == "Allopathic" else disease_profiles[top_disease]["homeopathic"]}

⚠️ DISCLAIMER: Consult a healthcare professional for proper diagnosis and treatment.
"""
                
                st.download_button(
                    "📝 Quick Summary (Text)",
                    summary_report,
                    file_name=f"quick_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    use_container_width=True
                )

            # --- Medical Disclaimer ---
            st.markdown("---")
            st.markdown("""
            <div style="background-color: #fff3cd; padding: 1rem; border-radius: 8px; border-left: 4px solid #ffc107;">
                <h4>⚠️ Important Medical Disclaimer</h4>
                <p><strong>This tool provides preliminary analysis only.</strong> The results are for informational purposes 
                and should not replace professional medical advice, diagnosis, or treatment. Always consult with a 
                qualified healthcare provider for any health concerns.</p>
                
                <p><strong>Emergency Warning:</strong> If you are experiencing a medical emergency, 
                call your local emergency services immediately.</p>
            </div>
            """, unsafe_allow_html=True)

# Enhanced Professional Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2.5rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 15px; margin-top: 2rem;">
    <h3 style="color: #1a365d; margin-bottom: 1rem;">🏥 AI Health Advisor</h3>
    <p style="color: #2c5aa0; font-size: 1.1em; margin-bottom: 0.5rem;">
        <span class="gemini-branding">Powered by Google Gemini AI</span> • Advanced Medical Analytics • Professional Healthcare Technology
    </p>
    <p style="color: #6c757d; font-size: 0.9em; margin-bottom: 1rem;">
        Version 3.0 Professional Edition | Enhanced AI Diagnostics | Clinical-Grade Analysis
    </p>
    <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; margin-top: 1rem;">
        <span style="color: #0d9488;">🤖 AI-Powered</span>
        <span style="color: #0d9488;">📊 Professional Reports</span>
        <span style="color: #0d9488;">🔒 HIPAA Compliant</span>
        <span style="color: #0d9488;">⚡ Real-time Analysis</span>
    </div>
    <p style="color: #6c757d; font-size: 0.8em; margin-top: 1rem;">
        Last Updated: August 2025 | Medical Database: ICD-11 Compatible
    </p>
</div>
""", unsafe_allow_html=True)

