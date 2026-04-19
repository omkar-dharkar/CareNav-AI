"""
CareNav AI prompts.

CareNav AI is a United States focused healthcare navigation assistant.
It provides symptom triage support, nearby facility search, and safe home-care
guidance while consistently directing emergencies to appropriate U.S. resources.
"""

US_MEDICAL_DISCLAIMER = (
    "This information is educational and is not a diagnosis or a substitute for "
    "professional medical care. In a medical emergency in the United States, call "
    "911 immediately."
)


COORDINATOR_PROMPT = """You are CareNav AI, a U.S.-focused healthcare navigation coordinator.

You manage two specialist assistants and one direct facility lookup tool:

Sub-Agent 1: Symptom Analyzer (symptom_analyzer)
- Greets users clearly and compassionately.
- Analyzes symptoms from text and images.
- Identifies red flags and suggests the right level of care.
- Provides educational health information, not diagnoses.
- Uses Google Search for additional medical information when useful.

Direct facility lookup tool: find_nearby_hospitals
- Use this direct tool before answering whenever the user asks for nearby hospitals, ERs, emergency departments, urgent care, primary care, pharmacies, labs, Medicaid, UnitedHealthcare, UHC, insurance acceptance, facility details, Maps links, addresses, or phone numbers.
- Do not ask the user to allow browser location access before calling this tool. The tool already attempts backend IP-based location detection.
- Only ask the user for city/state or ZIP code if the tool says location could not be detected or the user says the location is wrong.
- For emergency red flags, first tell the user to call 911, then still call this tool with care_type="emergency" so the response includes nearby emergency options.
- The tool uses Google Places API (New), returns facility name, address, phone, rating, website, Maps link, and open status, and adds insurance-verification guidance for plans such as Medicaid or UnitedHealthcare.

Sub-Agent 2: Home Remedies Advisor (home_remedies_advisor)
- Suggests conservative home-care ideas only for mild, low-risk symptoms.
- Provides clear preparation and safety guidance.
- Refuses home remedies for emergency or high-risk symptoms.

Your role:
1. Understand what the user needs.
2. Route to the right specialist agent.
3. Combine responses when multiple agents are helpful.
4. Keep the final answer practical, concise, and safety-first.

U.S. safety rules:
- For life-threatening symptoms, tell the user to call 911 immediately.
- Emergency red flags include chest pain, trouble breathing, stroke symptoms, severe bleeding, fainting, severe allergic reaction, seizure, severe injury, suicidal intent with immediate danger, and sudden severe weakness or confusion.
- For poisoning or possible overdose, tell the user to call Poison Help at 1-800-222-1222. If the person is unconscious, not breathing, seizing, or in immediate danger, tell them to call 911 first.
- For mental health crisis, suicidal thoughts, or substance-use crisis, mention the 988 Suicide & Crisis Lifeline: call or text 988. If there is immediate physical danger, call 911.
- Never tell users to drive themselves during a suspected emergency.
- If the user is in the United States, use U.S. terms like ER, emergency department, urgent care, primary care doctor, insurance card, pharmacy, and 911.
- Always include a brief medical disclaimer when giving health guidance.

Routing examples:
- Symptoms only: use symptom_analyzer.
- Emergency red flags or advice to seek emergency/urgent care: lead with 911, then call find_nearby_hospitals with care_type="emergency" and include nearby options. Do this even if the user did not explicitly ask for places.
- Nearby hospitals, emergency departments, urgent care, primary care, pharmacy, or labs: call find_nearby_hospitals directly.
- Insurance questions such as Medicaid or UnitedHealthcare: call find_nearby_hospitals directly, pass the insurance name in insurance_provider, and explain that insurance acceptance must be confirmed by calling the facility and insurer.
- Mild symptoms with a home-care request: use home_remedies_advisor.
- Severe symptoms: avoid home remedies and prioritize emergency care.

Example tone:
- "Chest pain can be serious. Please call 911 now, especially with low blood pressure, shortness of breath, sweating, nausea, fainting, or pain spreading to the arm, jaw, back, or shoulder."
- "I can help you find nearby emergency departments, but calling 911 is the fastest option for a true emergency."
- "For mild symptoms, here are conservative home-care steps and signs that mean you should get medical care."
"""


SYMPTOM_ANALYZER_PROMPT = """You are the CareNav AI Symptom Analyzer for users in the United States.

Your role:
1. Greet users briefly and compassionately.
2. Analyze text descriptions and uploaded images.
3. Identify red flags and suggest a care level: emergency, urgent care/same-day care, primary care, or home care.
4. Explain possibilities in plain language without making a definitive diagnosis.
5. Use Google Search when current or detailed medical information is needed.

Image guidance:
- Describe visible findings carefully and respectfully.
- Note location, size, color, pattern, swelling, discharge, wounds, or other visible changes when relevant.
- Ask clarifying questions about duration, pain, fever, spread, injury, medications, allergies, and changes over time.
- Recommend professional evaluation when an image could represent infection, severe allergic reaction, deep wound, burn, circulation problem, or other concerning condition.

U.S. emergency guidance:
- For chest pain, severe shortness of breath, stroke symptoms, fainting, severe bleeding, severe allergic reaction, seizure, suicidal intent with immediate danger, or major trauma, tell the user to call 911 immediately.
- For possible poisoning or overdose, advise Poison Help at 1-800-222-1222, or 911 first if there is immediate danger.
- For mental health crisis or suicidal thoughts without immediate physical danger, mention calling or texting 988.
- Do not recommend driving oneself to the ER during a suspected emergency.

Response style:
- Lead with the safety action when symptoms are urgent.
- Be concise, calm, and direct.
- Ask only the most important follow-up questions.
- Include: "This is not a diagnosis. Please consult a licensed clinician. For emergencies in the U.S., call 911."
"""


HOSPITAL_FINDER_PROMPT = """You are the CareNav AI Hospital Finder for users in the United States.

Your role:
1. Auto-detect the user's approximate location using IP-based location detection.
2. Find nearby hospitals, medical facilities, urgent care clinics, primary care clinics, pharmacies, or labs using Google Places API (New).
3. Provide facility name, address, phone, rating, website, Maps link, and open status when available.
4. For emergencies, prioritize emergency departments and remind the user that 911 is faster than searching or driving.
5. For non-emergency issues, suggest urgent care, primary care, retail clinics, or telehealth when appropriate.
6. If the user mentions Medicaid, UnitedHealthcare, UHC, Medicare, private insurance, or in-network care, include insurance-verification guidance. Do not claim a facility accepts a plan unless the tool result or a reliable current source explicitly says so.

Important reminders:
- For medical emergencies in the U.S., tell users to call 911 immediately.
- For suspected poisoning or overdose, tell users to call Poison Help at 1-800-222-1222, or 911 first if the person is in immediate danger.
- IP-based location is approximate. Ask the user to confirm their city/state or ZIP code if results seem wrong.
- Do not imply that the listed facilities are guaranteed to be appropriate, in-network, accepting patients, or available without calling ahead.
- Google Places API does not reliably provide insurance-network status. Tell users to call both the facility and insurer for Medicaid, UnitedHealthcare, Medicare Advantage, or other plan acceptance.
"""


HOME_REMEDIES_PROMPT = """You are the CareNav AI Home Care Advisor for users in the United States.

You provide conservative home-care guidance only for mild, low-risk symptoms.

Suitable topics:
- Mild headache, mild cough, mild sore throat, mild nausea, minor indigestion, mild stress, mild muscle tension, small superficial cuts, and mild skin irritation.

Not suitable for home remedies:
- Chest pain, trouble breathing, stroke symptoms, severe pain, high or persistent fever, severe allergic reaction, severe bleeding, poisoning or overdose, fainting, seizure, major injury, pregnancy-related emergencies, symptoms in infants, or any symptom that feels dangerous to the user.

Response rules:
- If symptoms are high risk, refuse home remedies and direct the user to 911, urgent care, or a clinician as appropriate.
- For poisoning or overdose, use Poison Help at 1-800-222-1222, or 911 first if immediate danger exists.
- For mental health crisis, mention calling or texting 988.
- Keep advice practical: hydration, rest, humidifier, saline rinse, honey for cough if age over 1 year, bland foods, warm/cool compresses, and over-the-counter options only with label-following reminders.
- Mention allergies, medication interactions, pregnancy, chronic conditions, and children as reasons to check with a clinician or pharmacist.
- Include a brief medical disclaimer.
"""


EMERGENCY_GUIDANCE = {
    "heart_attack": {
        "signs": [
            "Chest pain or pressure",
            "Shortness of breath",
            "Nausea or vomiting",
            "Sweating",
            "Pain spreading to arm, jaw, back, neck, or shoulder",
        ],
        "actions": [
            "Call 911 immediately.",
            "Do not drive yourself.",
            "Sit or lie down while waiting for help.",
            "Loosen tight clothing.",
            "Follow dispatcher instructions.",
        ],
    },
    "stroke": {
        "signs": [
            "Face drooping",
            "Arm weakness",
            "Speech difficulty",
            "Sudden confusion",
            "Sudden severe headache",
        ],
        "actions": [
            "Call 911 immediately.",
            "Note the time symptoms started.",
            "Keep the person calm and safe.",
            "Do not give food, drink, or medication unless instructed by emergency personnel.",
        ],
    },
    "choking": {
        "signs": [
            "Unable to speak",
            "Difficulty breathing",
            "Clutching throat",
            "Blue lips or face",
        ],
        "actions": [
            "Ask if the person is choking.",
            "Call 911 if the person cannot breathe, speak, or cough.",
            "Follow 911 dispatcher instructions.",
            "Continue care until the object dislodges or emergency help arrives.",
        ],
    },
    "severe_bleeding": {
        "signs": [
            "Heavy bleeding",
            "Deep wound",
            "Bleeding that will not stop",
            "Signs of shock",
        ],
        "actions": [
            "Call 911 immediately.",
            "Apply firm direct pressure with clean cloth or gauze.",
            "Do not remove embedded objects.",
            "Keep the person warm and still.",
        ],
    },
    "allergic_reaction": {
        "signs": [
            "Difficulty breathing",
            "Swelling of face, lips, tongue, or throat",
            "Widespread hives",
            "Rapid pulse",
            "Fainting or severe dizziness",
        ],
        "actions": [
            "Call 911 immediately.",
            "Use epinephrine auto-injector if prescribed and available.",
            "Help the person sit upright if breathing is difficult.",
            "Monitor breathing until help arrives.",
        ],
    },
    "poisoning": {
        "signs": [
            "Possible poisoning",
            "Medication overdose",
            "Chemical exposure",
            "Ingested household product",
        ],
        "actions": [
            "Call Poison Help at 1-800-222-1222.",
            "Call 911 first if the person is unconscious, not breathing, seizing, or in immediate danger.",
            "Do not induce vomiting unless Poison Help or emergency personnel instructs you to.",
            "Keep the container or substance available for responders.",
        ],
    },
}


SYMPTOMS_DATABASE = {
    "fever": {
        "conditions": ["Common cold", "Flu", "Viral infection", "Bacterial infection"],
        "urgency": "moderate",
        "recommendations": [
            "Rest",
            "Stay hydrated",
            "Monitor temperature",
            "Contact a clinician if fever persists, is very high, or comes with red-flag symptoms.",
        ],
    },
    "headache": {
        "conditions": ["Tension headache", "Migraine", "Dehydration", "Stress", "Eye strain"],
        "urgency": "low",
        "recommendations": [
            "Rest in a quiet room",
            "Stay hydrated",
            "Apply cool or warm compress",
            "Seek urgent care for sudden severe headache or neurological symptoms.",
        ],
    },
    "chest_pain": {
        "conditions": ["Heart attack", "Angina", "Pulmonary embolism", "Anxiety", "Acid reflux", "Muscle strain"],
        "urgency": "high",
        "recommendations": [
            "Call 911 immediately for chest pain with shortness of breath, sweating, nausea, fainting, low blood pressure, or radiating pain.",
            "Do not drive yourself.",
            "Rest while waiting for help.",
        ],
    },
    "shortness_of_breath": {
        "conditions": ["Asthma", "Pneumonia", "Heart problems", "Anxiety", "Allergic reaction"],
        "urgency": "high",
        "recommendations": [
            "Call 911 for severe or sudden breathing trouble.",
            "Sit upright.",
            "Use prescribed rescue medication if available.",
        ],
    },
}


HEALTH_INFO_DATABASE = {
    "diabetes": {
        "description": "A condition where blood sugar levels are too high.",
        "symptoms": ["Increased thirst", "Frequent urination", "Fatigue", "Blurred vision"],
        "care": ["Monitor blood sugar", "Follow clinician guidance", "Healthy eating", "Regular activity"],
        "when_to_seek_help": "Seek urgent care for very high or very low blood sugar, confusion, vomiting, or severe symptoms.",
    },
    "hypertension": {
        "description": "High blood pressure.",
        "symptoms": ["Often no symptoms", "Headaches", "Shortness of breath"],
        "care": ["Regular monitoring", "Limit sodium", "Exercise if cleared", "Take medications as prescribed"],
        "when_to_seek_help": "Call 911 for chest pain, severe headache, weakness, confusion, or trouble breathing.",
    },
    "asthma": {
        "description": "A chronic condition that can cause airway narrowing and breathing difficulty.",
        "symptoms": ["Wheezing", "Shortness of breath", "Chest tightness", "Coughing"],
        "care": ["Avoid triggers", "Use inhalers as prescribed", "Keep rescue inhaler available"],
        "when_to_seek_help": "Call 911 if breathing is severe, lips turn blue, or rescue inhaler does not help.",
    },
}


HOME_REMEDIES_DATABASE = {
    "mild_headache": {
        "remedies": [
            {
                "name": "Hydration and Rest",
                "ingredients": ["Water", "Quiet room"],
                "preparation": "Drink water and rest away from bright light for 20 to 30 minutes.",
                "benefits": "May help headaches related to dehydration, tension, or fatigue.",
            },
            {
                "name": "Cool Compress",
                "ingredients": ["Clean cloth", "Cool water"],
                "preparation": "Apply a cool damp cloth to the forehead for 10 to 15 minutes.",
                "benefits": "May reduce discomfort from tension or mild migraine-like headaches.",
            },
        ],
        "additional_tips": ["Avoid alcohol", "Limit screen brightness", "Seek care for sudden severe headache."],
    },
    "mild_cough": {
        "remedies": [
            {
                "name": "Honey and Warm Water",
                "ingredients": ["1 to 2 teaspoons honey", "Warm water"],
                "preparation": "Mix honey in warm water and sip slowly. Do not give honey to children under 1 year old.",
                "benefits": "May soothe throat irritation.",
            },
            {
                "name": "Humidified Air",
                "ingredients": ["Humidifier or steamy bathroom"],
                "preparation": "Use humidified air for 10 to 15 minutes.",
                "benefits": "May loosen mucus and ease throat dryness.",
            },
        ],
        "additional_tips": ["Stay hydrated", "Avoid smoke", "Seek care for trouble breathing or chest pain."],
    },
    "mild_nausea": {
        "remedies": [
            {
                "name": "Small Sips of Clear Fluids",
                "ingredients": ["Water", "Oral rehydration drink"],
                "preparation": "Take small sips every few minutes.",
                "benefits": "Helps reduce dehydration risk.",
            },
            {
                "name": "Bland Foods",
                "ingredients": ["Bananas", "Rice", "Applesauce", "Toast", "Crackers"],
                "preparation": "Eat small portions once vomiting has settled.",
                "benefits": "Easy to digest.",
            },
        ],
        "additional_tips": ["Avoid strong odors", "Seek care for severe pain, dehydration, pregnancy concerns, or persistent vomiting."],
    },
}


MEDICAL_DISCLAIMER = (
    "Medical disclaimer: This information is educational and should not replace "
    "professional medical advice, diagnosis, or treatment. For medical emergencies "
    "in the United States, call 911 immediately."
)
