import base64
import json
import re
import mimetypes
import requests
import os
import streamlit as st
from PIL import Image
import tempfile

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Mistral Feedback Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- Custom Styling -----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Apply Outfit font globally */
html, body, [class*="css"], .stMarkdown {
    font-family: 'Outfit', sans-serif;
}

/* Gradient Title */
.main-title {
    font-size: 2.85rem;
    font-weight: 700;
    background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
    padding-top: 0.5rem;
}

.subtitle {
    font-size: 1.15rem;
    color: #9ca3af;
    margin-bottom: 2rem;
}

/* Glassmorphic cards */
.feedback-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
}

.feedback-header {
    font-size: 1.3rem;
    font-weight: 600;
    color: #e5e7eb;
    margin-bottom: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 0.5rem;
}

/* Visual Badges */
.badge {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    font-size: 0.8rem;
    font-weight: 600;
    border-radius: 6px;
    margin-bottom: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.badge-positive {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #34d399;
}

.badge-negative {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.35);
    color: #f87171;
}

.badge-expectations {
    background: rgba(59, 130, 246, 0.15);
    border: 1px solid rgba(59, 130, 246, 0.35);
    color: #60a5fa;
}

.badge-neutral {
    background: rgba(156, 163, 175, 0.15);
    border: 1px solid rgba(156, 163, 175, 0.35);
    color: #d1d5db;
}

/* Aspect Section styling */
.aspect-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

.aspect-item {
    background: rgba(255, 255, 255, 0.01);
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: 8px;
    padding: 1rem;
    transition: all 0.3s ease;
}

.aspect-item:hover {
    background: rgba(255, 255, 255, 0.02);
    border-color: rgba(99, 102, 241, 0.2);
}

.aspect-title {
    font-weight: 600;
    font-size: 0.95rem;
    color: #f3f4f6;
    margin-bottom: 0.5rem;
    text-transform: capitalize;
}

/* Bullet list style */
ul.clean-list {
    list-style-type: none;
    padding-left: 0;
}

ul.clean-list li {
    padding-left: 1.2rem;
    position: relative;
    margin-bottom: 0.5rem;
    font-size: 0.92rem;
    color: #d1d5db;
    line-height: 1.4;
}

ul.clean-list li::before {
    content: "•";
    position: absolute;
    left: 0.2rem;
    font-weight: bold;
}

ul.positive-list li::before {
    color: #10b981;
}

ul.negative-list li::before {
    color: #ef4444;
}

ul.expectations-list li::before {
    color: #3b82f6;
}

/* Metric Display */
.metric-container {
    background: rgba(99, 102, 241, 0.05);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    margin-bottom: 1.5rem;
}

.metric-val {
    font-size: 1.8rem;
    font-weight: 700;
    color: #818cf8;
}

.metric-lbl {
    font-size: 0.8rem;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.2rem;
}

/* File info overlay */
.file-info {
    font-size: 0.85rem;
    color: #6b7280;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ----------------- Pipeline Implementations -----------------

def ocr_with_mistral(image_path, api_key):
    url = "https://api.mistral.ai/v1/ocr"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/jpeg"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    data_uri = f"data:{mime_type};base64,{b64}"

    payload = {
        "model": "mistral-ocr-latest",
        "document": {
            "type": "image_url",
            "image_url": data_uri
        },
        "include_image_base64": False
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Erreur OCR Mistral ({response.status_code}): {response.text}")

    data = response.json()
    pages_text = [page.get("markdown", "") for page in data.get("pages", [])]
    return "\n\n".join(pages_text).strip()

def analyze_feedback_with_mistral(text, api_key):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = f"""Tu es un système strict d'extraction d'information, spécialisé dans l'analyse de feedbacks.

TÂCHE :
À partir du texte ci-dessous (issu d'un OCR, peut contenir quelques imperfections), identifie un ou plusieurs feedbacks distincts.
Pour CHAQUE feedback, extrais :
- "points_positifs" : les éléments positifs exprimés
- "points_negatifs" : les éléments négatifs ou critiques exprimés
- "attentes" : les attentes, souhaits ou besoins exprimés par l'auteur (ce qu'il espère, souhaite apprendre, voir ou obtenir)

RÈGLES STRICTES :
- N'extrais que des phrases ou clauses complètes et cohérentes
- N'extrais jamais des mots isolés ou des fragments incompréhensibles
- Ignore le texte illisible ou les artefacts d'OCR
- Ne déduis rien qui ne soit pas explicitement présent dans le texte
- Si une catégorie n'est pas présente, laisse le tableau vide
- S'il n'y a qu'un seul feedback dans le texte, renvoie une liste avec un seul élément

FORMAT DE SORTIE : réponds UNIQUEMENT avec du JSON valide (pas de markdown, pas de balises ```)

{{
  "feedbacks": [
    {{
      "resume": "résumé en une phrase",
      "points_positifs": [],
      "points_negatifs": [],
      "attentes": []
    }}
  ]
}}

TEXTE :
{text}
"""

    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Erreur chat Mistral ({response.status_code}): {response.text}")

    return response.json()["choices"][0]["message"]["content"]

def analyze_image_with_vlm(image_b64, api_key):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = """You are an AI system that reads handwritten documents.

TASK:
1. Understand the image content directly (no OCR step).
2. Extract sentiment.

Return ONLY valid JSON (no markdown formatting, no code block backticks):
{
  "positive": [],
  "negative": [],
  "aspects": {
    "supervisor": {"positive": [], "negative": []},
    "environment": {"positive": [], "negative": []},
    "tasks": {"positive": [], "negative": []},
    "communication": {"positive": [], "negative": []},
    "workload": {"positive": [], "negative": []}
  }
}

Rules:
- Only full meaningful sentences or clauses
- No single words
- No explanations
"""

    payload = {
        "model": "pixtral-12b",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/png;base64,{image_b64}"
                    }
                ]
            }
        ],
        "temperature": 0
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Erreur Pixtral VLM ({response.status_code}): {response.text}")
    return response.json()["choices"][0]["message"]["content"]

def extract_text_vlm(image_b64, api_key):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = """You are an OCR system.

TASK:
Extract ONLY the exact text written in the image.

RULES:
- Do NOT analyze sentiment
- Do NOT summarize
- Do NOT interpret
- Keep original wording

Return ONLY JSON:
{
  "text": "..."
}
"""

    payload = {
        "model": "pixtral-12b",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/png;base64,{image_b64}"
                    }
                ]
            }
        ],
        "temperature": 0
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Erreur Pixtral OCR ({response.status_code}): {response.text}")
    return response.json()["choices"][0]["message"]["content"]

def analyze_text_vlm(text, api_key):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = f"""You are a sentiment analysis system.

INPUT TEXT:
{text}

TASK:
Extract:
- positive statements
- negative statements

RULES:
- Only full sentences or clauses
- No single words
- Return ONLY JSON (no markdown formatting, no code block backticks)

FORMAT:
{{
  "positive": [],
  "negative": []
}}
"""

    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Erreur Mistral Small ({response.status_code}): {response.text}")
    return response.json()["choices"][0]["message"]["content"]

def clean_and_parse_json(text_content):
    cleaned = text_content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    
    try:
        return json.loads(cleaned)
    except Exception as e:
        match = re.match(r'\{\s*"text":\s*"(?P<text_content>.*?)"\s*\}', cleaned, re.DOTALL)
        if match:
            inner_text = match.group('text_content')
            escaped_text = inner_text.replace('\n', '\\n')
            repaired = cleaned.replace(inner_text, escaped_text)
            try:
                return json.loads(repaired)
            except Exception:
                pass
        raise e

# ----------------- Session State initialization -----------------
if "results" not in st.session_state:
    st.session_state.results = None
if "ocr_text" not in st.session_state:
    st.session_state.ocr_text = None
if "pipeline_ran" not in st.session_state:
    st.session_state.pipeline_ran = None

# ----------------- Sidebar Controls -----------------
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    # API Key Input
    api_key_env = os.environ.get("MISTRAL_API_KEY", "")
    api_key = st.text_input(
        "Clé API Mistral :",
        value=api_key_env,
        type="password",
        placeholder="Entrez votre clé API...",
        help="Si non saisie, le système cherchera la variable d'environnement MISTRAL_API_KEY."
    )
    
    st.markdown("---")
    st.markdown("## 🧠 Pipeline d'analyse")
    
    pipeline_option = st.radio(
        "Choisissez un modèle/pipeline :",
        [
            "Pipeline 1: Mistral OCR + Mistral Large",
            "Pipeline 2: Direct Pixtral VLM (Aspects)",
            "Pipeline 3: Pixtral OCR + Mistral Small"
        ],
        index=0,
        help="""
        **Pipeline 1**: Utilise l'API OCR de Mistral puis extrait les avis structurés avec Mistral Large.
        **Pipeline 2**: Analyse directement l'image avec le modèle multimodal Pixtral-12b et segmente par thématiques.
        **Pipeline 3**: Extrait le texte brut via Pixtral-12b puis classifie les sentiments via Mistral Small.
        """
    )
    
    st.markdown("---")
    st.markdown("### 📝 Infos Techniques")
    st.info("""
    Ces pipelines correspondent aux architectures définies dans les notebooks de recherche :
    - `feedback_ocr_mistral.ipynb` (Pipeline 1)
    - `VLM.ipynb` (Pipelines 2 & 3)
    """)

# ----------------- Main View Layout -----------------
st.markdown('<div class="main-title">🎯 Mistral Feedback Insights</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Analyse intelligente et structurée de formulaires de feedback manuscrits ou imprimés.</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
    st.markdown("### 📤 Upload de l'Image")
    uploaded_file = st.file_uploader(
        "Glissez-déposez la photo du feedback ici...",
        type=["jpg", "jpeg", "png", "webp"],
        help="Prend en charge les formats standards d'images de bonne qualité."
    )
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Aperçu du feedback uploadé", use_container_width=True)
        
        # Analyze button triggers execution
        if st.button("🚀 Lancer l'analyse", use_container_width=True, type="primary"):
            if not api_key:
                st.error("⚠️ Veuillez renseigner votre clé API Mistral dans la barre latérale pour lancer l'analyse.")
            else:
                with col_right:
                    progress_text = "Lancement du pipeline..."
                    my_bar = st.progress(0, text=progress_text)
                    
                    try:
                        # Write uploaded image to a temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                            tmp.write(uploaded_file.getvalue())
                            temp_path = tmp.name
                        
                        # Prepare Base64 if needed for VLMs
                        with open(temp_path, "rb") as f:
                            image_b64 = base64.b64encode(f.read()).decode("utf-8")
                        
                        if pipeline_option.startswith("Pipeline 1"):
                            # Step 1: OCR
                            my_bar.progress(25, text="Étape 1/2 : Extraction du texte avec l'OCR de Mistral...")
                            ocr_text = ocr_with_mistral(temp_path, api_key)
                            
                            # Step 2: LLM analysis
                            my_bar.progress(60, text="Étape 2/2 : Analyse sémantique avec Mistral Large...")
                            raw_result = analyze_feedback_with_mistral(ocr_text, api_key)
                            
                            parsed_result = clean_and_parse_json(raw_result)
                            
                            # Update session state
                            st.session_state.results = parsed_result
                            st.session_state.ocr_text = ocr_text
                            st.session_state.pipeline_ran = "pipeline1"
                            
                        elif pipeline_option.startswith("Pipeline 2"):
                            # Direct Image analysis
                            my_bar.progress(40, text="Étape unique : Analyse d'image multimodale directe via Pixtral-12b...")
                            raw_result = analyze_image_with_vlm(image_b64, api_key)
                            
                            parsed_result = clean_and_parse_json(raw_result)
                            
                            st.session_state.results = parsed_result
                            st.session_state.ocr_text = None
                            st.session_state.pipeline_ran = "pipeline2"
                            
                        elif pipeline_option.startswith("Pipeline 3"):
                            # Step 1: VLM OCR
                            my_bar.progress(25, text="Étape 1/2 : Extraction du texte brut via Pixtral-12b...")
                            raw_ocr_json = extract_text_vlm(image_b64, api_key)
                            parsed_ocr = clean_and_parse_json(raw_ocr_json)
                            ocr_text = parsed_ocr.get("text", "")
                            
                            # Step 2: Mistral Small Sentiment
                            my_bar.progress(60, text="Étape 2/2 : Classification des opinions via Mistral Small...")
                            raw_sentiment = analyze_text_vlm(ocr_text, api_key)
                            parsed_result = clean_and_parse_json(raw_sentiment)
                            
                            st.session_state.results = parsed_result
                            st.session_state.ocr_text = ocr_text
                            st.session_state.pipeline_ran = "pipeline3"
                            
                        my_bar.progress(100, text="Analyse terminée avec succès !")
                        
                        # Cleanup temp file
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                            
                    except Exception as err:
                        st.error(f"❌ Une erreur s'est produite lors de l'exécution : {err}")
                        # Cleanup temp file if error
                        if 'temp_path' in locals() and os.path.exists(temp_path):
                            os.remove(temp_path)

# ----------------- Right Column: Results Rendering -----------------
with col_right:
    st.markdown("### 📊 Résultats de l'analyse")
    
    if st.session_state.results is None:
        st.info("Sélectionnez une image à gauche et cliquez sur **Lancer l'analyse** pour voir s'afficher les insights ici.")
    else:
        results = st.session_state.results
        pipeline_ran = st.session_state.pipeline_ran
        
        # Display tabs for organized visualization
        tab_insights, tab_text, tab_json = st.tabs(["✨ Analyse Visuelle", "📝 Texte Extrait (OCR)", "⚙️ JSON Brut"])
        
        with tab_insights:
            # Render based on pipeline output structures
            if pipeline_ran == "pipeline1":
                feedbacks = results.get("feedbacks", [])
                
                if not feedbacks:
                    st.warning("Aucun feedback distinct n'a été détecté dans l'image.")
                
                for idx, fb in enumerate(feedbacks, 1):
                    resume = fb.get("resume", f"Feedback #{idx}")
                    positives = fb.get("points_positifs", [])
                    negatives = fb.get("points_negatifs", [])
                    expectations = fb.get("attentes", [])
                    
                    st.markdown(f"""
                    <div class="feedback-card">
                        <div class="feedback-header">🗣️ {resume}</div>
                    """, unsafe_allow_html=True)
                    
                    # Positive Points
                    st.markdown('<div class="badge badge-positive">✅ Points Positifs</div>', unsafe_allow_html=True)
                    if positives:
                        st.markdown('<ul class="clean-list positive-list">' + 
                                    "".join(f"<li>{p}</li>" for p in positives) + 
                                    '</ul>', unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='color: #6b7280; font-size: 0.9rem;'>Aucun point positif mentionné.</p>", unsafe_allow_html=True)
                    
                    # Negative Points
                    st.markdown('<div class="badge badge-negative">❌ Points Négatifs</div>', unsafe_allow_html=True)
                    if negatives:
                        st.markdown('<ul class="clean-list negative-list">' + 
                                    "".join(f"<li>{n}</li>" for n in negatives) + 
                                    '</ul>', unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='color: #6b7280; font-size: 0.9rem;'>Aucun point négatif mentionné.</p>", unsafe_allow_html=True)
                        
                    # Expectations
                    st.markdown('<div class="badge badge-expectations">🎯 Attentes & Besoins</div>', unsafe_allow_html=True)
                    if expectations:
                        st.markdown('<ul class="clean-list expectations-list">' + 
                                    "".join(f"<li>{e}</li>" for e in expectations) + 
                                    '</ul>', unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='color: #6b7280; font-size: 0.9rem;'>Aucune attente spécifique exprimée.</p>", unsafe_allow_html=True)
                        
                    st.markdown("</div>", unsafe_allow_html=True)
                    
            elif pipeline_ran == "pipeline2":
                positives = results.get("positive", [])
                negatives = results.get("negative", [])
                aspects = results.get("aspects", {})
                
                # Sentiment Score calculation
                total_statements = len(positives) + len(negatives)
                sentiment_percentage = 50
                if total_statements > 0:
                    sentiment_percentage = int((len(positives) / total_statements) * 100)
                
                # Render overall metrics
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-val">{sentiment_percentage}%</div>
                    <div class="metric-lbl">Score global de satisfaction</div>
                    <div class="sentiment-meter">
                        <div class="sentiment-fill" style="width: {sentiment_percentage}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="feedback-card">', unsafe_allow_html=True)
                st.markdown('<div class="feedback-header">📋 Synthèse Générale</div>', unsafe_allow_html=True)
                
                # Positive Statements
                st.markdown('<div class="badge badge-positive">✅ Éléments Positifs</div>', unsafe_allow_html=True)
                if positives:
                    st.markdown('<ul class="clean-list positive-list">' + 
                                "".join(f"<li>{p}</li>" for p in positives) + 
                                '</ul>', unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color: #6b7280; font-size: 0.9rem;'>Aucun point positif détecté.</p>", unsafe_allow_html=True)
                
                # Negative Statements
                st.markdown('<div class="badge badge-negative">❌ Éléments Négatifs</div>', unsafe_allow_html=True)
                if negatives:
                    st.markdown('<ul class="clean-list negative-list">' + 
                                "".join(f"<li>{n}</li>" for n in negatives) + 
                                '</ul>', unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color: #6b7280; font-size: 0.9rem;'>Aucun point critique ou négatif détecté.</p>", unsafe_allow_html=True)
                    
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Aspects Grid layout
                st.markdown("#### 🔍 Analyse par thématiques")
                st.markdown('<div class="aspect-grid">', unsafe_allow_html=True)
                
                for aspect_name, aspect_data in aspects.items():
                    a_positives = aspect_data.get("positive", [])
                    a_negatives = aspect_data.get("negative", [])
                    
                    st.markdown(f"""
                    <div class="aspect-item">
                        <div class="aspect-title">🏷️ {aspect_name}</div>
                    """, unsafe_allow_html=True)
                    
                    if not a_positives and not a_negatives:
                        st.markdown("<div class='badge badge-neutral'>N/A</div>", unsafe_allow_html=True)
                        st.markdown("<p style='color: #6b7280; font-size: 0.8rem; margin: 0;'>Pas d'évaluation.</p>", unsafe_allow_html=True)
                    else:
                        if a_positives:
                            st.markdown("<div class='badge badge-positive' style='font-size:0.7rem; margin-bottom:0.25rem;'>+</div>", unsafe_allow_html=True)
                            st.markdown('<ul class="clean-list positive-list" style="margin-bottom:0.5rem; font-size:0.8rem;">' + 
                                        "".join(f"<li style='font-size:0.8rem;'>{p}</li>" for p in a_positives) + 
                                        '</ul>', unsafe_allow_html=True)
                        if a_negatives:
                            st.markdown("<div class='badge badge-negative' style='font-size:0.7rem; margin-bottom:0.25rem;'>-</div>", unsafe_allow_html=True)
                            st.markdown('<ul class="clean-list negative-list" style="margin-bottom:0.5rem; font-size:0.8rem;">' + 
                                        "".join(f"<li style='font-size:0.8rem;'>{n}</li>" for n in a_negatives) + 
                                        '</ul>', unsafe_allow_html=True)
                            
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
            elif pipeline_ran == "pipeline3":
                positives = results.get("positive", [])
                negatives = results.get("negative", [])
                
                st.markdown('<div class="feedback-card">', unsafe_allow_html=True)
                st.markdown('<div class="feedback-header">📋 Synthèse des sentiments (Mistral Small)</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="badge badge-positive">✅ Éléments Positifs</div>', unsafe_allow_html=True)
                if positives:
                    st.markdown('<ul class="clean-list positive-list">' + 
                                "".join(f"<li>{p}</li>" for p in positives) + 
                                '</ul>', unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color: #6b7280; font-size: 0.9rem;'>Aucun point positif mentionné.</p>", unsafe_allow_html=True)
                
                st.markdown('<div class="badge badge-negative">❌ Éléments Négatifs</div>', unsafe_allow_html=True)
                if negatives:
                    st.markdown('<ul class="clean-list negative-list">' + 
                                "".join(f"<li>{n}</li>" for n in negatives) + 
                                '</ul>', unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color: #6b7280; font-size: 0.9rem;'>Aucun point négatif mentionné.</p>", unsafe_allow_html=True)
                    
                st.markdown('</div>', unsafe_allow_html=True)
                
        with tab_text:
            if st.session_state.ocr_text:
                st.text_area("Texte brut extrait :", st.session_state.ocr_text, height=350, disabled=True)
            else:
                st.info("Ce pipeline n'utilise pas d'extraction de texte intermédiaire stockée, ou le texte n'a pas été enregistré.")
                
        with tab_json:
            st.json(results)
            
            # Download JSON Report
            json_string = json.dumps(results, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 Télécharger le rapport JSON",
                data=json_string,
                file_name="rapport_feedback.json",
                mime="application/json"
            )
