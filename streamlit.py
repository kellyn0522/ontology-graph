from dotenv import load_dotenv
load_dotenv()


import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app.services.pdf_loader import PDFLoader
from app.services.class_extractor import ClassExtractor
from app.services.hierarchy_builder import HierarchyBuilder
from app.services.relation_extractor import RelationExtractor
from app.services.ontology_refiner import OntologyRefiner
from app.services.rdf_builder import RDFBuilder
from app.services.graph_visualizer import GraphVisualizer


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="LLM Ontology Construction",
    page_icon="🧠",
    layout="wide"
)

# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------

st.title("🧠 LLM-Based Ontology Construction")

st.markdown("""
PDF 문서를 기반으로 LLM이 Ontology 구조와 Semantic Relation을 추출하고 Knowledge Graph 형태로 시각화

### Pipeline

PDF
→ Class Extraction
→ Hierarchy Construction
→ Semantic Relation Extraction
→ Ontology Refinement
→ RDF Graph
→ Knowledge Graph Visualization
""")

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.markdown(
    """
    <div style="margin-top: 2.0rem;"></div>
    """,
    unsafe_allow_html=True
)

st.sidebar.title("⚙️ Settings")

uploaded_file = st.sidebar.file_uploader(
    "Upload PDF",
    type=["pdf"]
)

run_button = st.sidebar.button(
    "🚀 Generate"
)

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

if uploaded_file and run_button:

    # ---------------------------------------------------------
    # TEMP FILE
    # ---------------------------------------------------------

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ) as tmp_file:

        tmp_file.write(uploaded_file.read())

        temp_pdf_path = tmp_file.name

    # ---------------------------------------------------------
    # PDF LOAD
    # ---------------------------------------------------------

    with st.spinner("📄 Loading PDF..."):

        loader = PDFLoader(
            pdf_path=temp_pdf_path
        )

        text = loader.load_text()

    st.success("1. PDF Loaded")

    # ---------------------------------------------------------
    # TEXT PREVIEW
    # ---------------------------------------------------------

    with st.expander("📄 Extracted Text"):

        st.text_area(
            "Document Text",
            text[:5000],
            height=300
        )

    # ---------------------------------------------------------
    # CLASS EXTRACTION
    # ---------------------------------------------------------

    with st.spinner("🧠 Extracting Core Classes..."):

        class_extractor = ClassExtractor()

        class_result = class_extractor.extract(
            text
        )

        core_classes = class_result[
            "core_classes"
        ]

    st.success("2. Core Classes Extracted")

    with st.expander("📚 Core Classes"):
        st.json(core_classes)

    # ---------------------------------------------------------
    # HIERARCHY
    # ---------------------------------------------------------

    with st.spinner("🌳 Building Hierarchy..."):

        hierarchy_builder = HierarchyBuilder()

        hierarchy_result = hierarchy_builder.build(
            text=text,
            core_classes=core_classes
        )

        hierarchies = hierarchy_result[
            "hierarchies"
        ]

    st.success("3. Hierarchy Constructed")

    with st.expander("🌳 Hierarchies"):
        st.json(hierarchies)

    # ---------------------------------------------------------
    # RELATION EXTRACTION
    # ---------------------------------------------------------

    with st.spinner("🔗 Extracting Semantic Relations..."):

        relation_extractor = RelationExtractor()

        relation_result = relation_extractor.extract(
            text=text,
            core_classes=core_classes,
            hierarchies=hierarchies,
            attributes=[]
        )

        relations = relation_result[
            "relations"
        ]

    st.success("4. Semantic Relations Extracted")

    with st.expander("🔗 Semantic Relations"):
        st.json(relations)

    # ---------------------------------------------------------
    # ONTOLOGY REFINEMENT
    # ---------------------------------------------------------

    with st.spinner("✨ Refining Ontology Graph..."):

        ontology_refiner = OntologyRefiner()

        refined_result = ontology_refiner.refine(
            core_classes=core_classes,
            hierarchies=hierarchies,
            attributes=[],
            relations=relations
        )

    st.success("5. Ontology Refinement Completed")

    with st.expander("✨ Refined Ontology"):
        st.json(refined_result)

    # ---------------------------------------------------------
    # RDF BUILD
    # ---------------------------------------------------------

    with st.spinner("🧾 Building RDF Graph..."):

        rdf_builder = RDFBuilder()

        rdf_graph = rdf_builder.build(
            refined_result
        )

        output_dir = Path(
            "data/output"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        rdf_output_path = (
            output_dir / "ontology.ttl"
        )

        rdf_builder.save(
            str(rdf_output_path)
        )

    st.success("6. RDF Graph Generated")

    # ---------------------------------------------------------
    # RDF PREVIEW
    # ---------------------------------------------------------

    with st.expander("🧾 RDF Turtle Preview"):

        with open(
            rdf_output_path,
            "r",
            encoding="utf-8"
        ) as f:

            rdf_content = f.read()

        st.code(
            rdf_content[:5000],
            language="ttl"
        )

    # ---------------------------------------------------------
    # GRAPH TABS
    # ---------------------------------------------------------

    st.subheader("🕸️ Knowledge Graph Views")

    tab1, tab2 = st.tabs([
        "Full Graph",
        "Taxonomy View",
        # "Business View",
        # "Dependency View",
        # "Document Flow View"
    ])

    # ---------------------------------------------------------
    # FULL GRAPH
    # ---------------------------------------------------------

    with tab1:

        full_visualizer = GraphVisualizer()

        full_visualizer.build(
            ontology_data=refined_result
        )

        full_path = (
            output_dir / "full_graph.html"
        )

        full_visualizer.save(
            str(full_path)
        )

        with open(
            full_path,
            "r",
            encoding="utf-8"
        ) as f:

            html = f.read()

        components.html(
            html,
            height=800,
            scrolling=True
        )

    # ---------------------------------------------------------
    # TAXONOMY VIEW
    # ---------------------------------------------------------

    with tab2:

        taxonomy_visualizer = GraphVisualizer()

        taxonomy_visualizer.build(
            ontology_data=refined_result,
            allowed_relations=[
                "subClassOf"
            ]
        )

        taxonomy_path = (
            output_dir / "taxonomy_graph.html"
        )

        taxonomy_visualizer.save(
            str(taxonomy_path)
        )

        with open(
            taxonomy_path,
            "r",
            encoding="utf-8"
        ) as f:

            html = f.read()

        components.html(
            html,
            height=800,
            scrolling=True
        )

    

    # ---------------------------------------------------------
    # DOWNLOAD RDF
    # ---------------------------------------------------------

    st.download_button(
        label="⬇️ Download RDF (.ttl)",
        data=rdf_content,
        file_name="ontology.ttl",
        mime="text/plain"
    )