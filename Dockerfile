# syntax=docker/dockerfile:1
# ==============================================================================
# 백엔드 애플리케이션 도커 이미지 빌드 레시피 (Dockerfile)
#
# [역할]
# 내 파이썬(FastAPI) 백엔드 코드를 어느 컴퓨터에서나 동일하게 실행할 수 있도록
# 독립된 전용 가상 실행 환경(도커 이미지)으로 밀봉/포장하는 "제작 설명서"입니다.
#
# [핵심 과정]
# 1. FROM   : 파이썬 3.12 슬림 버전 가상 환경 준비
# 2. WORKDIR: 컨테이너 내부 작업 폴더 지정 (/app)
# 3. COPY   : 소스 코드 및 설정 파일들을 컨테이너 내부로 복사
# 4. RUN    : 파이썬 패키지(FastAPI, SQLAlchemy 등) 설치
# 5. EXPOSE : 웹 서버 포트(8000) 개방
# 6. CMD    : 컨테이너 켜질 때 DB 마이그레이션 실행 후 FastAPI 서버 가동
# ==============================================================================

FROM python:3.12-slim AS runtime

# Python 로그를 즉시 출력하고 .pyc 생성을 막아 컨테이너 동작을 단순화합니다.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 빌드 도구가 필요한 패키지를 설치한 뒤 같은 레이어에서 정리합니다.
RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
RUN pip install --upgrade pip && pip install .

# 루트 권한으로 웹 애플리케이션을 실행하지 않습니다.
RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app

EXPOSE 8000

# 초기 단계에서는 마이그레이션과 데모 데이터 준비 후 API 서버를 실행합니다.
CMD ["sh", "-c", "alembic upgrade head && python -m app.db.demo_seed && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]

