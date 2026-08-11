## 스테이지 재생 세션 생성
- http 메서드: post
- 엔드포인트: api/v1/stages/{stageId}/sessions
- api 설명: 사용자가 스테이지 영상 조회를 한 후 플레이를 시작하면 호출한다.

프론트는 일반 관람 모드인지 ar 모드인지 전달을 하고 db에는 하나의 재생 세션이 생성됨.
- 요청 Query: 
- 요청 Path: 

{
	"stageId": 1
}

- 요청 Body:

{
	"viewMode": "NORMAL"
}
{
	"viewMode": "AR"
}

- 정상 응답 데이터: 201

{
  "stageSession": {
    "id": 501,
    "viewMode": "AR"
  }
}


- 오류 응답 데이터: 404

{
  "code": "STAGE_NOT_FOUND",
  "message": "스테이지 영상을 찾을 수 없습니다."
}

{
  "code": "ACTIVE_CUBE_OWNERSHIP_NOT_FOUND",
  "message": "활성화된 큐브 소유권을 찾을 수 없습니다."
}

- 오류 응답 데이터: 409

동일한 스테이지에 이미 `PLAYING` 상태인 세션이 있으면 반환한다.

{
  "code": "STAGE_SESSION_ALREADY_PLAYING",
  "message": "이미 재생 중인 스테이지 세션이 있습니다."
}







## 스테이지 재생 세션 저장
- http 메서드: patch
- 엔드포인트: api/v1/users/me/stage-sessions/{stageSessionId}
- 사용자가 스테이지 영상 재생을 하다가 영상이 끝나거나, 뒤로 가기 혹은 AR 모드로 전환을 하여 영상이 중간에 취소되면 세션 정보를 갱신해 저장하기 위해 호출된다.

재생 중인 `STAGE_SESSION`의 최종 재생 위치, 실제 시청 시간과 종료 상태를 저장한다.

로그인 기능을 구현하기 전까지 현재 사용자는 `user.id = 1`로 고정한다.
요청한 세션이 `user.id = 1`의 큐브 소유권에 속한 세션인지 확인한 후 저장한다.

- 사용자가 영상을 시청하다가 나감 → `CANCELLED`
- 영상이 끝까지 재생됨 → `COMPLETED`
- 일반 모드에서 AR 모드로 변경함 → 기존 일반 세션을 `CANCELLED`
- AR 모드에서 일반 모드로 변경함 → 기존 AR 세션을 `CANCELLED`
- 허용 상태 전이 → `PLAYING`에서 `COMPLETED` 또는 `CANCELLED`
- 이미 `COMPLETED` 또는 `CANCELLED`인 세션은 다시 변경할 수 없음

- 요청 Query: 
- 요청 Path: 

{
	"stageSessionId": 501
}

- 요청 Body:

{
	"status": "CANCELLED",
	"lastPositionSeconds": 74,
	"viewedSeconds": 62
}
{
  "status": "COMPLETED",
  "lastPositionSeconds": 222,
  "viewedSeconds": 222
}

- `lastPositionSeconds`: 영상을 종료한 시점의 재생 위치
- `viewedSeconds`: 사용자가 실제로 시청한 누적 시간
- `status`: `COMPLETED`, `CANCELLED`만 허용하며 프론트가 전달한 값을 그대로 저장
- `lastPositionSeconds`, `viewedSeconds`는 0 이상의 정수만 허용
- `lastPositionSeconds`는 스테이지 영상의 `duration_seconds`를 초과할 수 없음
- `lastPositionSeconds`에는 별도의 1~2초 오차를 허용하지 않음
- `viewedSeconds`는 반복 시청이 가능하므로 `lastPositionSeconds` 또는 `duration_seconds`보다 클 수 있음
- `ended_at`은 프론트에서 받지 않고 서버가 요청 처리 시점의 한국시간으로 저장
- 미션 카운트와 친밀도는 이 API에서 변경하지 않음

- 정상 응답 데이터: 204

응답 Body는 반환하지 않는다.



- 오류 응답 데이터: 404

세션이 존재하지 않거나 해당 세션이 현재 사용자 `user.id = 1`의 세션이 아니면 동일한 404 응답을 반환한다.

{
  "code": "STAGE_SESSION_NOT_FOUND",
  "message": "스테이지 재생 세션을 찾을 수 없습니다."
}


- 오류 응답 데이터: 409

요청한 세션이 이미 `COMPLETED` 또는 `CANCELLED` 상태이면 반환한다.

{
  "code": "STAGE_SESSION_ALREADY_ENDED",
  "message": "이미 종료된 스테이지 재생 세션입니다."
}

같은 세션에 종료 요청이 동시에 들어오면 먼저 처리된 요청만 204로 성공하고, 나중에 처리된 요청은 409를 반환한다.
