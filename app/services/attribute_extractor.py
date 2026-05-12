import json
import re

from app.configs.settings import OPENAI_API_KEY, LLM_MODEL
from openai import OpenAI


class AttributeExtractor:

    ALLOWED_RELATIONS = [
        "hasProperty",
        "belongsTo",
        "includes",
        "requires"
    ]

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

    def extract(
        self,
        text: str,
        core_classes: list,
        hierarchies: list
    ) -> dict:
        """
        Ontology Attribute 및 Property Relation 추출

        Args:
            text (str):
                원본 문서 텍스트

            core_classes (list):
                추출된 ontology class 목록

            hierarchies (list):
                생성된 hierarchy 정보

        Returns:
            dict:
                {
                    "attributes": [
                        {
                            "class": "",
                            "attribute": "",
                            "relation": "hasProperty"
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

        allowed_relation_text = "\n".join([
            f"- {r}"
            for r in self.ALLOWED_RELATIONS
        ])

        prompt = f"""
당신은 Enterprise Ontology 및 Knowledge Graph Property 설계 전문가입니다.

아래 Ontology Class와 Hierarchy를 기반으로
각 Class의 핵심 Attribute(Property)를 추출하세요.

[목표]

- 각 Class가 가지는 핵심 Property(Attribute)를 추출하세요.
- Attribute는 해당 Class의 지속적인 속성(Property)이어야 합니다.
- Enterprise Knowledge Graph 구조 기반으로 생성하세요.
- 조직, 시스템, 프로젝트, 문서, 사용자, 제품 등
  실제 비즈니스 Entity의 속성을 중심으로 생성하세요.

[매우 중요]

허용된 Relation만 사용하세요.

[허용 Relation]

{allowed_relation_text}

--------------------------------------------------
[핵심 규칙]
--------------------------------------------------

- 반드시 영어로 생성하세요.
- Attribute는 camelCase 형식으로 생성하세요.
- Relation은 반드시 허용된 relation 중 하나만 사용하세요.
- 새로운 Core Class 생성 금지
- Event/action/status 형태 금지
- 너무 low-level attribute 금지
- disconnected ontology를 만들지 마세요.
- 가능한 실제 비즈니스 Entity의 핵심 속성만 생성하세요.
- 행동(action)보다 "지속적인 속성(property)"을 우선하세요.

--------------------------------------------------
[좋은 예시]
--------------------------------------------------

Employee
 ├── employeeId
 ├── employeeName
 ├── emailAddress

Project
 ├── projectName
 ├── startDate
 ├── projectStatus

Document
 ├── documentTitle
 ├── documentType
 ├── createdDate

Customer
 ├── customerName
 ├── customerEmail
 ├── customerAddress

SoftwareSystem
 ├── systemName
 ├── versionNumber
 ├── serverLocation

--------------------------------------------------
[잘못된 예시]
--------------------------------------------------

Employee
 ├── loginCompleted
 ├── taskApproved
 ├── requestProcessed

Project
 ├── projectStartedYesterday
 ├── taskFinished

Document
 ├── documentUploadedNow
 ├── approvalTriggered

--------------------------------------------------
[주의]
--------------------------------------------------

- Attribute는 행동(action)이 아닙니다.
- Attribute는 상태 변화(status transition)가 아닙니다.
- Attribute는 이벤트(event)가 아닙니다.
- Attribute는 Entity의 지속적인 특성이어야 합니다.
- workflow/process/event 구조를 만들지 마세요.
- ontology property 형태로 생성하세요.

--------------------------------------------------
[Ontology 설계 방향]
--------------------------------------------------

좋은 방향:
- Employee hasProperty employeeId
- Project hasProperty startDate
- Customer hasProperty customerEmail
- Document hasProperty documentTitle

나쁜 방향:
- Employee completedTask
- Project triggeredWorkflow
- Document uploadedYesterday

--------------------------------------------------
[현재 Ontology Class]
--------------------------------------------------

{class_text}

--------------------------------------------------
[현재 Hierarchy]
--------------------------------------------------

{hierarchy_text}

반드시 아래 JSON 형식으로만 반환하세요.

{{
  "attributes": [
    {{
      "class": "",
      "attribute": "",
      "relation": ""
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
                        "You are an ontology attribute extraction expert."
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