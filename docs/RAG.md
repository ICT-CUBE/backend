# 제니 대화 RAG 구현 현황 및 계획

## 1. 목표

제니 관련 원본 텍스트를 임베딩해 ChromaDB에 저장하고, 사용자의 대화 요청과
관련성이 높은 정보를 검색해 기존 답변 생성 모델의 컨텍스트로 제공한다.

```text
사용자 질문
  -> OpenAI 질문 임베딩 생성
  -> ChromaDB에서 관련 청크 검색
  -> 검색 결과 + 최근 대화 + 시스템 지침 구성
  -> OpenAI 답변 생성 모델 호출
  -> 최종 응답 반환
```

ChromaDB는 답변을 생성하지 않는다. 임베딩 벡터, 원문 청크, 메타데이터를
보관하고 유사도 검색 결과를 반환하는 역할을 담당한다.

## 2. 확정한 기술 구성

| 구분 | 결정 |
|---|---|
| 원본 문서 | `scripts/rag/jennie_text.md` |
| 벡터 데이터베이스 | ChromaDB |
| Chroma 서버/클라이언트 버전 | `1.5.3` |
| 컬렉션 이름 | `jenny_knowledge` |
| 임베딩 제공자 | OpenAI |
| 임베딩 모델 | `text-embedding-3-small` |
| 답변 생성 모델 | `OPENAI_MODEL` 환경변수 값 |
| 로컬 Chroma 주소 | API 컨테이너 기준 `chroma:8000` |
| 호스트 공개 주소 | `localhost:8001` |
| 영속 저장소 | Docker named volume `chroma-data` |

`BAAI/bge-m3`도 검토했지만, 현재 데이터 규모와 Azure 배포 편의성을 고려해
별도 로컬 임베딩 모델을 운영하지 않고 OpenAI Embeddings API를 사용하기로
결정했다.

## 3. 현재까지 완료한 작업

### 3.1 원본 텍스트 준비

- [x] `scripts/rag/jennie_text.md`에 제니 기본 정보, 활동, 성격, 취향, 말투 예시
  등을 정리했다.
- [x] 원본 문서는 ChromaDB와 별도로 Git에서 관리한다.
- [x] Chroma 볼륨이 삭제되더라도 원본 문서에서 다시 색인할 수 있는 구조로
  정했다.

현재 파일명은 `jennie_text.md`, 컬렉션 이름은 `jenny_knowledge`다. 구현 시 이
이름들을 그대로 사용하되 ID와 메타데이터에서는 표기를 일관되게 유지한다.

### 3.2 로컬 Chroma 컨테이너 구성

- [x] `docker-compose.dev.yml`에 `chroma` 서비스를 추가했다.
- [x] `chromadb/chroma:1.5.3` 이미지를 고정해서 사용한다.
- [x] 호스트 포트 `8001`을 Chroma 컨테이너 포트 `8000`에 연결했다.
- [x] Chroma의 `/data`를 `chroma-data` 볼륨에 연결했다.
- [x] `/api/v2/heartbeat` 기반 health check를 추가했다.
- [x] Chroma가 healthy 상태가 된 뒤 API가 시작되도록 `depends_on`을 추가했다.

현재 연결 구조:

```text
호스트 PC               Docker Compose 네트워크
localhost:8001  ------>  chroma:8000
                            ^
                            |
                         api:8000
```

Chroma 이미지는 프로젝트에서 직접 빌드하지 않는다. Compose 실행 시 지정한
공식 이미지를 pull한다. API 이미지만 기존 `Dockerfile`로 빌드한다.

### 3.3 Python 의존성 추가

- [x] `requirements.txt`에 `chromadb==1.5.3`을 추가했다.
- [x] Chroma 서버 이미지와 Python 클라이언트의 버전을 맞췄다.
- [x] 기존 `openai==1.109.1` 패키지를 임베딩 생성에도 사용하기로 했다.

### 3.4 Chroma 접속 설정 추가

`app/core/config.py`의 `Settings`에 다음 설정을 추가했다.

```python
chroma_host: str = "localhost"
chroma_port: int = 8000
chroma_ssl_enabled: bool = False
chroma_collection_name: str = "jenny_knowledge"
```

`.env.example`의 로컬 Docker 예시는 다음과 같다.

```env
CHROMA_HOST=chroma
CHROMA_PORT=8000
CHROMA_SSL_ENABLED=false
CHROMA_COLLECTION_NAME=jenny_knowledge
```

Compose의 API 서비스는 `env_file: .env`를 사용한다. Compose 파일을
`Settings`가 직접 읽는 것이 아니라, Compose가 실제 `.env` 값을 API 컨테이너의
환경변수로 주입하고 Pydantic `Settings`가 그 환경변수를 읽는다.

현재 Compose에는 Chroma 설정을 중복 지정하는 `environment` 블록이 없다.
따라서 로컬 Docker 실행에 사용하는 실제 `.env`에도 위 네 값을 넣어야 한다.
`.env.example`은 예시 파일일 뿐 자동으로 로드되지 않는다.

### 3.5 임베딩 모델 결정

- [x] `text-embedding-3-small`을 문서와 질문의 임베딩 모델로 사용한다.
- [x] 문서 적재와 질문 검색에서 반드시 같은 모델을 사용한다.
- [x] 임베딩 모델 또는 출력 차원을 바꾸면 전체 문서를 새로 색인한다.

### 3.6 Chroma 클라이언트 모듈 작성

- [x] `app/core/chroma.py`에 설정 기반 `HttpClient` 생성 함수를 추가했다.
- [x] 프로세스에서 재사용할 수 있도록 클라이언트를 캐시한다.
- [x] `jenny_knowledge` 컬렉션 조회/생성 함수를 추가했다.
- [x] Chroma의 기본 임베딩 함수를 비활성화했다. OpenAI에서 생성한 임베딩을
  적재와 검색 시 명시적으로 전달한다.
- [x] heartbeat 확인 함수를 추가했다.
- [x] 설정 전달, 클라이언트 캐시, 컬렉션 생성, heartbeat 성공/실패 단위 테스트를
  작성했다.
- [ ] 실제 Chroma 컨테이너를 실행한 통합 연결 검증은 아직 하지 않았다.

### 3.7 원본 문서 청크 분할

- [x] `app/services/rag/chunking.py`에 대괄호 제목 기반 섹션 파서를 구현했다.
- [x] 짧은 섹션은 유지하고 긴 섹션만 문단, 줄, 문장, 단어 경계 순서로 나누는
  분할 로직을 구현했다.
- [x] 모든 청크에 섹션 제목을 포함한다.
- [x] 기본 최대 길이를 제목 포함 1,200자로 제한했다.
- [x] 원본명, 섹션명, 청크 순번, 내용 해시로 결정적 ID를 생성한다.
- [x] 원본, 섹션, 순번, 해시, 문서 버전, 임베딩 모델 메타데이터를 생성한다.
- [x] UTF-8 파일 로딩 함수와 입력값 검증을 구현했다.
- [x] 파싱, 길이 제한, 결정적 ID, 빈 문서, 실제 원본 검증 단위 테스트를 작성했다.
- [x] 실제 `jennie_text.md`에서 34개 섹션, 35개 고유 청크를 생성했으며 가장 긴
  청크가 1,098자인 것을 확인했다.
- [ ] 현재 실행 환경의 pytest 의존성/캐시 제약으로 테스트 파일의 pytest 통과는
  아직 확인하지 못했다.

## 4. 아직 구현되지 않은 부분

현재 Chroma 컨테이너와 설정만 준비된 상태다. 제니 텍스트는 아직 임베딩되지
않았으며 `chroma-data` 볼륨에도 제니 컬렉션 데이터가 적재되지 않았다.

- [ ] `OPENAI_EMBEDDING_MODEL` 환경설정 추가
- [ ] 실제 Chroma 컨테이너 대상 클라이언트 연결 검증
- [ ] 청크 분할 pytest 실행 확인
- [ ] OpenAI 임베딩 생성 로직 작성
- [ ] Chroma 컬렉션 생성 및 `upsert` 적재 스크립트 작성
- [ ] 적재 결과와 재실행 안전성 테스트
- [ ] 사용자 질문 임베딩과 Top-K 검색 로직 작성
- [ ] 기존 대화 응답 서비스에 검색 결과 연결
- [ ] RAG 프롬프트 및 답변 제한 규칙 작성
- [ ] 대표 질문 데이터셋으로 검색 품질 평가
- [ ] Azure용 Chroma 인프라와 영속 스토리지 구성
- [ ] 운영 환경 네트워크 접근 제한과 백업/복구 절차 구성

## 5. 앞으로의 구현 순서

### 단계 1. 임베딩 환경설정 추가

`Settings`, `.env.example`, `.env.production.example`에 다음 값을 추가한다.

```env
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

코드에 모델명을 여러 번 하드코딩하지 않고 문서 적재와 질문 검색이 같은 설정을
공유하게 한다.

완료 조건:

- `settings.openai_embedding_model`로 모델명에 접근할 수 있다.
- 환경변수가 없을 때 `text-embedding-3-small`이 기본값으로 사용된다.
- 설정 로딩 테스트가 통과한다.

### 단계 2. Chroma 클라이언트 모듈 작성 및 연결 검증

클라이언트 모듈과 단위 테스트 작성은 완료했다. 다음으로 실제 컨테이너에 대한
heartbeat와 컬렉션 생성 동작을 검증한다.

`chromadb.HttpClient` 또는 `chromadb.AsyncHttpClient`를 생성하는 코드를 공통
모듈로 분리한다.

```python
client = chromadb.HttpClient(
    host=settings.chroma_host,
    port=settings.chroma_port,
    ssl=settings.chroma_ssl_enabled,
)
collection = client.get_or_create_collection(
    name=settings.chroma_collection_name,
)
```

고려 사항:

- 적재 스크립트는 동기 `HttpClient`를 사용해도 된다.
- 대화 요청 경로에서는 이벤트 루프를 막지 않도록 `AsyncHttpClient` 사용을
  우선 검토한다.
- 연결 실패를 일반적인 500 오류로 숨기지 말고 로그에서 원인을 식별할 수 있게
  예외 경계를 정한다.

완료 조건:

- Chroma heartbeat를 코드에서 확인할 수 있다.
- 설정한 컬렉션을 생성하거나 기존 컬렉션을 가져올 수 있다.
- Chroma 장애 상황에 대한 테스트가 있다.

### 단계 3. 원본 문서 청크 분할 — 구현 완료, pytest 실행 대기

`jennie_text.md`는 `[기본 정보]`, `[성격 및 평소 모습]`, `[패션]` 같은 섹션
제목을 우선 경계로 사용한다. 고정 글자 수로 전체 문서를 무조건 자르지 않는다.

분할 규칙 초안:

1. 대괄호로 둘러싸인 제목을 섹션으로 인식한다.
2. 짧은 섹션은 제목과 본문을 하나의 청크로 유지한다.
3. 긴 섹션은 빈 줄 또는 문단을 기준으로 추가 분할한다.
4. 각 청크 앞에 섹션 제목을 포함해 검색 문맥을 보존한다.
5. 빈 청크와 공백만 있는 청크는 제거한다.

각 청크의 ID는 실행할 때마다 달라지는 UUID 대신 결정적인 값을 사용한다.

```text
jennie_text:{section_slug}:{chunk_index}:{content_hash}
```

권장 메타데이터:

```json
{
  "source": "jennie_text.md",
  "section": "성격 및 평소 모습",
  "chunk_index": 0,
  "content_hash": "...",
  "document_version": 1,
  "embedding_model": "text-embedding-3-small"
}
```

완료 조건:

- [x] 같은 원본을 두 번 분할했을 때 동일한 청크와 ID가 생성된다.
- [x] 제목이 각 청크에 보존된다.
- [x] 모든 청크가 설정한 최대 길이 이내다.
- [ ] `tests/test_rag_chunking.py`를 Docker API 컨테이너에서 실행해 통과를
  확인한다.

### 단계 4. 임베딩 및 Chroma 적재 스크립트 작성

별도 관리 스크립트에서 다음 순서로 실행한다.

1. 원본 문서를 읽고 청크를 만든다.
2. OpenAI Embeddings API에 청크들을 배치로 전달한다.
3. 응답 순서대로 임베딩과 청크를 연결한다.
4. `jenny_knowledge` 컬렉션에 ID, 임베딩, 원문, 메타데이터를 `upsert`한다.
5. 최종 적재 건수와 컬렉션 건수를 출력한다.

```python
from openai import OpenAI

openai_client = OpenAI(api_key=settings.openai_api_key)
response = openai_client.embeddings.create(
    model=settings.openai_embedding_model,
    input=chunks,
)
embeddings = [item.embedding for item in response.data]

collection.upsert(
    ids=chunk_ids,
    embeddings=embeddings,
    documents=chunks,
    metadatas=metadatas,
)
```

예정 실행 방식:

```powershell
docker compose -f docker-compose.dev.yml exec api `
  python scripts/rag/index_jennie.py
```

적재 스크립트는 API 서버 시작 시 자동으로 실행하지 않는다. 원본 문서가
변경되거나 컬렉션을 재생성해야 할 때 명시적으로 실행한다.

완료 조건:

- 최초 실행으로 컬렉션과 데이터가 생성된다.
- 동일 문서로 다시 실행해도 중복 데이터가 늘어나지 않는다.
- 일부 문서가 바뀌면 해당 ID가 안정적으로 갱신된다.
- API 키, Chroma 연결, OpenAI 호출 실패가 명확한 오류로 표시된다.

### 단계 5. 질문 검색 서비스 작성

사용자 질문을 문서 적재와 동일한 모델로 임베딩한 뒤 Chroma에서 검색한다.

초기 검색 설정:

```text
collection: jenny_knowledge
Top-K: 4
검색 방식: dense vector similarity
```

Top-K 4는 초기값이며 평가 결과에 따라 조정한다. 거리 임계값을 무조건 먼저
고정하기보다 실제 대표 질문의 관련/비관련 결과 분포를 확인한 뒤 결정한다.

완료 조건:

- 제니 정보와 관련된 질문에서 올바른 섹션이 검색된다.
- 무관한 질문에서 낮은 관련도의 문서를 강제로 사실처럼 사용하지 않는다.
- 검색 결과가 없거나 Chroma가 일시적으로 실패했을 때의 동작이 정의되어 있다.

### 단계 6. 기존 대화 응답에 RAG 연결

검색된 청크를 기존 대화 생성 요청의 참고 컨텍스트에 넣는다.

프롬프트 원칙:

- 검색 결과는 제니 관련 사실과 말투를 참고하기 위한 자료로 사용한다.
- 검색 문서에 없는 사실을 확정적으로 만들어내지 않는다.
- 원본 말투 예시는 스타일 참고용이며 매번 같은 문장을 복사하지 않는다.
- 시스템 지침, 최근 대화, 검색 컨텍스트, 사용자 질문의 역할을 명확히 분리한다.
- 검색된 텍스트 안의 문장을 시스템 명령으로 취급하지 않는다.

완료 조건:

- 대화 API 응답 전에 검색 단계가 실행된다.
- 검색된 제니 정보가 답변에 자연스럽게 반영된다.
- 기존 대화 기록 저장과 응답 형식이 깨지지 않는다.
- OpenAI 또는 Chroma 오류 처리 방식이 기존 API 정책과 일치한다.

### 단계 7. 테스트와 품질 평가

단위 테스트:

- Markdown 섹션 파싱
- 긴 섹션 분할
- 결정적 청크 ID 생성
- 빈 문서 처리
- 임베딩 응답과 청크 순서 매핑
- Chroma `upsert` 인자 검증
- 검색 결과 프롬프트 변환
- 외부 API 실패 처리

검색 평가 질문 예시:

- 제니 생일은 언제야?
- 제니가 좋아하는 계절은 뭐야?
- Ruby 앨범에 참여한 아티스트는 누구야?
- 평소 제니와 무대 위 제니는 어떻게 달라?
- 제니가 작업 후 몸과 마음을 리셋하는 방법은 뭐야?
- 제니는 어떤 음식을 가장 좋아해?  
  원본에 근거가 없다면 관련 없는 청크를 정답처럼 사용하지 않아야 한다.

평가 항목:

- 정답을 포함한 청크가 Top-K에 들어오는지
- 다른 섹션의 유사한 문장이 정답보다 먼저 나오는지
- 질문과 무관한 청크를 답변 모델이 사실로 사용하는지
- 말투 예시가 과도하게 복사되거나 반복되는지
- RAG 추가 전후 응답 지연 시간이 허용 범위인지

### 단계 8. Azure 운영 배포

로컬 기능과 검색 품질 검증이 끝난 후 진행한다.

- Chroma를 백엔드와 분리된 단일 서버로 배포한다.
- Chroma `/data`에 영속 스토리지를 연결한다.
- 단일 노드 Chroma를 여러 인스턴스가 같은 데이터 파일에 동시에 쓰도록
  구성하지 않는다.
- Chroma 엔드포인트를 공개 인터넷에 그대로 노출하지 않는다.
- 백엔드만 접근할 수 있도록 네트워크 또는 접근 제한을 구성한다.
- Azure 환경변수에 실제 Chroma 주소와 SSL 설정을 넣는다.
- 원본 문서와 적재 스크립트로 컬렉션을 복구할 수 있게 한다.
- 재색인, 백업, 장애 복구 절차를 문서화한다.

## 6. 로컬 실행 및 확인 명령

전체 서비스 빌드 및 실행:

```powershell
docker compose -f docker-compose.dev.yml up --build
```

Chroma 상태 확인:

```powershell
curl http://localhost:8001/api/v2/heartbeat
```

컨테이너 상태 확인:

```powershell
docker compose -f docker-compose.dev.yml ps
```

주의:

```powershell
docker compose -f docker-compose.dev.yml down -v
```

위 명령은 `chroma-data`를 포함한 named volume을 삭제할 수 있다. 재색인이 가능한
상태인지 확인하지 않고 실행하지 않는다.

## 7. 재색인 및 버전 관리 규칙

- 문서 적재와 질문 검색은 같은 `OPENAI_EMBEDDING_MODEL`을 사용한다.
- 임베딩 모델 또는 출력 차원이 바뀌면 기존 컬렉션에 혼합 저장하지 않는다.
- 모델 변경 시 새 컬렉션을 만들거나 기존 컬렉션을 비운 뒤 전체 재색인한다.
- 원본 문서 변경은 결정적 ID와 `upsert`로 반영한다.
- 원본에서 삭제된 청크가 컬렉션에도 삭제되도록 동기화 로직을 구현한다.
- 컬렉션 메타데이터 또는 별도 매니페스트에 문서 버전과 임베딩 모델을 기록한다.
- `OPENAI_API_KEY`는 실제 `.env` 또는 Azure 환경변수로만 관리하고 Git에 올리지
  않는다.

## 8. 전체 진행 체크리스트

- [x] RAG 아키텍처 방향 결정
- [x] ChromaDB 선택
- [x] 로컬 Chroma 컨테이너 추가
- [x] Chroma 영속 볼륨 추가
- [x] Chroma health check와 API 의존 관계 추가
- [x] `chromadb` Python 패키지 추가
- [x] Chroma 접속 설정 추가
- [x] 제니 원본 텍스트 준비
- [x] OpenAI `text-embedding-3-small` 선택
- [ ] OpenAI 임베딩 모델 설정 추가
- [x] Chroma 클라이언트 모듈 구현
- [ ] 실제 Chroma 연결 통합 검증
- [x] 문서 청크 분할 구현
- [ ] 청크 분할 단위 테스트 실행 확인
- [ ] 적재 스크립트 구현
- [ ] 제니 문서 실제 적재
- [ ] 검색 서비스 구현
- [ ] 대화 응답 서비스에 RAG 연결
- [ ] 단위 및 통합 테스트
- [ ] 검색 품질 평가 및 튜닝
- [ ] Azure Chroma 배포
- [ ] 운영 보안, 백업 및 복구 구성

## 9. 참고 문서

- [OpenAI text-embedding-3-small](https://developers.openai.com/api/docs/models/text-embedding-3-small)
- [OpenAI Embeddings API](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create)
- [Chroma Docker 배포](https://docs.trychroma.com/deployment/docker)
- [Chroma embedding functions](https://docs.trychroma.com/docs/embeddings/embedding-functions)
- [Chroma 클라이언트](https://docs.trychroma.com/reference/python/client)
- [Azure App Service 사용자 지정 컨테이너](https://learn.microsoft.com/en-us/azure/app-service/configure-custom-container)
- [Azure App Service 사이드카](https://learn.microsoft.com/en-us/azure/app-service/overview-sidecar)
