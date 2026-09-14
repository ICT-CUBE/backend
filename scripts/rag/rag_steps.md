# 제니 RAG 구현 단계

## 1. 확정한 구성

- 원본 문서: `scripts/rag/jennie_text.md`
- 벡터 데이터베이스: ChromaDB
- Chroma 컬렉션: `jenny_knowledge`
- 임베딩 제공자: OpenAI
- 임베딩 모델: `text-embedding-3-small`
- 답변 생성 모델: `OPENAI_MODEL` 환경변수에 설정된 모델

임베딩 모델은 애플리케이션에서 호출한다. Chroma는 생성된 벡터와 원문 청크,
메타데이터를 저장하고 유사도 검색을 수행한다.

## 2. 환경변수

다음 설정을 사용한다.

```env
OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

CHROMA_HOST=chroma
CHROMA_PORT=8000
CHROMA_SSL_ENABLED=false
CHROMA_COLLECTION_NAME=jenny_knowledge
```

Docker Compose 내부의 API는 `chroma:8000`으로 접속한다. 호스트에서 직접
Python 스크립트를 실행할 경우에는 `localhost:8001`을 사용한다.

## 3. 문서 적재

별도의 적재 스크립트에서 다음 순서로 처리한다.

1. `jennie_text.md`를 UTF-8로 읽는다.
2. `[기본 정보]`, `[성격 및 평소 모습]` 같은 제목을 기준으로 문서를 나눈다.
3. 너무 긴 섹션만 문단 단위로 추가 분할한다.
4. 각 청크에 재실행해도 동일하게 만들어지는 고정 ID를 부여한다.
5. OpenAI Embeddings API에 청크들을 배치로 전달한다.
6. 반환된 임베딩과 원문, 메타데이터를 Chroma에 `upsert`한다.

임베딩 생성 예시:

```python
from openai import OpenAI

client = OpenAI()
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=chunks,
)
embeddings = [item.embedding for item in response.data]
```

Chroma에는 다음 정보를 함께 저장한다.

```python
collection.upsert(
    ids=chunk_ids,
    documents=chunks,
    embeddings=embeddings,
    metadatas=[
        {
            "source": "jennie_text.md",
            "section": section_name,
            "version": 1,
        }
        for section_name in section_names
    ],
)
```

적재는 API 서버가 시작될 때마다 실행하지 않는다. 문서가 변경됐을 때 관리자가
적재 스크립트를 명시적으로 실행한다.

## 4. 질문 검색

대화 요청을 받으면 다음 순서로 처리한다.

1. 사용자 질문을 `text-embedding-3-small`로 임베딩한다.
2. `jenny_knowledge` 컬렉션에서 유사한 청크를 검색한다.
3. 우선 `Top-K=4`로 시작하고 검색 품질을 평가해 조정한다.
4. 검색된 청크를 출처 컨텍스트로 답변 생성 프롬프트에 전달한다.
5. 관련 자료가 부족하면 모르는 내용을 만들어내지 않도록 프롬프트에서 제한한다.

```text
사용자 질문
  -> OpenAI 질문 임베딩
  -> Chroma 유사도 검색
  -> 검색된 제니 정보 + 최근 대화
  -> 답변 생성 모델
  -> 최종 응답
```

## 5. 재색인 규칙

- 문서 적재와 질문 검색에는 반드시 동일한 임베딩 모델을 사용한다.
- 임베딩 모델이나 출력 차원을 변경하면 기존 컬렉션을 그대로 사용하지 않고
  새 컬렉션을 만들어 전체 문서를 재색인한다.
- `jennie_text.md`를 원본 데이터로 유지한다. Chroma 볼륨이 삭제돼도 원본에서
  다시 색인할 수 있어야 한다.
- `docker compose down -v`를 실행하면 `chroma-data` 볼륨도 삭제될 수 있으므로
  주의한다.
- `OPENAI_API_KEY`는 실제 `.env` 또는 Azure 환경변수로만 관리하고 Git에 올리지
  않는다.

## 6. 다음 구현 작업

- [ ] `OPENAI_EMBEDDING_MODEL` 설정을 `Settings`에 추가
- [ ] Chroma HTTP 클라이언트 모듈 작성
- [ ] Markdown 분할 및 적재 스크립트 작성
- [ ] 적재 스크립트 테스트 작성
- [ ] 대화 서비스에 검색 단계 연결
- [ ] 대표 질문 세트로 검색 결과 평가

## 참고 문서

- [OpenAI text-embedding-3-small](https://developers.openai.com/api/docs/models/text-embedding-3-small)
- [OpenAI Embeddings API](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create)
- [Chroma embedding functions](https://docs.trychroma.com/docs/embeddings/embedding-functions)
