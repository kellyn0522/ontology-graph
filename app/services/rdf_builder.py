# ttl 형태로 RDF Graph에 넣는 코드

import re

from rdflib import Graph
from rdflib import Namespace
from rdflib import URIRef
from rdflib import RDF
from rdflib import RDFS


class RDFBuilder:

    def __init__(self):

        self.graph = Graph()

        self.namespace = Namespace(
            "http://example.org/ontology/"
        )

        self.graph.bind(
            "onto",
            self.namespace
        )

    def _sanitize_uri(
        self,
        value: str
    ) -> str:
        """
        RDF URI 안전 문자열로 변환

        예:
            disease codes C00 to C97
            -> disease_codes_C00_to_C97
        """

        # 앞뒤 공백 제거
        value = value.strip()

        # 공백 -> _
        value = value.replace(
            " ",
            "_"
        )

        # 특수문자 제거
        value = re.sub(
            r"[^a-zA-Z0-9_]",
            "",
            value
        )

        return value

    def _create_uri(
        self,
        value: str
    ) -> URIRef:
        """
        Namespace 기반 URI 생성
        """

        safe_value = self._sanitize_uri(
            value
        )

        return URIRef(
            self.namespace + safe_value
        )

    def build(self, ontology_data: dict):
        """
        Refined Ontology를 RDF Graph로 변환

        Args:
            ontology_data (dict):
                refined ontology json
        """

        hierarchies = ontology_data.get(
            "refined_hierarchies",
            []
        )

        attributes = ontology_data.get(
            "refined_attributes",
            []
        )

        relations = ontology_data.get(
            "refined_relations",
            []
        )

        # -------------------------------------------------
        # HIERARCHY RDF
        # -------------------------------------------------

        for hierarchy in hierarchies:

            parent = self._create_uri(
                hierarchy["parent"]
            )

            child = self._create_uri(
                hierarchy["child"]
            )

            # child rdfs:subClassOf parent
            self.graph.add((
                child,
                RDFS.subClassOf,
                parent
            ))

        # -------------------------------------------------
        # ATTRIBUTE RDF
        # -------------------------------------------------

        for attr in attributes:

            class_uri = self._create_uri(
                attr["class"]
            )

            attribute_uri = self._create_uri(
                attr["attribute"]
            )

            relation_uri = self._create_uri(
                attr["relation"]
            )

            self.graph.add((
                class_uri,
                relation_uri,
                attribute_uri
            ))

        # -------------------------------------------------
        # SEMANTIC RELATION RDF
        # -------------------------------------------------

        for rel in relations:

            subject_uri = self._create_uri(
                rel["subject"]
            )

            predicate_uri = self._create_uri(
                rel["predicate"]
            )

            object_uri = self._create_uri(
                rel["object"]
            )

            self.graph.add((
                subject_uri,
                predicate_uri,
                object_uri
            ))

        return self.graph

    def save(
        self,
        output_path: str
    ):
        """
        RDF Graph를 Turtle(.ttl) 파일로 저장
        """

        self.graph.serialize(
            destination=output_path,
            format="turtle"
        )

    def print_graph(self):
        """
        RDF Triple 출력
        """

        print("\n===== RDF GRAPH =====\n")

        for subj, pred, obj in self.graph:

            print(
                f"{subj} "
                f"{pred} "
                f"{obj}"
            )