# 지금까지 만들어진 온톨로지 품질 정제
# 중복 relation 생성 제거 / 의미 충돌 확인 / disconnected graph / 이상한 relation / ontology level mismatch / naming inconsistency 등 확인

import json
import re

from app.configs.settings import OPENAI_API_KEY, LLM_MODEL
from collections import defaultdict
from openai import OpenAI


class OntologyRefiner:

    ALLOWED_RELATIONS = [
        "subClassOf",
        "hasProperty",
        "belongsTo",
        "manages",
        "subscribesTo",
        "includes",
        "requires",
        "covers",
        "claims"
    ]

    def __init__(self):

        self.client = OpenAI(
            api_key=OPENAI_API_KEY
        )

    def _extract_json(self, text: str) -> dict:
        """
        LLM 응답에서 JSON 부분만 추출
        """

        text = text.strip()

        text = re.sub(r"^```json", "", text)
        text = re.sub(r"^```", "", text)
        text = re.sub(r"```$", "", text)

        text = text.strip()

        match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            raise ValueError("JSON object not found")

        return json.loads(match.group(0))

    def _remove_duplicate_hierarchies(
        self,
        hierarchies: list
    ) -> list:
        """
        Hierarchy 중복 제거
        """

        seen = set()

        refined = []

        for h in hierarchies:

            key = (
                h["parent"],
                h["child"],
                h["relation"]
            )

            if key not in seen:

                seen.add(key)

                refined.append(h)

        return refined

    def _remove_duplicate_attributes(
        self,
        attributes: list
    ) -> list:
        """
        Attribute 중복 제거
        """

        seen = set()

        refined = []

        for attr in attributes:

            key = (
                attr["class"],
                attr["attribute"],
                attr["relation"]
            )

            if key not in seen:

                seen.add(key)

                refined.append(attr)

        return refined

    def _remove_duplicate_relations(
        self,
        relations: list
    ) -> list:
        """
        Relation 중복 제거
        """

        seen = set()

        refined = []

        for rel in relations:

            key = (
                rel["subject"],
                rel["predicate"],
                rel["object"]
            )

            if key not in seen:

                seen.add(key)

                refined.append(rel)

        return refined

    def _filter_invalid_relations(
        self,
        relations: list
    ) -> list:
        """
        허용되지 않은 relation 제거
        """

        refined = []

        for rel in relations:

            if (
                rel["predicate"]
                in self.ALLOWED_RELATIONS
            ):
                refined.append(rel)

        return refined

    def _remove_invalid_self_relations(
        self,
        relations: list
    ) -> list:
        """
        자기 자신 relation 제거
        """

        refined = []

        for rel in relations:

            if rel["subject"] != rel["object"]:
                refined.append(rel)

        return refined

    def _normalize_attribute_relations(
        self,
        attributes: list
    ) -> list:
        """
        Attribute relation 정규화

        attribute 단계에서는
        hasProperty만 사용하도록 통일
        """

        refined = []

        for attr in attributes:

            attr["relation"] = "hasProperty"

            refined.append(attr)

        return refined
    
    def _remove_bidirectional_relations(
        self,
        hierarchies: list,
        relations: list
    ) -> list:
        """
        hierarchy와 의미적으로 중복되는
        includes relation 제거

        예:
        LifeInsurance subClassOf InsuranceProduct
        가 존재하면

        InsuranceProduct includes LifeInsurance
        제거
        """

        hierarchy_pairs = set()

        for h in hierarchies:

            hierarchy_pairs.add((
                h["parent"],
                h["child"]
            ))

        refined = []

        for rel in relations:

            # includes relation만 검사
            if rel["predicate"] == "includes":

                pair = (
                    rel["subject"],
                    rel["object"]
                )

                # hierarchy와 중복되면 제거
                if pair in hierarchy_pairs:
                    continue

            refined.append(rel)

        return refined
    
    def _remove_disconnected_nodes(
        self,
        hierarchies: list,
        attributes: list,
        relations: list
    ):
        """
        중심 ontology graph와 연결되지 않은
        disconnected node 제거
        """

        connected_nodes = set()

        # hierarchy 연결 노드
        for h in hierarchies:

            connected_nodes.add(h["parent"])
            connected_nodes.add(h["child"])

        # semantic relation 연결 노드
        for rel in relations:

            connected_nodes.add(rel["subject"])
            connected_nodes.add(rel["object"])

        # 연결된 attribute만 유지
        refined_attributes = []

        for attr in attributes:

            if attr["class"] in connected_nodes:
                refined_attributes.append(attr)

        return refined_attributes

    def _build_llm_prompt(
        self,
        core_classes: list,
        hierarchies: list,
        attributes: list,
        relations: list
    ) -> str:
        """
        LLM Refinement Prompt 생성
        """

        class_text = "\n".join([
            f"- {c}"
            for c in core_classes
        ])

        hierarchy_text = "\n".join([
            (
                f"- {h['child']} "
                f"{h['relation']} "
                f"{h['parent']}"
            )
            for h in hierarchies
        ])

        attribute_text = "\n".join([
            (
                f"- {a['class']} "
                f"{a['relation']} "
                f"{a['attribute']}"
            )
            for a in attributes
        ])

        relation_text = "\n".join([
            (
                f"- {r['subject']} "
                f"{r['predicate']} "
                f"{r['object']}"
            )
            for r in relations
        ])

        allowed_relation_text = "\n".join([
            f"- {r}"
            for r in self.ALLOWED_RELATIONS
        ])

        prompt = f"""
당신은 Enterprise Knowledge Graph 및 Ontology Refinement 전문가입니다.

현재 생성된 Ontology 및 Knowledge Graph를 검토하고
정제(refinement)하세요.

--------------------------------------------------
[목표]
--------------------------------------------------

- 중복 제거
- 잘못된 relation 제거
- semantic consistency 유지
- disconnected ontology 최소화
- ontology graph 품질 개선
- Enterprise Knowledge Graph 구조 개선
- semantic connectivity 강화
- 한국어로 작성된 부분 전체 영어로 변경

--------------------------------------------------
[허용 Relation]
--------------------------------------------------

{allowed_relation_text}

--------------------------------------------------
[핵심 Refinement 원칙]
--------------------------------------------------

- 새로운 Class 생성 금지
- 새로운 Relation 생성 금지
- 허용 relation 외 사용 금지
- ontology semantic consistency 유지
- hierarchy 구조 유지
- event/action relation 제거
- semantic relation 중심 구조 유지
- disconnected graph 최소화
- isolated node 최소화

--------------------------------------------------
[가장 중요한 규칙]
--------------------------------------------------

Ontology graph는 가능한 하나의 connected graph로 유지하세요.

Class들이 서로 분리된 작은 graph로 존재하지 않도록 하세요.

가능한 경우 중심 business entity를 기준으로
다른 ontology cluster들을 연결하세요.

--------------------------------------------------
[Enterprise Knowledge Graph 방향]
--------------------------------------------------

좋은 방향:

- Employee belongsTo Department
- Project includes Document
- Customer subscribesTo Service
- SoftwareSystem requires Database
- Manager manages Employee
- Contract belongsTo Customer

나쁜 방향:

- loginCompleted
- notificationTriggered
- requestProcessed
- temporaryStatusChanged
- eventFinished

--------------------------------------------------
[Hierarchy Refinement 기준]
--------------------------------------------------

subClassOf는 반드시:

- is-a
- type-of
- inheritance

관계일 때만 유지하세요.

다음 관계는 subClassOf가 아닙니다:

- includes
- requires
- belongsTo
- manages
- workflow relation
- document relation
- system interaction

--------------------------------------------------
[Relation Refinement 기준]
--------------------------------------------------

Semantic relation은 다음 기준을 만족해야 합니다.

- business ownership
- organizational relationship
- dependency relationship
- inclusion relationship
- document reference relationship
- system interaction relationship
- service dependency relationship

--------------------------------------------------
[Attribute Refinement 기준]
--------------------------------------------------

Attribute는 반드시:

- Entity의 지속적인 속성(property)
- stable characteristic
- ontology property

여야 합니다.

다음은 제거하세요:

- event
- workflow
- temporary action
- status transition
- process execution

--------------------------------------------------
[현재 Core Classes]
--------------------------------------------------

{class_text}

--------------------------------------------------
[현재 Hierarchies]
--------------------------------------------------

{hierarchy_text}

--------------------------------------------------
[현재 Attributes]
--------------------------------------------------

{attribute_text}

--------------------------------------------------
[현재 Relations]
--------------------------------------------------

{relation_text}

--------------------------------------------------
[출력 형식]
--------------------------------------------------

반드시 아래 JSON 형식을 정확히 따르세요.

{{
  "refined_hierarchies": [
    {{
      "parent": "",
      "child": "",
      "relation": "subClassOf"
    }}
  ],

  "refined_attributes": [
    {{
      "class": "",
      "attribute": "",
      "relation": "hasProperty"
    }}
  ],

  "refined_relations": [
    {{
      "subject": "",
      "predicate": "",
      "object": ""
    }}
  ]
}}

설명 금지.
마크다운 금지.
```json 금지.
"""

        return prompt

    def refine(
        self,
        core_classes: list,
        hierarchies: list,
        attributes: list,
        relations: list
    ) -> dict:
        """
        Ontology 정제 수행

        Args:
            core_classes (list):
                ontology class 목록

            hierarchies (list):
                hierarchy 정보

            attributes (list):
                attribute 정보

            relations (list):
                semantic relation 정보

        Returns:
            dict:
                refined ontology result
        """

        # -------------------------
        # RULE-BASED REFINEMENT
        # -------------------------

        refined_hierarchies = (
            self._remove_duplicate_hierarchies(
                hierarchies
            )
        )

        refined_attributes = (
            self._remove_duplicate_attributes(
                attributes
            )
        )

        refined_relations = (
            self._remove_duplicate_relations(
                relations
            )
        )

        refined_relations = (
            self._filter_invalid_relations(
                refined_relations
            )
        )

        refined_relations = (
            self._remove_invalid_self_relations(
                refined_relations
            )
        )

        refined_attributes = (
            self._normalize_attribute_relations(
                refined_attributes
            )
        )

        refined_relations = (
            self._remove_invalid_self_relations(
                refined_relations
            )
        )

        refined_relations = (
            self._remove_bidirectional_relations(
                refined_hierarchies,
                refined_relations
            )
        )

        refined_relations = (
            self._remove_bidirectional_relations(
                refined_hierarchies,
                refined_relations
            )
        )

        refined_attributes = (
            self._remove_disconnected_nodes(
                refined_hierarchies,
                refined_attributes,
                refined_relations
            )
        )

        # -------------------------
        # LLM REFINEMENT
        # -------------------------

        prompt = self._build_llm_prompt(
            core_classes=core_classes,
            hierarchies=refined_hierarchies,
            attributes=refined_attributes,
            relations=refined_relations
        )

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an ontology refinement expert."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            response_format={
                "type": "json_object"
            }
        )

        result = response.choices[0].message.content

        return self._extract_json(result)
    
