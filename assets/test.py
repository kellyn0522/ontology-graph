
import json

from dotenv import load_dotenv

load_dotenv()

from app.services.pdf_loader import PDFLoader
from app.services.class_extractor import ClassExtractor
from app.services.hierarchy_builder import HierarchyBuilder
from app.services.attribute_extractor import AttributeExtractor
from app.services.relation_extractor import RelationExtractor
from app.services.ontology_refiner import OntologyRefiner
from app.services.rdf_builder import RDFBuilder
from app.services.graph_visualizer import GraphVisualizer



def main():

    # -----------------------------
    # PDF LOAD
    # -----------------------------
    loader = PDFLoader(
        pdf_path="assets/test2.pdf"
    )

    text = loader.load_text()

    print("\n===== PDF LOADED =====\n")

    print(text[:1000])

    # -----------------------------
    # CLASS EXTRACTION
    # -----------------------------
    class_extractor = ClassExtractor()

    class_result = class_extractor.extract(text)

    core_classes = class_result["core_classes"]

    print("\n===== CORE CLASSES =====\n")

    for idx, class_name in enumerate(
        core_classes,
        start=1
    ):
        print(f"{idx}. {class_name}")

    # -----------------------------
    # SAVE CLASS RESULT
    # -----------------------------
    with open(
        "data/output/classes.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            class_result,
            f,
            indent=2,
            ensure_ascii=False
        )

    # -----------------------------
    # HIERARCHY BUILDING
    # -----------------------------
    hierarchy_builder = HierarchyBuilder()

    hierarchy_result = hierarchy_builder.build(
        text=text,
        core_classes=core_classes
    )

    print("\n===== HIERARCHY RESULT =====\n")

    hierarchies = hierarchy_result["hierarchies"]

    for hierarchy in hierarchies:

        parent = hierarchy["parent"]
        child = hierarchy["child"]

        print(
            f"{child} "
            f"--- subClassOf ---> "
            f"{parent}"
        )

    # -----------------------------
    # SAVE HIERARCHY RESULT
    # -----------------------------
    with open(
        "data/output/hierarchies.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            hierarchy_result,
            f,
            indent=2,
            ensure_ascii=False
        )

    # -----------------------------
    # ATTRIBUTE EXTRACTION
    # -----------------------------
    attribute_extractor = AttributeExtractor()

    attribute_result = attribute_extractor.extract(
        text=text,
        core_classes=core_classes,
        hierarchies=hierarchies
    )

    print("\n===== ATTRIBUTE RESULT =====\n")

    attributes = attribute_result["attributes"]

    for attr in attributes:

        class_name = attr["class"]
        attribute_name = attr["attribute"]
        relation = attr["relation"]

        print(
            f"{class_name} "
            f"--- {relation} ---> "
            f"{attribute_name}"
        )

    # -----------------------------
    # SAVE ATTRIBUTE RESULT
    # -----------------------------
    with open(
        "data/output/attributes.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            attribute_result,
            f,
            indent=2,
            ensure_ascii=False
        )

    # -----------------------------
    # RELATION EXTRACTION
    # -----------------------------
    relation_extractor = RelationExtractor()

    relation_result = relation_extractor.extract(
        text=text,
        core_classes=core_classes,
        hierarchies=hierarchies,
        attributes=attributes
    )

    print("\n===== RELATION RESULT =====\n")

    relations = relation_result["relations"]

    for rel in relations:

        subject = rel["subject"]
        predicate = rel["predicate"]
        object_ = rel["object"]

        print(
            f"{subject} "
            f"--- {predicate} ---> "
            f"{object_}"
        )

    # -----------------------------
    # SAVE RELATION RESULT
    # -----------------------------
    with open(
        "data/output/relations.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            relation_result,
            f,
            indent=2,
            ensure_ascii=False
        )

    # -----------------------------
    # ONTOLOGY REFINEMENT
    # -----------------------------
    ontology_refiner = OntologyRefiner()

    refined_result = ontology_refiner.refine(
        core_classes=core_classes,
        hierarchies=hierarchies,
        attributes=attributes,
        relations=relations
    )

    print("\n===== ONTOLOGY REFINEMENT RESULT =====\n")

    refined_hierarchies = (
        refined_result["refined_hierarchies"]
    )

    refined_attributes = (
        refined_result["refined_attributes"]
    )

    refined_relations = (
        refined_result["refined_relations"]
    )

    # -----------------------------
    # PRINT REFINED HIERARCHIES
    # -----------------------------
    print("\n--- REFINED HIERARCHIES ---\n")

    for hierarchy in refined_hierarchies:

        print(
            f"{hierarchy['child']} "
            f"--- {hierarchy['relation']} ---> "
            f"{hierarchy['parent']}"
        )

    # -----------------------------
    # PRINT REFINED ATTRIBUTES
    # -----------------------------
    print("\n--- REFINED ATTRIBUTES ---\n")

    for attr in refined_attributes:

        print(
            f"{attr['class']} "
            f"--- {attr['relation']} ---> "
            f"{attr['attribute']}"
        )

    # -----------------------------
    # PRINT REFINED RELATIONS
    # -----------------------------
    print("\n--- REFINED RELATIONS ---\n")

    for rel in refined_relations:

        print(
            f"{rel['subject']} "
            f"--- {rel['predicate']} ---> "
            f"{rel['object']}"
        )

    # -----------------------------
    # SAVE REFINED RESULT
    # -----------------------------
    with open(
        "data/output/refined_ontology.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            refined_result,
            f,
            indent=2,
            ensure_ascii=False
        )

    # -----------------------------
    # RDF BUILDING
    # -----------------------------
    rdf_builder = RDFBuilder()

    rdf_graph = rdf_builder.build(
        ontology_data=refined_result
    )

    print("\n===== RDF BUILD RESULT =====\n")

    rdf_builder.print_graph()

    # -----------------------------
    # SAVE RDF GRAPH
    # -----------------------------
    rdf_builder.save(
        output_path="data/output/ontology.ttl"
    )

    # -----------------------------
    # GRAPH VISUALIZATION
    # -----------------------------
    graph_visualizer = GraphVisualizer()

    graph_visualizer.build(
        ontology_data=refined_result
    )

    graph_visualizer.save(
        output_path="data/output/ontology_graph.html"
    )


    print("\n===== SAVED =====\n")

    print("classes.json 저장 완료")
    print("hierarchies.json 저장 완료")
    print("attributes.json 저장 완료")
    print("relations.json 저장 완료")
    print("refined_ontology.json 저장 완료")
    print("ontology.ttl 저장 완료")
    print("ontology_graph.html 저장 완료")



if __name__ == "__main__":
    main()