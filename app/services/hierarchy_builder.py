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
당신은 Enterprise Ontology 및 Knowledge Graph Hierarchy 설계 전문가입니다.

아래 Class 목록을 기반으로
Ontology 계층 구조(Hierarchy)를 생성하세요.

[목표]

- Parent Class
- Child Class
- subClassOf 관계

를 생성하세요.

Ontology Hierarchy는 반드시:

"A is a type of B"

관계일 때만 생성하세요.

즉:

- Manager는 Employee의 한 종류이다.
- TechnicalDocument는 Document의 한 종류이다.
- InternalSystem은 SoftwareSystem의 한 종류이다.

와 같은 inheritance 관계만 허용됩니다.

--------------------------------------------------
[매우 중요: subClassOf 정의]
--------------------------------------------------

subClassOf는 반드시:

- is-a
- type-of
- inheritance

관계일 때만 사용하세요.

아래 관계는 subClassOf가 아닙니다:

- part-of 관계
- includes 관계
- requires 관계
- uses 관계
- stores 관계
- manages 관계
- workflow relation
- business relation
- event relation
- process relation

--------------------------------------------------
[절대 생성하면 안되는 잘못된 예시]
--------------------------------------------------

Document
    subClassOf
Project

Employee
    subClassOf
Department

Database
    subClassOf
Server

Invoice
    subClassOf
Customer

위 예시는 "한 종류(type-of)" 관계가 아니므로 잘못된 Ontology입니다.

--------------------------------------------------
[좋은 예시]
--------------------------------------------------

Employee
 ├── Manager
 ├── Engineer
 ├── Analyst
 └── Consultant

Document
 ├── ContractDocument
 ├── TechnicalDocument
 ├── ReportDocument
 └── PolicyDocument

SoftwareSystem
 ├── ManagementSystem
 ├── DatabaseSystem
 ├── MonitoringSystem
 └── AuthenticationSystem

Project
 ├── InternalProject
 ├── ClientProject
 └── ResearchProject

--------------------------------------------------
[중요 규칙]
--------------------------------------------------

- 반드시 기존 Class만 사용하세요.
- 새로운 Class 생성 금지
- Parent와 Child는 반드시 제공된 목록 안에 존재해야 합니다.
- Relation은 반드시 "subClassOf"만 사용하세요.
- disconnected hierarchy를 최소화하세요.
- Enterprise Knowledge Graph 구조를 고려하세요.
- Child는 반드시 Parent의 한 종류(type)여야 합니다.
- 하나의 Child는 가능한 하나의 Parent만 가지도록 하세요.
- semantic inheritance 관계만 생성하세요.
- relation/explanation/event/property 구조를 hierarchy로 만들지 마세요.
- hierarchy보다 semantic correctness를 우선하세요.

--------------------------------------------------
[Hierarchy 생성 기준]
--------------------------------------------------

다음 질문에 YES일 때만 subClassOf를 생성하세요.

"Child는 Parent의 한 종류인가?"

YES 예시:
- Engineer → Employee
- TechnicalDocument → Document
- DatabaseSystem → SoftwareSystem

NO 예시:
- Employee → Department
- Project → Document
- Customer → Invoice
- Document → Server

--------------------------------------------------
[출력 형식]
--------------------------------------------------

반드시 아래 JSON 형식으로만 반환하세요.

{{
  "hierarchies": [
    {{
      "parent": "",
      "child": "",
      "relation": "subClassOf"
    }}
  ]
}}

설명 금지.
마크다운 금지.
```json 금지.

--------------------------------------------------
[Class 목록]
--------------------------------------------------

{class_text}

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