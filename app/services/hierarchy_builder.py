# Ontology Tree 구조 생성
# 누가 부모고 자식인지

import json
import re

from app.configs.settings import OPENAI_API_KEY, LLM_MODEL
from openai import OpenAI


class HierarchyBuilder:

    def __init__(self):

        self.client = OpenAI(
            api_key=OPENAI_API_KEY
        )

    def extract_json(self, text: str) -> dict:
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

    def build(
        self,
        text: str,
        core_classes: list
    ) -> dict:
        """
        Core Class 기반 Ontology Hierarchy 생성

        Args:
            text (str):
                원본 문서 텍스트

            core_classes (list):
                추출된 핵심 ontology class 목록

        Returns:
            dict:
                {
                    "hierarchies": [
                        {
                            "parent": "",
                            "child": "",
                            "relation": "subClassOf"
                        }
                    ]
                }
        """

        class_text = "\n".join([
            f"- {c}" for c in core_classes
        ])

        prompt = f"""
당신은 Enterprise Knowledge Graph 및 Organizational Ontology 설계 전문가입니다.

아래 Class 목록을 기반으로
Enterprise Ontology Structure를 생성하세요.

==================================================
[목표]
==================================================

Class 간의 구조적 관계(structural hierarchy)와
Ontology Hierarchy를 생성하세요.

반드시 아래 두 종류의 관계만 생성하세요.

1. subClassOf
   - taxonomy
   - is-a
   - type-of
   - inheritance 관계

2. hasComponent
   - organizational structure
   - part-of
   - structural containment 관계

==================================================
[관계 정의]
==================================================

--------------------------------------------------
1. subClassOf
--------------------------------------------------

반드시 아래 관계일 때만 사용하세요.

- is-a
- type-of
- inheritance

예시:
- TechnicalDocument → Document
- MonitoringSystem → System
- HealthInsurance → InsuranceProduct
- Manager → Employee

즉:

"Child는 Parent의 한 종류인가?"

YES일 때만 사용하세요.

--------------------------------------------------
2. hasComponent
--------------------------------------------------

조직 구조 및 구성 관계일 때 사용하세요.

예시:
- Company hasComponent Department
- Department hasComponent Team
- Team hasComponent Employee
- Project hasComponent Document

즉:

"Parent가 Child를 구조적으로 포함하는가?"

YES일 때만 사용하세요.

==================================================
[매우 중요]
==================================================

subClassOf와 hasComponent를 절대 혼동하지 마세요.

--------------------------------------------------
subClassOf 예시
--------------------------------------------------

Document
 ├── TechnicalDocument
 ├── ContractDocument
 └── ReportDocument

Employee
 ├── Manager
 ├── Engineer
 └── Analyst

--------------------------------------------------
hasComponent 예시
--------------------------------------------------

Company
 ├── Department
 │    ├── Team
 │    └── Employee

Project
 ├── Document
 └── Database

==================================================
[절대 잘못 생성하면 안되는 예시]
==================================================

Department
    subClassOf
Company

Employee
    subClassOf
Department

Project
    subClassOf
Document

Database
    subClassOf
System

위 관계는 inheritance가 아니므로 잘못된 hierarchy입니다.

--------------------------------------------------
또한 아래 관계도 금지입니다.
--------------------------------------------------

- manages
- uses
- requires
- stores
- subscribesTo
- references
- belongsTo
- workflow relation
- event relation
- process relation

==================================================
[좋은 예시]
==================================================

Company
    hasComponent
Department

Department
    hasComponent
Employee

Department
    hasComponent
Project

Project
    hasComponent
Document

Document
    subClassOf
TechnicalDocument

System
    subClassOf
MonitoringSystem

Employee
    subClassOf
Manager

==================================================
[중요 규칙]
==================================================

- 반드시 제공된 Class만 사용하세요.
- 새로운 Class 생성 금지
- Parent와 Child는 반드시 목록 안에 존재해야 합니다.
- Relation은 반드시:
    - subClassOf
    - hasComponent
  둘 중 하나만 사용하세요.
- semantic correctness를 relation 개수보다 우선하세요.
- 적절한 relation이 없으면 생성하지 않아도 됩니다.
- 억지 relation 생성 금지
- disconnected graph 허용
- 동일한 node pair에 여러 relation 생성 금지
- semantic relation(manages, uses 등)은 생성하지 마세요.
- hierarchy와 business workflow를 혼동하지 마세요.
- ontology 구조의 일관성을 유지하세요.
- 하나의 Child는 가능한 하나의 Parent만 가지도록 하세요.

==================================================
[출력 형식]
==================================================

반드시 아래 JSON 형식으로만 반환하세요.

{{
  "hierarchies": [
    {{
      "parent": "",
      "child": "",
      "relation": ""
    }}
  ]
}}

relation은 반드시:
- subClassOf
- hasComponent

둘 중 하나만 사용하세요.

설명 금지.
마크다운 금지.
```json 금지.

==================================================
[Class 목록]
==================================================

{class_text}

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
                        "You are an ontology hierarchy construction expert."
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

        return self.extract_json(result)