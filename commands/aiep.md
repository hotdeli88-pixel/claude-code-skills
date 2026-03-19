---
name: aiep
description: 전북교육청 AIEP(AI 맞춤형 교수학습 플랫폼, ai.jbedu.kr) 관리 스킬. MCP 서버를 통해 수업 관리, 학생 관리, 콘텐츠 검색, 학습현황 조회, 공지사항 확인 등을 수행합니다. 사용자가 "수업", "클래스", "학생", "과제", "토론", "공지", "AIEP", "ai.jbedu.kr", "학습현황", "콘텐츠" 등을 언급하면 이 스킬을 사용하세요.
---

# AIEP MCP 관리 스킬

## 개요
전북특별자치도교육청 AIEP(AI 맞춤형 교수학습 플랫폼)을 MCP 도구를 통해 관리하는 스킬입니다.
사이트 URL: https://ai.jbedu.kr/

## 사이트 특성
- SPA(Single Page Application) 방식 -- URL은 항상 `https://ai.jbedu.kr/` 고정
- 모든 페이지 전환은 좌측 사이드바 메뉴 클릭으로 이루어짐
- 데이터 조회는 POST 방식의 Ajax 호출로 처리됨
- NEIS 연동 인증 체계 사용

---

## MCP 도구 목록 및 사용법

MCP 도구를 호출하기 전에 반드시 `ToolSearch`로 해당 도구를 로드해야 합니다.
예: `ToolSearch` query="+aiep class list" 또는 query="select:aiep_get_class_list"

### 카테고리별 도구 목록

#### 1. 사용자정보
| 도구 | 설명 | 주요 파라미터 |
|------|------|---------------|
| `aiep_get_user_info` | 로그인한 사용자 기본 정보 조회 | 없음 |
| `aiep_get_teacher_info` | 교사 상세정보 조회 (학교, 담당과목 등) | 없음 |

#### 2. 내수업
| 도구 | 설명 | 주요 파라미터 |
|------|------|---------------|
| `aiep_get_class_list` | 클래스 목록 조회 | `schlGrdr` (학년), `serchTxt` (검색어) |
| `aiep_get_weekly_schedule` | 주간 수업 목록 조회 | 없음 |
| `aiep_get_today_classes` | 오늘의 수업 조회 | 없음 |
| `aiep_get_my_lecture_combo` | 수업 콤보(드롭다운) 목록 조회 | 없음 |

#### 3. 학습콘텐츠
| 도구 | 설명 | 주요 파라미터 |
|------|------|---------------|
| `aiep_search_content` | 수업콘텐츠 검색 (49,000+건) | `grade` (학년), `subject` (교과), `cntntsType` (콘텐츠타입), `searchWord` (검색어) |
| `aiep_search_bundles` | 수업꾸러미 검색 | `searchWrd` (검색어), `publishType` (공개타입) |

#### 4. 학생관리
| 도구 | 설명 | 주요 파라미터 |
|------|------|---------------|
| `aiep_get_student_classes` | 학생배정 교과클래스 조회 | `schlGrdr` (학년), `lctrNm` (클래스명) |

#### 5. 학습현황
| 도구 | 설명 | 주요 파라미터 |
|------|------|---------------|
| `aiep_get_learning_stats` | 통합학습현황 조회 | `lectSttsCd` (수업상태코드), `lectNm` (수업명) |
| `aiep_get_student_learning_stats` | 학생별 학습현황 조회 | 없음 |
| `aiep_get_learning_progress` | 수업 진행 통계 조회 | `startDate` (시작일), `endDate` (종료일), `periodType` (일/주/월) |

#### 6. 헬프센터
| 도구 | 설명 | 주요 파라미터 |
|------|------|---------------|
| `aiep_get_edu_notices` | 교육청 공지사항 조회 | 없음 |
| `aiep_get_school_notices` | 학교 공지사항 조회 | 없음 |
| `aiep_get_faq` | 자주묻는질문(FAQ) 조회 | 없음 |
| `aiep_get_inquiries` | 이용문의 게시판 조회 | 없음 |
| `aiep_get_community_posts` | 교사커뮤니티 게시글 조회 | 없음 |
| `aiep_get_webzine` | 웹진(뉴스레터) 조회 | 없음 |
| `aiep_get_events` | 이벤트 조회 | 없음 |
| `aiep_get_policy_info` | 정책정보 조회 | 없음 |
| `aiep_get_support_centers` | 지역별 지원센터 조회 | 없음 |
| `aiep_get_manuals` | 이용자 매뉴얼 조회 | 없음 |

#### 7. 마이페이지
| 도구 | 설명 | 주요 파라미터 |
|------|------|---------------|
| `aiep_get_assignments` | 과제 목록 조회 | `lctrId` (수업ID), `pstTtl` (제목 검색) |
| `aiep_get_discussions` | 토론 목록 조회 | `lctrId` (수업ID), `pstTtl` (제목 검색) |
| `aiep_get_qna` | Q&A(묻고답하기) 목록 조회 | `lctrId` (수업ID), `ansYn` (답변여부) |
| `aiep_get_qna_answer_count` | Q&A 답변 건수 조회 | 없음 |
| `aiep_get_my_records` | 내 기록 조회 | 없음 |
| `aiep_get_my_inquiries` | 내 이용문의 조회 | 없음 |
| `aiep_get_screen_settings` | 화면설정 조회 | 없음 |

#### 8. 공통코드
| 도구 | 설명 | 주요 파라미터 |
|------|------|---------------|
| `aiep_get_common_codes` | 공통 코드(학년, 교과, 상태 등) 조회 | 없음 |

#### 9. LCMS 저작도구
| 도구 | 설명 | 주요 파라미터 |
|------|------|---------------|
| `aiep_lcms_list_content` | LCMS 콘텐츠 목록 조회 | `searchKeyword` (검색어) |
| `aiep_lcms_list_authoring` | 저작도구 콘텐츠 목록 조회 | `searchKeyword` (검색어) |
| `aiep_lcms_get_authoring_detail` | 저작도구 콘텐츠 상세 | `content_id` (콘텐츠ID) |
| `aiep_lcms_register_authoring` | 저작도구 콘텐츠 등록 | `tool_type` (타입), `title` (제목), `content_data` (JSON) |
| `aiep_lcms_delete_authoring` | 저작도구 콘텐츠 삭제 | `content_id` (콘텐츠ID) |
| `aiep_generate_authoring_content` | 콘텐츠 JSON 생성 (로컬) | `tool_type`, `title`, `subject`, `grade`, `unit`, `questions_json` |

---

## 메뉴 구조 참고

### 내수업
| 메뉴 | 경로 | MCP 도구 |
|------|------|----------|
| 내수업홈 | 내수업 > 내수업홈 | `aiep_get_class_list`, `aiep_get_today_classes`, `aiep_get_weekly_schedule` |
| 수업꾸러미 | 학습콘텐츠 > 수업꾸러미 | `aiep_search_bundles` |
| 수업콘텐츠 | 학습콘텐츠 > 수업콘텐츠 | `aiep_search_content` |

### 학생관리
| 메뉴 | 경로 | MCP 도구 |
|------|------|----------|
| 교과클래스 | 학생관리 > 학생배정 > 교과클래스 | `aiep_get_student_classes` |

### 학습현황
| 메뉴 | 경로 | MCP 도구 |
|------|------|----------|
| 통합학습현황 | 학습현황 > 통합학습현황 | `aiep_get_learning_stats`, `aiep_get_learning_progress` |
| 학생별학습현황 | 학습현황 > 학생별학습현황 | `aiep_get_student_learning_stats` |

### 헬프센터
| 메뉴 | 경로 | MCP 도구 |
|------|------|----------|
| 교육청공지사항 | 헬프센터 > 교육청공지사항 | `aiep_get_edu_notices` |
| 학교공지사항 | 헬프센터 > 학교공지사항 | `aiep_get_school_notices` |
| 이용자매뉴얼 | 헬프센터 > 이용자매뉴얼 | `aiep_get_manuals` |
| 자주묻는질문 | 헬프센터 > 자주묻는질문 | `aiep_get_faq` |
| 이용문의 | 헬프센터 > 이용문의 | `aiep_get_inquiries` |
| 교사커뮤니티 | 헬프센터 > 교사커뮤니티 | `aiep_get_community_posts` |
| 웹진 | 헬프센터 > 웹진 | `aiep_get_webzine` |
| 이벤트 | 헬프센터 > 이벤트 | `aiep_get_events` |
| 정책정보 | 헬프센터 > 정책정보 | `aiep_get_policy_info` |
| 지역별지원센터 | 헬프센터 > 지역별지원센터 | `aiep_get_support_centers` |

### 마이페이지
| 메뉴 | 경로 | MCP 도구 |
|------|------|----------|
| 내정보관리 | 마이페이지 > 내정보관리 | `aiep_get_user_info`, `aiep_get_teacher_info` |
| 과제정보 | 마이페이지 > 내수업정보 > 과제정보 | `aiep_get_assignments` |
| 토론정보 | 마이페이지 > 내수업정보 > 토론정보 | `aiep_get_discussions` |
| 묻고답하기 | 마이페이지 > 내수업정보 > 묻고답하기 | `aiep_get_qna`, `aiep_get_qna_answer_count` |
| 화면설정 | 마이페이지 > 내환경설정 > 화면설정 | `aiep_get_screen_settings` |
| 내기록관리 | 마이페이지 > 내기록관리 | `aiep_get_my_records` |
| 내이용문의 | 마이페이지 > 내이용문의 | `aiep_get_my_inquiries` |

### LCMS 저작도구
| 메뉴 | 경로 | MCP 도구 |
|------|------|----------|
| 콘텐츠 | 수업콘텐츠 관리 > 콘텐츠 | `aiep_lcms_list_content` |
| 저작도구 | 수업콘텐츠 관리 > 저작도구 | `aiep_lcms_list_authoring`, `aiep_lcms_register_authoring` |

---

## 작업별 수행 시나리오 (MCP 도구 호출)

### 1. 클래스 목록 조회
```
1. aiep_get_class_list 호출 (schlGrdr로 학년 필터, serchTxt로 검색)
2. 결과에서 클래스ID(lctrId), 클래스명, 학생수, 등록일 확인
```

### 2. 수업콘텐츠 검색
```
1. aiep_get_common_codes 호출하여 학년/교과/콘텐츠타입 코드값 확인
2. aiep_search_content 호출 (grade, subject, cntntsType, searchWord 지정)
3. 결과에서 콘텐츠명, 조회수, 태그 확인
```

### 3. 학생 배정 확인
```
1. aiep_get_student_classes 호출 (schlGrdr로 학년 필터, lctrNm으로 클래스명 검색)
2. 결과에서 번호, 학년, 클래스명, 학생수, 등록일 확인
```

### 4. 통합학습현황 조회
```
1. aiep_get_learning_stats 호출 (lectSttsCd, lectNm으로 필터)
2. aiep_get_learning_progress 호출 (startDate, endDate, periodType 지정)
3. 클래스 개설현황, 수업 진행 현황, 참여 현황 데이터 확인
```

### 5. 학생별 학습현황 조회
```
1. aiep_get_student_learning_stats 호출
2. 개설 클래스 수, 배정학생 수, 학사 진행율, 수업 진행율 확인
```

### 6. 공지사항 확인
```
1. aiep_get_edu_notices 또는 aiep_get_school_notices 호출
2. 결과에서 제목, 날짜, 내용 확인
```

### 7. 과제/토론/Q&A 관리
```
1. aiep_get_my_lecture_combo 호출하여 수업 목록(콤보) 조회
2. aiep_get_assignments / aiep_get_discussions / aiep_get_qna 호출
   (lctrId로 수업 지정, pstTtl 또는 ansYn으로 필터)
3. 미답변 Q&A 확인: aiep_get_qna_answer_count 호출
```

### 8. 수업꾸러미 검색
```
1. aiep_search_bundles 호출 (searchWrd로 키워드, publishType으로 공개타입 지정)
2. 결과에서 꾸러미명, 포함 콘텐츠 목록 확인
```

### 9. 교사 정보/프로필 확인
```
1. aiep_get_user_info 호출 -- 기본 사용자 정보
2. aiep_get_teacher_info 호출 -- 학교, 담당과목 등 상세 정보
```

### 10. 지역별 지원센터 조회
```
1. aiep_get_support_centers 호출
2. 결과에서 지역, 센터명, 담당자, 연락처 확인
```

### 11. 저작도구 콘텐츠 생성 및 등록
```
1. 교과/학년/단원 정보 수집
2. aiep_generate_authoring_content 호출로 콘텐츠 JSON 생성 (tool_type 지정)
3. 생성된 JSON 검증 (valid 필드 확인)
4. aiep_lcms_register_authoring 호출로 LCMS에 등록
5. aiep_lcms_list_authoring으로 등록 확인
```

---

## 주의사항

### 인증 관련
- NEIS 연동 인증 체계 사용 -- MCP 서버의 인증 세션이 만료되면 도구 호출이 실패할 수 있음
- 인증 오류 발생 시 사용자에게 AIEP 사이트에서 재로그인을 안내

### 파라미터 형식
- 날짜 파라미터: `YYYY-MM-DD` 형식 사용 (예: `2026-03-04`)
- 학년(schlGrdr/grade): 공통코드 조회 후 해당 코드값 사용
- 수업ID(lctrId): `aiep_get_class_list` 또는 `aiep_get_my_lecture_combo` 결과에서 획득
- 검색어: 부분 일치 검색 지원

### 도구 호출 순서
- 대부분의 조회 작업은 단일 도구 호출로 가능
- 코드값이 필요한 경우 먼저 `aiep_get_common_codes`로 코드 체계 확인
- 수업(lctrId) 기반 조회는 먼저 `aiep_get_class_list` 또는 `aiep_get_my_lecture_combo`로 수업ID 획득
- 결과가 페이징될 수 있으므로 필터 조건을 구체적으로 지정

### 기타
- SPA이므로 브라우저 기반 접근 시 새로고침하면 메인 페이지로 돌아감
- 검색 결과가 없을 때는 필터 조건을 완화하여 재시도
- 정렬 기본값은 대부분 "최신순"
