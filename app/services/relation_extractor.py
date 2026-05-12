import json
import re

from app.configs.settings import OPENAI_API_KEY, LLM_MODEL
from openai import OpenAI


class RelationExtractor:

    ALLOWED_RELATIONS = [
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

--------------------------------------------------
[목표]
--------------------------------------------------

- Ontology Class 간 Semantic Relation 생성
- Enterprise Knowledge Graph 생성
- 조직, 시스템, 프로젝트, 문서, 사용자, 제품, 서비스 간
  실제 비즈니스 관계를 중심으로 생성
- disconnected ontology graph 방지
- semantic connectivity 강화

--------------------------------------------------
[매우 중요]
--------------------------------------------------

허용된 Relation만 사용하세요.

[허용 Relation]

{relation_text}

--------------------------------------------------
[핵심 Knowledge Graph 원칙]
--------------------------------------------------

- 반드시 영어로 생성하세요.
- Subject/Object는 반드시 기존 Class만 사용하세요.
- 새로운 Class 생성 금지
- 새로운 Relation 생성 금지
- 허용 relation 외 사용 금지
- Event/action/status relation 금지
- semantic 중심 구조 유지
- disconnected graph 생성 금지
- isolated node를 최소화하세요.

--------------------------------------------------
[가장 중요한 규칙]
--------------------------------------------------

Knowledge Graph는 가능한 하나의 connected graph로 생성하세요.

Class들이 서로 분리된 작은 graph로 존재하지 않도록 하세요.

가능한 경우 중심 business entity를 기준으로
다른 ontology cluster들을 연결하세요.

각 Class는 가능하면 최소 1개 이상의 semantic relation을 가지도록 하세요.

--------------------------------------------------
[Enterprise 중심 Entity 예시]
--------------------------------------------------

아래와 같은 Entity는 중심 ontology entity가 될 수 있습니다.

- Employee
- Department
- Project
- Customer
- Product
- Document
- Contract
- SoftwareSystem
- Database
- Service

다른 class들은 가능한 경우
위 중심 entity와 semantic relation을 가져야 합니다.

--------------------------------------------------
[Relation 생성 기준]
--------------------------------------------------

Semantic relation은 다음 기준으로 생성하세요.

- business ownership
- organizational relationship
- dependency relationship
- inclusion relationship
- document reference relationship
- system interaction relationship
- project collaboration relationship
- service dependency relationship

--------------------------------------------------
[좋은 예시]
--------------------------------------------------

Employee
    belongsTo
Department

Project
    includes
Document

Customer
    subscribesTo
Service

SoftwareSystem
    requires
Database

Manager
    manages
Employee

Contract
    belongsTo
Customer

Document
    requires
ApprovalProcess

Service
    includes
Product

--------------------------------------------------
[절대 생성하면 안되는 예시]
--------------------------------------------------

Employee
    after
Meeting

Notification
    completed
Request

Document
    triggered
Workflow

Customer
    worksAt
Laptop

Database
    subClassOf
SoftwareSystem

--------------------------------------------------
[중요한 추가 규칙]
--------------------------------------------------

- hierarchy(subClassOf) 관계를 다시 relation으로 생성하지 마세요.
- attribute(hasProperty) 관계를 relation으로 생성하지 마세요.
- local relation만 만들지 말고,
  ontology 전체 graph 구조를 고려하세요.
- semantic relation 중심으로 graph를 구성하세요.
- hierarchy보다 entity interaction을 우선하세요.
- 단순 event relation보다 지속적인 business relation을 우선하세요.
- workflow/event 중심 graph를 만들지 마세요.

--------------------------------------------------
[현재 Ontology Class]
--------------------------------------------------

{class_text}

--------------------------------------------------
[현재 Hierarchy]
--------------------------------------------------

{hierarchy_text}

--------------------------------------------------
[현재 Attribute]
--------------------------------------------------

{attribute_text}

--------------------------------------------------
[출력 형식]
--------------------------------------------------

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

--------------------------------------------------
[원본 문서]
--------------------------------------------------

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