import streamlit as st
import time
from datetime import datetime

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

# --- Streamlit UI ---
st.set_page_config(page_title="MedCheck", layout="wide")
st.title("MedCheck | AI-Powered Health Advisor")
st.markdown("Enter your symptoms below to get a medically-aligned prediction of possible diseases.")

st.divider()
st.subheader("Select Your Symptoms")
selected_symptoms = st.multiselect("Choose from common symptoms:", options=all_symptoms)

medicine_type = st.radio("Preferred treatment type:", ["Allopathic", "Homeopathic"], horizontal=True)

if st.button("Run Diagnostic", use_container_width=True):
    if not selected_symptoms:
        st.warning("Please select at least one symptom.")
    else:
        with st.spinner("Processing symptoms using medical profile matching..."):
            time.sleep(2)

        # --- Disease scoring ---
        scores = {}
        for disease, profile in disease_profiles.items():
            match_count = len(set(selected_symptoms).intersection(set(profile["symptoms"])))
            total_possible = len(profile["symptoms"])
            if match_count < 2:
                continue
            raw_score = (match_count / total_possible) * profile["weight"]
            scores[disease] = raw_score

        total_score = sum(scores.values())
        if total_score == 0:
            st.error("No likely disease matches found. Try selecting more or different symptoms.")
        else:
            probabilities = {d: round((s / total_score) * 100, 2) for d, s in scores.items() if s > 0}
            sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)[:2]

            top_disease = sorted_probs[0][0]
            st.success(f"Most likely disease: **{top_disease}**")

            st.markdown("### Top Disease Predictions:")
            for disease, prob in sorted_probs:
                st.markdown(f"- **{disease}:** {prob}%")

            # Show recommended medicine
            st.markdown("### Suggested Treatment:")
            for disease, _ in sorted_probs:
                med = disease_profiles[disease]["allopathic"] if medicine_type == "Allopathic" else disease_profiles[disease]["homeopathic"]
                st.write(f"**{disease}:** {med}")

            # --- Downloadable report ---
            report = f"Disease Diagnosis Report\n\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nSelected Symptoms: {', '.join(selected_symptoms)}\n\nTop Predictions:\n"
            for disease, prob in sorted_probs:
                report += f"- {disease}: {prob}%\n"
                treatment = disease_profiles[disease]["allopathic"] if medicine_type == "Allopathic" else disease_profiles[disease]["homeopathic"]
                report += f"  Suggested {medicine_type} Treatment: {treatment}\n"
            report += "\nNote: This is a preliminary prediction. Please consult a medical professional for a confirmed diagnosis."

            st.download_button("Download Diagnosis Report", report, file_name="diagnosis_report.txt")

            # --- Disclaimer note at bottom ---
            st.markdown("\n---")
            st.caption("This is a preliminary prediction. Please consult a medical professional for a confirmed diagnosis.")


