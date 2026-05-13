import json
import re

from app.configs.settings import OPENAI_API_KEY, LLM_MODEL
from openai import OpenAI


class RelationExtractor:

    ALLOWED_RELATIONS = [
        "hasComponent",
        "manages",
        "uses",
        "requires"
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

    def extract(
        self,
        text: str,
        core_classes: list,
        hierarchies: list,
        attributes: list
    ) -> dict:
        """
        Ontology Class 간 Semantic Relation 추출

        Args:
            text (str):
                원본 문서 텍스트

            core_classes (list):
                ontology class 목록

            hierarchies (list):
                hierarchy 정보

            attributes (list):
                attribute 정보

        Returns:
            dict:
                {
                    "relations": [
                        {
                            "subject": "",
                            "predicate": "",
                            "object": ""
                        }
                    ]
                }
        """

        class_text = "\n".join([
            f"- {c}" for c in core_classes
        ])

        hierarchy_text = "\n".join([
            (
                f"- {h['child']} "
                f"subClassOf "
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
            f"- {r}"
            for r in self.ALLOWED_RELATIONS
        ])

        prompt = f"""
당신은 Enterprise Knowledge Graph 및 Ontology Relation 설계 전문가입니다.

아래 Ontology 정보를 기반으로
Class 간 Semantic Relation을 생성하세요.

==================================================
[목표]
==================================================

- Ontology Class 간 Semantic Relation 생성
- Enterprise Knowledge Graph 생성
- 조직, 시스템, 프로젝트, 문서 간의
  핵심 business relation만 생성
- semantic consistency 유지
- ontology readability 향상
- relation redundancy 최소화

==================================================
[매우 중요]
==================================================

허용된 Relation만 사용하세요.

[허용 Relation]

{relation_text}

==================================================
[핵심 Ontology 원칙]
==================================================

- 반드시 영어로 생성하세요.
- Subject/Object는 반드시 기존 Class만 사용하세요.
- 새로운 Class 생성 금지
- 새로운 Relation 생성 금지
- 허용 relation 외 사용 금지
- hierarchy(subClassOf) relation 생성 금지
- attribute(hasProperty) relation 생성 금지
- Event/action/status relation 금지
- semantic precision을 relation 개수보다 우선하세요.
- disconnected graph는 허용됩니다.
- graph 연결을 위해 억지 relation 생성 금지

==================================================
[가장 중요한 규칙]
==================================================

명확한 semantic relation이 존재하는 경우에만
relation을 생성하세요.

모든 Class를 억지로 연결하려고 하지 마세요.

Class들이 서로 연결되지 않아도 괜찮습니다.

--------------------------------------------------
동일한 node pair에 대해
여러 relation 생성 금지
--------------------------------------------------

잘못된 예시:
- Department manages Project
- Department hasComponent Project

둘 중 하나만 생성하세요.

--------------------------------------------------
semantic meaning이 중복되는 relation 생성 금지
--------------------------------------------------

예:
- belongsTo + includes
- manages + hasComponent

와 같이 의미가 겹치는 relation은
동시에 생성하지 마세요.

==================================================
[Relation 생성 기준]
==================================================

Semantic relation은 아래 경우에만 생성하세요.

- organizational management relationship
- system dependency relationship
- system usage relationship
- project-document relationship

==================================================
[권장 Relation 의미]
==================================================

- manages
    → 조직/관리 관계

- uses
    → 시스템 또는 프로젝트 사용 관계

- requires
    → 시스템/서비스 의존 관계

==================================================
[좋은 예시]
==================================================

Department
    manages
Employee

Department
    manages
Project

Project
    uses
Document

Project
    uses
Database

System
    requires
Database

Service
    requires
AuthenticationSystem

Manager
    manages
Employee

==================================================
[절대 생성하면 안되는 예시]
==================================================

Document
    requires
ApprovalDocument

Department
    requires
Customer

Employee
    belongsTo
Department

Customer
    subscribesTo
Service

Project
    includes
Database

Database
    subClassOf
System

Notification
    completed
Request

Document
    triggered
Workflow

==================================================
[중요한 추가 규칙]
==================================================

- hierarchy(subClassOf) 관계를 relation으로 다시 생성하지 마세요.
- attribute(hasProperty) 관계를 relation으로 생성하지 마세요.
- workflow/event 중심 relation 생성 금지
- graph connectivity보다 semantic correctness를 우선하세요.
- local relation만 만들지 말고 ontology 전체 의미를 고려하세요.
- semantic ambiguity가 큰 relation은 생성하지 마세요.
- relation direction(subject/object)을 신중히 결정하세요.
- inverse relation 중복 생성 금지
- relation 개수보다 semantic consistency를 우선하세요.

==================================================
[현재 Ontology Class]
==================================================

{class_text}

==================================================
[현재 Hierarchy]
==================================================

{hierarchy_text}

==================================================
[현재 Attribute]
==================================================

{attribute_text}

==================================================
[출력 형식]
==================================================

반드시 아래 JSON 형식으로만 반환하세요.

{{
  "relations": [
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

==================================================
[원본 문서]
==================================================

{text}
"""

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an ontology relation extraction expert."
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