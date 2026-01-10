# 세션 요약: 2026-01-09

## 작업 목표
extracted_audio 폴더의 모든 오디오 파일에 대해:
1. Whisper MLX turbo로 SRT 모드 전사 → transcribed/ 폴더에 저장
2. 전사된 txt 파일을 GPT로 구조화 → structured/ 폴더에 .md/.html 저장

## 주요 작업 내역

### 1. Lightning-SimulWhisper 설치 및 테스트 (완료, 미사용)

**작업 내용**:
- Lightning-SimulWhisper 프로젝트 클론 (`/Users/suengj/Documents/Code/Python/PJT/Lightning-SimulWhisper`)
- 기본 의존성 설치 (librosa, mlx, tqdm, tiktoken, onnxruntime)
- CoreML 가속 도구 설치 (coremltools, ane_transformers)
- `stt_lightning_simulwhisper.py` 모듈 통합

**발견된 문제**:
- MLX 라이브러리 초기화 크래시 → MLX 직접 import 제거하여 해결
- 모델 다운로드 실패 (HuggingFace에서 자동 다운로드 이슈)
- 출력 파싱 문제

**결정사항**:
- 현재는 기존 MLX Whisper turbo 모델 사용 유지
- Lightning-SimulWhisper는 별도 클래스로 구현되어 기존 코드와 충돌 없음

---

### 2. SRT 파일 생성 기능 추가 (완료)

**문제 발견**:
- `transcribed/` 폴더에 txt 파일은 48개 있지만 SRT 파일은 0개
- `run_full_pipeline.py`에서 이미 전사된 파일은 건너뛰어 SRT가 생성되지 않음

**수정 내용**:
- `run_full_pipeline.py` 수정:
  - 이미 전사된 txt 파일이 있지만 SRT 파일이 없는 경우 자동 감지
  - `files_to_generate_srt` 리스트로 SRT만 필요한 파일 별도 처리
  - SRT 파일만 생성하는 로직 추가
- `stt_transcriber.py` 수정:
  - txt 파일이 이미 존재하는 경우 덮어쓰지 않도록 수정
  - SRT만 생성하는 경우에도 정상 작동하도록 개선

**테스트 결과**:
- 작은 파일(`BM_main_howDelicious02 - HD 720p.wav`)로 테스트 성공
- SRT 파일 생성 확인: `transcribed/BM_main_howDelicious02 - HD 720p_SRT.srt`

---

### 3. 문서 업데이트 (완료)

**context.md 업데이트**:
- SRT 자막 파일 생성 기능 추가 내용 반영
- Lightning-SimulWhisper 테스트 및 문제점 문서화
- 파이프라인 프로세스에 SRT 생성 단계 명시
- 최근 업데이트 내역 섹션 추가

---

### 4. 다음 작업

**대기 중인 작업**:
1. 전체 파이프라인 실행:
   - 48개 파일에 대해 SRT 파일 생성 (이미 txt는 있음)
   - 모든 txt 파일에 대해 GPT 구조화 작업 (이미 완료된 것으로 보임)
   
**예상 소요 시간**:
- SRT 파일 생성: 파일당 2-10분 (총 48개 파일)
- 구조화 작업: 이미 완료된 것으로 보임

---

## 현재 상태

### 완료된 작업
- ✅ Lightning-SimulWhisper 설치 및 테스트 (미사용 결정)
- ✅ SRT 파일 생성 기능 구현
- ✅ run_full_pipeline.py 수정 (SRT 자동 생성 로직)
- ✅ context.md 업데이트
- ✅ 기존 MLX Whisper 코드 정상 작동 확인

### 대기 중인 작업
- ⏳ 전체 파일에 대한 SRT 생성 (48개 파일)
- ⏳ 파이프라인 전체 실행 및 검증

---

## 파일 변경 사항

1. **run_full_pipeline.py**: SRT 파일 자동 생성 로직 추가
2. **stt_transcriber.py**: txt 파일 존재 시 덮어쓰지 않도록 수정
3. **context.md**: SRT 기능 및 Lightning-SimulWhisper 테스트 내용 추가
4. **stt_lightning_simulwhisper.py**: 새로 생성 (미사용)
5. **generate_srt_files.py**: 임시 스크립트 생성 (사용 안 함)

---

## 주의사항

1. **기존 코드 보존**: Lightning-SimulWhisper는 별도 클래스로 구현되어 기존 MLX Whisper 코드에 영향 없음
2. **SRT 생성 시간**: 파일당 2-10분 소요 예상 (큰 파일은 더 오래 걸림)
3. **구조화 작업**: 이미 대부분 완료된 것으로 보임 (structured/ 폴더 확인 필요)

---

## 실행 명령어

```bash
cd /Users/suengj/Documents/Code/Python/PJT/p10_bromath
conda activate ai
python run_full_pipeline.py
```
