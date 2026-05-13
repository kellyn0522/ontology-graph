import json
import re

from app.configs.settings import OPENAI_API_KEY, LLM_MODEL
from openai import OpenAI


class ClassExtractor:

    def __init__(self):

        self.client = OpenAI(
            api_key=OPENAI_API_KEY
        )

    def extract_json(self, text: str) -> dict:
        """
        LLM 응답에서 JSON 부분만 추출
        """

        text = text.strip()

        # ```json 제거
        text = re.sub(r"^```json", "", text)
        text = re.sub(r"^```", "", text)
        text = re.sub(r"```$", "", text)

        text = text.strip()

        match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            raise ValueError("JSON object not found")

        return json.loads(match.group(0))

    def extract(self, text: str) -> dict:
        """
        문서에서 핵심 Ontology Class를 추출합니다.

        Args:
            text (str):
                PDF에서 추출된 전체 텍스트

        Returns:
            dict:
                {
                    "core_classes": [...]
                }
        """

        prompt = f"""
당신은 Enterprise Knowledge Graph 및 Ontology 설계 전문가입니다.

아래 문서를 기반으로
문서의 Enterprise Ontology Schema를 구성하는
핵심 상위 Concept 및 Ontology Class를 추출하세요.

[목표]

- 문서의 재사용 가능한 상위 Ontology Concept와 Class을 추출하세요.
- 조직, 시스템, 문서, 프로젝트, 사용자, 부서, 제품, 서비스 등 실제 비즈니스 구조의 중심 개념을 우선적으로 추출하세요.
- Enterprise Knowledge Graph 구축에 적합한 상위 개념 중심으로 생성하세요.

[중요 규칙]

- **반드시 영어**로 생성하세요.
- PascalCase 형식으로 생성하세요.

예시:
- Employee
- Department
- Project
- Document
- ManagementSystem
- Product
- Service
- DatabaseServer

[제외 대상]

아래와 같은 low-level concept는 제외하세요.

- temporary event
- date
- time
- status
- simple action
- message
- notification
- log
- approval document
- technical report
- operational report
- temporary contract
- detailed artifact
- workflow status
- response
- update event
- request history

[추출 기준]

좋은 Ontology Class 예시:
- Company
- Department
- Employee
- Customer
- Product
- Project
- System
- Database
- Document
- Service

나쁜 예시:
- employee login event
- update request
- notification sent
- temporary status
- completed action
- event trigger

[매우 중요]

- 반드시 Enterprise Knowledge Graph의 중심이 되는 개념만 추출하세요.
- 유사 의미는 하나로 통합하세요.
- isolated node가 생기지 않도록 서로 연결 가능한 핵심 개념 중심으로 생성하세요.
- 단순 이벤트보다 "지속적으로 존재하는 개체(entity)"를 우선하세요.
- 행동(action)보다 "주체(entity)"를 우선하세요.
- 최소 5개 이상의 핵심 class를 생성하세요.
- 너무 세부적인 개념은 제외하세요.
- 개별 업무 객체(instance-level concept)보다 재사용 가능한 schema-level class를 우선 생성하세요.
- 모든 Class는 동일한 abstraction level을 유지하세요.
- 세부 문서명, 이벤트, 로그, 리포트, 승인 객체 등은 제외하세요.

[Ontology 설계 방향]

좋은 방향:
- Employee belongsTo Department
- Project uses Document
- Customer purchases Product
- Contract references Regulation

나쁜 방향:
- login completed
- request approved
- event triggered
- status updated

반드시 아래 JSON 형식으로만 반환하세요.

{{
  "core_classes": []
}}

설명 금지.
마크다운 금지.
```json 금지.

문서:
{text}
"""

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an ontology class extraction expert."
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
    
