"""
MPV - Modular Phenotype-driven Variant prioritization
Streamlit Web Application for Clinical Decision Support in IRDs
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# Import the framework modules
from clinical_support import ClinicalSupportEngine
from decision_tree import InteractiveSession, Response

# Page configuration
st.set_page_config(
    page_title="MPV - IRD Clinical Decision Support",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #29B5E8;
        margin-bottom: 0;
        text-shadow: 0 0 10px rgba(41, 181, 232, 0.3);
    }
    .sub-header {
        font-size: 1.1rem;
        color: #B0BEC5;
        margin-top: 0;
        font-weight: 300;
        letter-spacing: 0.5px;
    }
    .stApp {
        background-color: #0E1117;
    }
    .gene-tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        margin: 3px;
        font-size: 0.9rem;
        font-weight: 500;
        color: #000000;
    }
    .core-gene {
        background-color: #81C784; /* Green matching dark theme */
        border: 1px solid #4CAF50;
    }
    .peripheral-gene {
        background-color: #FFF59D; /* Yellow */
        border: 1px solid #FBC02D;
    }
    .unstable-gene {
        background-color: #FFCCBC; /* Orange/Red */
        border: 1px solid #FF7043;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #E1F5FE;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_engine():
    """Load the clinical support engine (cached)."""
    return ClinicalSupportEngine()


def main():
    # Header
    st.markdown('<p class="main-header">👁️ MPV Clinical Decision Support</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Modular Phenotype-driven Variant prioritization for Inherited Retinal Diseases</p>', unsafe_allow_html=True)
    st.divider()
    
    # Load engine
    engine = load_engine()
    
    # Sidebar - Mode selection
    st.sidebar.title("🔧 Query Mode")
    mode = st.sidebar.radio(
        "Select mode:",
        ["📋 Phenotype Query", "🔄 Interactive Q&A", "🧬 Gene Query"],
        index=0
    )
    
    st.sidebar.divider()
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "This tool helps identify disease modules and candidate genes "
        "based on clinical phenotypes in Inherited Retinal Diseases."
    )
    
    # Main content based on mode
    if mode == "📋 Phenotype Query":
        phenotype_query_mode(engine)
    elif mode == "🔄 Interactive Q&A":
        interactive_mode(engine)
    else:
        gene_query_mode(engine)


def phenotype_query_mode(engine):
    """Phenotype-based query mode."""
    st.header("📋 Phenotype Query")
    st.write("Enter observed and excluded phenotypes to find matching disease modules and candidate genes.")
    
    # Initialize example state BEFORE widgets are created
    if "example_observed" not in st.session_state:
        st.session_state.example_observed = ""
    if "example_excluded" not in st.session_state:
        st.session_state.example_excluded = ""
    
    # Example buttons - BEFORE text areas
    st.markdown("**Quick examples:**")
    col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)
    
    with col_ex1:
        if st.button("🔵 BBS Example"):
            st.session_state.example_observed = "Obesity\nPolydactyly\nRod-cone dystrophy"
            st.session_state.example_excluded = ""
            st.rerun()
    with col_ex2:
        if st.button("🟢 Usher Example"):
            st.session_state.example_observed = "Sensorineural hearing impairment\nRod-cone dystrophy"
            st.session_state.example_excluded = ""
            st.rerun()
    with col_ex3:
        if st.button("🟡 ACHM Example"):
            st.session_state.example_observed = "Photophobia\nColor blindness\nNystagmus"
            st.session_state.example_excluded = ""
            st.rerun()
    with col_ex4:
        if st.button("🟠 Mito Example"):
            st.session_state.example_observed = "Optic atrophy\nAtaxia\nPeripheral neuropathy"
            st.session_state.example_excluded = ""
            st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Observed Phenotypes")
        st.caption("Phenotypes that ARE present in the patient")
        observed_text = st.text_area(
            "Enter phenotypes (one per line):",
            value=st.session_state.example_observed,
            height=150,
            placeholder="Obesity\nPolydactyly\nRod-cone dystrophy"
        )
    
    with col2:
        st.subheader("❌ Excluded Phenotypes")
        st.caption("Phenotypes that are NOT present in the patient")
        excluded_text = st.text_area(
            "Enter phenotypes (one per line):",
            value=st.session_state.example_excluded,
            height=150,
            placeholder="Hearing impairment"
        )
    
    st.divider()
    
    if st.button("🔍 Analyze", type="primary", use_container_width=True):
        # Parse inputs
        observed = [p.strip() for p in observed_text.split("\n") if p.strip()]
        excluded = [p.strip() for p in excluded_text.split("\n") if p.strip()]
        
        if not observed and not excluded:
            st.warning("Please enter at least one phenotype.")
            return
        
        with st.spinner("Analyzing phenotypes..."):
            result = engine.query(observed=observed, excluded=excluded)
        
        display_query_results(result)


def display_query_results(result):
    """Display query results in a formatted way."""
    
    # Unmatched warning
    if result.unmatched_inputs:
        st.warning(f"⚠️ Unrecognized phenotypes: {', '.join(result.unmatched_inputs)}")
    
    # Best module
    if result.best_module and result.best_module.score > 0:
        st.success(f"### 🎯 Best Match: Module {result.best_module.module_id}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Score", f"{result.best_module.score:.3f}")
        col2.metric("Confidence", f"{result.best_module.confidence:.1%}")
        col3.metric("Genes in Module", result.best_module.gene_count)
        
        # Top modules table
        st.subheader("📊 Top 5 Modules")
        module_data = []
        for m in result.matched_modules[:5]:
            module_data.append({
                "Module": m.module_id,
                "Score": f"{m.score:.3f}",
                "Confidence": f"{m.confidence:.1%}",
                "Genes": m.gene_count
            })
        st.dataframe(pd.DataFrame(module_data), use_container_width=True, hide_index=True)
        
        # Candidate genes
        st.subheader("🧬 Candidate Genes")
        gene_cols = st.columns(4)
        for i, gene in enumerate(result.candidate_genes[:12]):
            col = gene_cols[i % 4]
            class_color = {"core": "🟢", "peripheral": "🟡", "unstable": "🟠"}.get(gene.classification, "⚪")
            score_text = f"{gene.support_score:.2f}" if gene.support_score is not None else "NA"
            col.markdown(
                f"{class_color} **{gene.gene}**<br>"
                f"<span style='font-size:0.8em; color:#B0BEC5'>Score: {score_text}</span>",
                unsafe_allow_html=True
            )
        
        # Predicted phenotypes
        if result.predicted_phenotypes:
            st.subheader("🔮 Predicted Missing Phenotypes")
            for pheno in result.predicted_phenotypes[:5]:
                st.markdown(f"- **{pheno.name}** (prevalence: {pheno.prevalence:.1f}%)")
        
        # Discriminative Questions (Safeguard)
        if result.discriminative_questions:
            st.subheader("❓ Discriminative Questions")
            st.caption("Ask these to confirm the best match against the runner-up module:")
            for q in result.discriminative_questions[:5]:
                st.markdown(f"- **{q.name}** ({q.reason})")
        
        # Alternative Candidates (Safeguard)
        if result.alternative_genes:
            with st.expander("🔍 See top candidates from other modules (Safeguard)"):
                st.caption("Top scoring genes from non-selected modules. Check these if the main result seems incorrect.")
                alt_cols = st.columns(3)
                for i, gene in enumerate(result.alternative_genes):
                    col = alt_cols[i % 3]
                    score_text = f"{gene.support_score:.2f}"
                    col.markdown(
                        f"**{gene.gene}** (Module {gene.module_id})<br>"
                        f"<span style='font-size:0.8em; color:#B0BEC5'>Score: {score_text}</span>",
                        unsafe_allow_html=True
                    )
    else:
        st.info("No strong module match found. Try adding more specific phenotypes.")


def interactive_mode(engine):
    """Interactive Yes/No/Unknown Q&A mode."""
    st.header("🔄 Interactive Q&A Mode")
    st.write("Answer questions about phenotypes step by step. The system will update predictions after each answer.")
    
    # Initialize session state
    if "interactive_session" not in st.session_state:
        st.session_state.interactive_session = InteractiveSession(engine.loader)
        st.session_state.question_history = []
    
    session = st.session_state.interactive_session
    
    # Reset button
    if st.button("🔄 Reset Session"):
        st.session_state.interactive_session = InteractiveSession(engine.loader)
        st.session_state.question_history = []
        st.rerun()
    
    # Current status
    col1, col2 = st.columns([2, 1])
    
    with col1:
        best = session.get_best_module()
        if best and best.score > 0:
            st.success(f"**Current Best Match:** Module {best.module_id} (confidence: {best.confidence:.1%})")
        else:
            st.info("Answer some questions to start the analysis.")
    
    with col2:
        st.metric("Questions Answered", len(session.state.history))
    
    st.divider()
    
    # Question input
    st.subheader("📝 Add Phenotype")
    
    input_col, answer_col = st.columns([3, 1])
    
    with input_col:
        phenotype_input = st.text_input(
            "Enter a phenotype name or HPO ID:",
            placeholder="e.g., Rod-cone dystrophy or HP:0000510"
        )
    
    with answer_col:
        st.write("")  # Spacing
        answer = st.radio("Response:", ["Yes", "No", "Unknown"], horizontal=True)
    
    if st.button("➕ Add Answer", use_container_width=True):
        if phenotype_input:
            response_map = {"Yes": Response.YES, "No": Response.NO, "Unknown": Response.UNKNOWN}
            session.answer(phenotype_input, response_map[answer], phenotype_input)
            st.session_state.question_history.append((phenotype_input, answer))
            st.rerun()
        else:
            st.warning("Please enter a phenotype.")
    
    # Suggested next question
    st.divider()
    next_q = session.get_next_question()
    if next_q:
        st.subheader("💡 Suggested Next Question")
        st.info(f"**{next_q.name}** ({next_q.hpo_id})")
        
        q_col1, q_col2, q_col3 = st.columns(3)
        if q_col1.button("✅ Yes", key="sugg_yes"):
            session.answer(next_q.hpo_id, Response.YES, next_q.name)
            st.rerun()
        if q_col2.button("❌ No", key="sugg_no"):
            session.answer(next_q.hpo_id, Response.NO, next_q.name)
            st.rerun()
        if q_col3.button("❓ Unknown", key="sugg_unk"):
            session.answer(next_q.hpo_id, Response.UNKNOWN, next_q.name)
            st.rerun()
    
    # Show history
    if session.state.history:
        st.divider()
        st.subheader("📜 Answer History")
        history_data = []
        for name, hpo_id, resp in session.state.history:
            emoji = {"yes": "✅", "no": "❌", "unknown": "❓"}.get(resp.value, "")
            history_data.append({"Phenotype": name, "Answer": f"{emoji} {resp.value.upper()}"})
        st.dataframe(pd.DataFrame(history_data), use_container_width=True, hide_index=True)
    
    # Current results
    if best and best.score > 0:
        st.divider()
        st.subheader("🧬 Current Candidate Genes")
        genes = session.get_candidate_genes()[:10]
        gene_cols = st.columns(5)
        for i, gene in enumerate(genes):
            col = gene_cols[i % 5]
            class_color = {"core": "🟢", "peripheral": "🟡", "unstable": "🟠"}.get(gene.classification, "⚪")
            score_text = f"{gene.support_score:.2f}" if gene.support_score is not None else "NA"
            col.markdown(
                f"{class_color} **{gene.gene}**<br>"
                f"<span style='font-size:0.8em; color:#B0BEC5'>Score: {score_text}</span>",
                unsafe_allow_html=True
            )


def gene_query_mode(engine):
    """Gene-based query mode."""
    st.header("🧬 Gene Query")
    st.write("Look up a gene to see its module, related genes, and characteristic phenotypes.")
    
    gene_input = st.text_input(
        "Enter gene symbol:",
        placeholder="e.g., RPGR, BBS1, CNGA3"
    )
    
    # Quick examples
    st.markdown("**Quick examples:**")
    gene_cols = st.columns(6)
    example_genes = ["RPGR", "BBS1", "USH2A", "CNGA3", "CHM", "OPA1"]
    for i, gene in enumerate(example_genes):
        if gene_cols[i].button(gene):
            gene_input = gene
    
    if gene_input:
        result = engine.query_gene(gene_input.strip().upper())
        
        if result:
            st.success(f"### Gene: {result.gene}")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Module", result.module_id)
            col2.metric("Classification", result.classification.upper())
            col3.metric("Stability Score", f"{result.stability_score:.3f}")
            
            # Related genes
            st.subheader("🔗 Related Genes in Module")
            related = [g for g in result.module_genes if g.classification == "core"][:10]
            gene_cols = st.columns(5)
            for i, gene in enumerate(related):
                col = gene_cols[i % 5]
                col.markdown(f"🟢 **{gene.gene}**")
            
            # Characteristic phenotypes
            st.subheader("📋 Characteristic Phenotypes")
            for pheno in result.characteristic_phenotypes[:10]:
                st.markdown(f"- **{pheno.name}** ({pheno.prevalence:.1f}% prevalence)")
        else:
            st.error(f"Gene '{gene_input}' not found in the database.")


if __name__ == "__main__":
    main()
