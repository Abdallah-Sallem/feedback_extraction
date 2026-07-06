import sys
import os
import json
import shutil
import tempfile

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# Ensure module imports work from the app directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_api_key, WATCHED_FOLDER
from database import (
    init_db, add_document, update_document_text, update_document_status,
    save_analysis_result, get_all_documents, get_analyzed_documents,
    search_documents, delete_document
)
from ocr_engine import extract_text_from_file
from analysis_engine import analyze_raw_text
from aggregation import compute_aggregation
from report_generator import generate_executive_report
from watcher import FolderWatcher

# ─────────────────────────── Page Config ───────────────────────────
st.set_page_config(
    page_title="HR Feedback Intelligence",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────── Custom CSS ───────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], .stMarkdown, .stTextArea textarea {
    font-family: 'Inter', sans-serif;
}

/* ── Gradient Header ── */
.platform-title {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.15rem;
    letter-spacing: -0.02em;
}
.platform-subtitle {
    font-size: 1.05rem;
    color: #9ca3af;
    margin-bottom: 1.8rem;
}

/* ── Glass Cards ── */
.glass-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.4rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(16px);
    box-shadow: 0 4px 30px rgba(0,0,0,0.15);
}
.glass-card-header {
    font-size: 1.15rem;
    font-weight: 700;
    color: #f3f4f6;
    margin-bottom: 0.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

/* ── Sentiment Badges ── */
.sentiment-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    font-size: 0.78rem;
    font-weight: 700;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.sentiment-positive {
    background: rgba(16,185,129,0.15);
    border: 1px solid rgba(16,185,129,0.4);
    color: #34d399;
}
.sentiment-neutral {
    background: rgba(234,179,8,0.15);
    border: 1px solid rgba(234,179,8,0.4);
    color: #fbbf24;
}
.sentiment-negative {
    background: rgba(239,68,68,0.15);
    border: 1px solid rgba(239,68,68,0.4);
    color: #f87171;
}

/* ── Item Badges ── */
.tag-badge {
    display: inline-block;
    padding: 0.2rem 0.55rem;
    font-size: 0.72rem;
    font-weight: 600;
    border-radius: 6px;
    margin: 0.15rem 0.2rem;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.25);
    color: #a5b4fc;
}

/* ── Metric Boxes ── */
.metric-box {
    text-align: center;
    padding: 1rem 0.5rem;
    background: rgba(99,102,241,0.04);
    border: 1px solid rgba(99,102,241,0.12);
    border-radius: 12px;
}
.metric-value {
    font-size: 2rem;
    font-weight: 800;
    color: #818cf8;
}
.metric-label {
    font-size: 0.75rem;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 0.15rem;
}

/* ── Clean Lists ── */
ul.insight-list {
    list-style: none;
    padding-left: 0;
}
ul.insight-list li {
    padding: 0.4rem 0 0.4rem 1.2rem;
    position: relative;
    font-size: 0.9rem;
    color: #d1d5db;
    line-height: 1.5;
}
ul.insight-list li::before {
    content: "›";
    position: absolute;
    left: 0.2rem;
    font-weight: 700;
    color: #818cf8;
}
ul.strength-list li::before { color: #34d399; }
ul.issue-list li::before { color: #f87171; }
ul.action-list li::before { color: #60a5fa; content: "→"; }
ul.quote-list li::before { color: #a78bfa; content: '"'; font-size: 1.1rem; }
ul.quote-list li { font-style: italic; }

/* ── Status pill ── */
.status-pill {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    font-size: 0.7rem;
    font-weight: 600;
    border-radius: 12px;
    text-transform: uppercase;
}
.status-pending { background: rgba(234,179,8,0.15); color: #fbbf24; border: 1px solid rgba(234,179,8,0.3); }
.status-processing { background: rgba(59,130,246,0.15); color: #60a5fa; border: 1px solid rgba(59,130,246,0.3); }
.status-analyzed { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }
.status-failed { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }

/* ── Hide Streamlit branding ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────── Session State ───────────────────────────
if "watcher_instance" not in st.session_state:
    st.session_state.watcher_instance = None
if "exec_report" not in st.session_state:
    st.session_state.exec_report = None

# ─────────────────────────── Helpers ───────────────────────────
def get_sentiment_badge(sentiment):
    s = sentiment.lower() if sentiment else "neutral"
    css = f"sentiment-{s}" if s in ("positive", "neutral", "negative") else "sentiment-neutral"
    return f'<span class="sentiment-badge {css}">{sentiment}</span>'

def get_status_pill(status):
    s = status.lower() if status else "pending"
    css_map = {"pending": "status-pending", "processing": "status-processing",
               "ocr_completed": "status-processing", "analyzed": "status-analyzed", "failed": "status-failed"}
    css = css_map.get(s, "status-pending")
    return f'<span class="status-pill {css}">{status}</span>'

def render_list(items, css_class="insight-list"):
    if not items:
        return '<p style="color:#6b7280; font-size:0.85rem;">Aucun élément.</p>'
    html = f'<ul class="insight-list {css_class}">'
    for item in items:
        html += f"<li>{item}</li>"
    html += "</ul>"
    return html

def render_tags(items):
    if not items:
        return ""
    return "".join(f'<span class="tag-badge">{t}</span>' for t in items)

def process_single_file(filepath, api_key):
    """Full pipeline: register → OCR → Analysis → DB save. Returns doc_id."""
    filename = os.path.basename(filepath)
    doc_id = add_document(filename, filepath)
    update_document_status(doc_id, "processing")
    
    # Step 1: OCR
    raw_text = extract_text_from_file(filepath, api_key)
    update_document_text(doc_id, raw_text, status="ocr_completed")
    
    # Step 2: LLM Analysis
    analysis = analyze_raw_text(doc_id, raw_text, api_key)
    save_analysis_result(doc_id, analysis)
    
    return doc_id

# ─────────────────────────── Sidebar ───────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    env_key = get_api_key() or ""
    api_key = st.text_input("Clé API Mistral", value=env_key, type="password",
                            placeholder="Entrez votre clé API…")
    
    st.markdown("---")
    st.markdown("## 📂 Auto-Watcher")
    st.caption(f"Dossier surveillé : `{os.path.abspath(WATCHED_FOLDER)}`")
    
    watcher_active = st.session_state.watcher_instance and st.session_state.watcher_instance.is_running
    
    if watcher_active:
        if st.button("⏹ Arrêter le watcher", use_container_width=True):
            st.session_state.watcher_instance.stop()
            st.session_state.watcher_instance = None
            st.rerun()
    else:
        if st.button("▶️ Démarrer le watcher", use_container_width=True):
            if not api_key:
                st.error("Veuillez d'abord entrer une clé API.")
            else:
                def _watcher_callback(fpath):
                    try:
                        process_single_file(fpath, api_key)
                    except Exception as e:
                        print(f"[Watcher] Pipeline error: {e}")
                
                w = FolderWatcher(WATCHED_FOLDER, _watcher_callback)
                w.start()
                st.session_state.watcher_instance = w
                st.rerun()
    
    watcher_status = "🟢 Actif" if watcher_active else "🔴 Inactif"
    st.markdown(f"**Statut :** {watcher_status}")
    
    st.markdown("---")
    st.markdown("### 📊 Base de données")
    all_docs = get_all_documents()
    analyzed_docs = get_analyzed_documents()
    st.metric("Documents totaux", len(all_docs))
    st.metric("Analysés", len(analyzed_docs))

# ─────────────────────────── Header ───────────────────────────
st.markdown('<div class="platform-title">🏢 HR Feedback Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="platform-subtitle">Plateforme d\'analyse intelligente de formulaires de feedback RH — OCR, LLM et insights exploitables.</div>', unsafe_allow_html=True)

# ─────────────────────────── Tabs ───────────────────────────
tab_upload, tab_docs, tab_analytics, tab_report = st.tabs([
    "📤 Upload & Traitement",
    "📋 Feedbacks Individuels",
    "📊 Analytique Globale",
    "📝 Rapport Exécutif"
])

# ═══════════════════════════ TAB 1: Upload ═══════════════════════════
with tab_upload:
    st.markdown("### Télécharger des formulaires de feedback")
    
    uploaded_files = st.file_uploader(
        "Glissez-déposez vos images ou PDF ici…",
        type=["jpg", "jpeg", "png", "webp", "pdf"],
        accept_multiple_files=True,
        help="Formats supportés : JPG, PNG, WebP, PDF. Upload unique ou par lots."
    )
    
    if uploaded_files:
        # Preview grid
        cols = st.columns(min(len(uploaded_files), 4))
        for i, f in enumerate(uploaded_files):
            with cols[i % 4]:
                if f.type and f.type.startswith("image"):
                    img = Image.open(f)
                    st.image(img, caption=f.name, width="stretch")
                else:
                    st.info(f"📄 {f.name}")
        
        if st.button("🚀 Lancer le traitement complet", use_container_width=True, type="primary"):
            if not api_key:
                st.error("⚠️ Veuillez configurer votre clé API Mistral dans la barre latérale.")
            else:
                progress = st.progress(0, text="Initialisation…")
                results_log = []
                total = len(uploaded_files)
                
                for idx, ufile in enumerate(uploaded_files):
                    progress.progress(
                        int((idx / total) * 100),
                        text=f"Traitement de {ufile.name} ({idx+1}/{total})…"
                    )
                    
                    # Save uploaded file to a temp path
                    ext = os.path.splitext(ufile.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                        tmp.write(ufile.getvalue())
                        tmp_path = tmp.name
                    
                    try:
                        doc_id = process_single_file(tmp_path, api_key)
                        results_log.append({"file": ufile.name, "status": "✅ Analysé", "doc_id": doc_id})
                    except Exception as e:
                        results_log.append({"file": ufile.name, "status": f"❌ Erreur: {e}", "doc_id": None})
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                
                progress.progress(100, text="Traitement terminé !")
                
                st.markdown("#### Résultats du traitement")
                for r in results_log:
                    st.markdown(f"- **{r['file']}** → {r['status']}")
                
                st.rerun()
    
    # ── Document Queue ──
    st.markdown("---")
    st.markdown("### 📋 File de documents")
    
    all_docs = get_all_documents()
    if not all_docs:
        st.info("Aucun document dans la base. Téléchargez des fichiers ci-dessus pour commencer.")
    else:
        for doc in all_docs:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{doc['filename']}**")
            with col2:
                st.markdown(get_status_pill(doc["status"]), unsafe_allow_html=True)
            with col3:
                st.caption(doc["uploaded_at"][:16])

# ═══════════════════════════ TAB 2: Individual Feedbacks ═══════════════════════════
with tab_docs:
    st.markdown("### 🔍 Recherche & Feedbacks individuels")
    
    search_kw = st.text_input("🔎 Rechercher par mot-clé (ex: communication, workload)…",
                              placeholder="Entrez un mot-clé…")
    
    if search_kw.strip():
        docs = search_documents(search_kw.strip())
        st.caption(f"{len(docs)} résultat(s) pour « {search_kw} »")
    else:
        docs = get_analyzed_documents()
    
    if not docs:
        st.info("Aucun feedback analysé trouvé. Veuillez d'abord traiter des documents dans l'onglet Upload.")
    else:
        for doc in docs:
            with st.expander(f"📄 {doc['filename']}  —  {get_sentiment_badge(doc.get('overall_sentiment', 'Neutral'))}", expanded=False):
                st.markdown(f"""
                <div class="glass-card">
                    <div class="glass-card-header">
                        {doc['filename']} &nbsp;&nbsp; {get_sentiment_badge(doc.get('overall_sentiment', 'Neutral'))}
                        &nbsp;&nbsp; Score: <strong style="color:#818cf8;">{doc.get('sentiment_score', '-')}/10</strong>
                    </div>
                """, unsafe_allow_html=True)
                
                # Summary
                st.markdown(f"**Résumé :** {doc.get('summary', 'N/A')}")
                
                # Themes
                st.markdown("**Thèmes :**")
                st.markdown(render_tags(doc.get("themes", [])), unsafe_allow_html=True)
                
                # Strengths
                st.markdown("**✅ Points forts :**")
                st.markdown(render_list(doc.get("strengths", []), "strength-list"), unsafe_allow_html=True)
                
                # Issues
                st.markdown("**⚠️ Axes d'amélioration :**")
                st.markdown(render_list(doc.get("improvement_areas", []), "issue-list"), unsafe_allow_html=True)
                
                # Quotes
                st.markdown("**💬 Citations représentatives :**")
                st.markdown(render_list(doc.get("quotes", []), "quote-list"), unsafe_allow_html=True)
                
                # Actions
                st.markdown("**🎯 Actions recommandées :**")
                st.markdown(render_list(doc.get("recommended_actions", []), "action-list"), unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Expandable raw text
                with st.expander("📝 Texte OCR brut"):
                    st.text_area("Texte extrait", doc.get("raw_text", ""), height=200, disabled=True, key=f"raw_{doc['id']}")
                
                # JSON export per document
                doc_json = {
                    "document_id": doc["id"],
                    "filename": doc["filename"],
                    "summary": doc.get("summary"),
                    "overall_sentiment": doc.get("overall_sentiment"),
                    "sentiment_score": doc.get("sentiment_score"),
                    "strengths": doc.get("strengths", []),
                    "improvement_areas": doc.get("improvement_areas", []),
                    "themes": doc.get("themes", []),
                    "representative_quotes": doc.get("quotes", []),
                    "recommended_actions": doc.get("recommended_actions", [])
                }
                st.download_button(
                    "📥 Télécharger JSON",
                    data=json.dumps(doc_json, indent=2, ensure_ascii=False),
                    file_name=f"feedback_{doc['id']}.json",
                    mime="application/json",
                    key=f"dl_{doc['id']}"
                )

# ═══════════════════════════ TAB 3: Analytics ═══════════════════════════
with tab_analytics:
    st.markdown("### 📊 Analytique Globale")
    
    analyzed = get_analyzed_documents()
    agg = compute_aggregation(analyzed)
    
    if agg["total_count"] == 0:
        st.info("Aucune donnée d'analyse disponible. Traitez d'abord des documents.")
    else:
        # ── Top Metrics Row ──
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{agg['total_count']}</div>
                <div class="metric-label">Documents analysés</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{agg['average_score']}</div>
                <div class="metric-label">Score moyen (1-10)</div>
            </div>""", unsafe_allow_html=True)
        with m3:
            pos_pct = int((agg['sentiment_distribution']['Positive'] / agg['total_count']) * 100) if agg['total_count'] else 0
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value" style="color:#34d399;">{pos_pct}%</div>
                <div class="metric-label">Feedbacks positifs</div>
            </div>""", unsafe_allow_html=True)
        with m4:
            neg_pct = int((agg['sentiment_distribution']['Negative'] / agg['total_count']) * 100) if agg['total_count'] else 0
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value" style="color:#f87171;">{neg_pct}%</div>
                <div class="metric-label">Feedbacks négatifs</div>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("")
        
        # ── Charts Row ──
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("#### Distribution des sentiments")
            sent_data = agg["sentiment_distribution"]
            fig_pie = px.pie(
                names=list(sent_data.keys()),
                values=list(sent_data.values()),
                color=list(sent_data.keys()),
                color_discrete_map={
                    "Positive": "#34d399",
                    "Neutral": "#fbbf24",
                    "Negative": "#f87171"
                },
                hole=0.45
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#d1d5db", family="Inter"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                margin=dict(l=20, r=20, t=30, b=40),
                height=350
            )
            st.plotly_chart(fig_pie, use_container_width=True, key="pie_chart")
        
        with chart_col2:
            st.markdown("#### Thèmes les plus fréquents")
            if agg["theme_counts"]:
                theme_names = [t[0] for t in agg["theme_counts"][:10]]
                theme_values = [t[1] for t in agg["theme_counts"][:10]]
                
                fig_bar = px.bar(
                    x=theme_values,
                    y=theme_names,
                    orientation="h",
                    color=theme_values,
                    color_continuous_scale=["#6366f1", "#a855f7", "#ec4899"]
                )
                fig_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#d1d5db", family="Inter"),
                    yaxis=dict(autorange="reversed"),
                    xaxis_title="Fréquence",
                    yaxis_title="",
                    coloraxis_showscale=False,
                    margin=dict(l=20, r=20, t=30, b=40),
                    height=350
                )
                st.plotly_chart(fig_bar, use_container_width=True, key="bar_chart")
            else:
                st.info("Pas de thèmes disponibles.")
        
        # ── Sentiment Score Distribution ──
        st.markdown("#### Distribution des scores de sentiment")
        scores = [d.get("sentiment_score", 5) for d in analyzed]
        fig_hist = px.histogram(
            x=scores,
            nbins=10,
            range_x=[1, 10],
            color_discrete_sequence=["#818cf8"]
        )
        fig_hist.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#d1d5db", family="Inter"),
            xaxis_title="Score de sentiment",
            yaxis_title="Nombre de documents",
            margin=dict(l=40, r=20, t=30, b=40),
            height=280
        )
        st.plotly_chart(fig_hist, use_container_width=True, key="hist_chart")
        
        # ── Top Strengths & Issues ──
        str_col, iss_col = st.columns(2)
        with str_col:
            st.markdown("#### ✅ Forces principales")
            st.markdown(render_list(agg["all_strengths"][:10], "strength-list"), unsafe_allow_html=True)
        with iss_col:
            st.markdown("#### ⚠️ Problèmes récurrents")
            st.markdown(render_list(agg["all_improvement_areas"][:10], "issue-list"), unsafe_allow_html=True)
        
        # ── Export all data ──
        st.markdown("---")
        all_json = json.dumps(
            [{"id": d["id"], "filename": d["filename"], "summary": d.get("summary"),
              "overall_sentiment": d.get("overall_sentiment"), "sentiment_score": d.get("sentiment_score"),
              "strengths": d.get("strengths", []), "improvement_areas": d.get("improvement_areas", []),
              "themes": d.get("themes", []), "quotes": d.get("quotes", []),
              "recommended_actions": d.get("recommended_actions", [])} for d in analyzed],
            indent=2, ensure_ascii=False
        )
        st.download_button(
            "📥 Exporter toutes les analyses (JSON)",
            data=all_json,
            file_name="all_feedback_analyses.json",
            mime="application/json"
        )

# ═══════════════════════════ TAB 4: Executive Report ═══════════════════════════
with tab_report:
    st.markdown("### 📝 Rapport Exécutif RH")
    st.caption("Générez un rapport de synthèse complet destiné à la direction RH, basé sur l'ensemble des feedbacks analysés.")
    
    analyzed = get_analyzed_documents()
    agg = compute_aggregation(analyzed)
    
    if agg["total_count"] == 0:
        st.info("Aucune donnée disponible. Traitez des documents avant de générer un rapport.")
    else:
        if st.button("🧠 Générer le rapport exécutif", use_container_width=True, type="primary"):
            if not api_key:
                st.error("Veuillez configurer votre clé API Mistral.")
            else:
                with st.spinner("Génération du rapport exécutif avec Mistral Large…"):
                    try:
                        report = generate_executive_report(agg, api_key)
                        st.session_state.exec_report = report
                    except Exception as e:
                        st.error(f"Erreur lors de la génération : {e}")
        
        if st.session_state.exec_report:
            st.markdown("---")
            st.markdown(st.session_state.exec_report)
            
            st.markdown("---")
            st.download_button(
                "📥 Télécharger le rapport (Markdown)",
                data=st.session_state.exec_report,
                file_name="rapport_executif_rh.md",
                mime="text/markdown"
            )
