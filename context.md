# p10_bromath 프로젝트 구조 및 이해

## 프로젝트 개요

**p10_bromath**는 수학 교육 콘텐츠를 처리하는 자동화 파이프라인입니다. 오디오/비디오 파일이나 텍스트 파일로부터 수학 강의/대화 내용을 추출하고, GPT를 활용하여 구조화된 마크다운 및 HTML 문서로 변환합니다.

### 주요 목적
- 수학 교육 콘텐츠(강의, 토론, 리뷰)의 자동 전사 및 구조화
- 시간 순서가 있는 대화 형식 지원
- 수학적 표기법 및 용어의 정확한 보존
- 전문적이고 간결한 형태로 콘텐츠 재구성

---

## 프로젝트 구조

### 디렉토리 구조
```
p10_bromath/
├── extracted_audio/      # .mov에서 추출한 오디오 파일 (.wav)
├── transcribed/          # STT로 전사된 텍스트 파일 (.txt)
├── record_text_raw/      # 시간 스탬프가 있는 원본 텍스트 파일 (.txt)
├── structured/           # 최종 구조화된 문서 (.md, .html)
├── clips/                # YouTube에서 다운로드한 오디오 파일
├── config.py             # 전역 설정 관리
├── main.py               # 오디오 추출 + STT 전사 파이프라인
├── run_full_pipeline.py  # 전체 파이프라인 통합 실행
└── [모듈 파일들]
```

---

## 핵심 모듈 설명

### 1. `config.py` - 설정 관리
**역할**: 모든 경로, 모델, 프롬프트 설정을 중앙 관리

**주요 설정 항목**:
- **경로 설정**:
  - `INPUT_FOLDER`: 입력 비디오 파일 폴더 (기본: `/Volumes/OricoSSD/BroMath`)
  - `AUDIO_OUTPUT_FOLDER`: 추출된 오디오 저장 폴더
  - `TEXT_OUTPUT_FOLDER`: STT 전사 텍스트 저장 폴더
  - `STRUCTURED_OUTPUT_FOLDER`: 최종 구조화 문서 저장 폴더
  - `RECORD_TEXT_RAW_FOLDER`: 시간 스탬프 텍스트 원본 폴더

- **모델 설정**:
  - `WHISPER_MODEL_TYPE`: "openai" 또는 "mlx"
  - `MLX_MODEL_NAME`: "large" 또는 "turbo"
  - `GPT_MODEL`: GPT 모델 이름 (기본: "gpt-5-mini-2025-08-07")
  - `HF_HOME_PATH`: Hugging Face 모델 저장 경로

- **프롬프트 설정**:
  - `CONTEXT_QUERY`: 수학 교육 콘텐츠 컨텍스트 설명
  - `MAIN_QUERY`: 주요 구조화 요구사항
  - `MATH_SPECIFIC_QUERY`: 수학 특화 요구사항 (수식, 용어 보존)
  - `TIMESTAMP_DIALOGUE_QUERY`: 시간 순서 대화 형식 요구사항
  - `TONE_QUERY`: 간결하고 전문적인 문체 요구

**특징**:
- `update_paths()` 메서드로 런타임 설정 변경 가능
- `create_directories()`로 필요한 폴더 자동 생성

---

### 2. `audio_extractor.py` - 오디오 추출
**역할**: .mov 비디오 파일에서 오디오 트랙을 추출하여 .wav/.mp3로 변환

**주요 클래스**: `AudioExtractor`

**주요 메서드**:
- `extract_audio()`: 단일 비디오 파일에서 오디오 추출
- `extract_all()`: 폴더 내 모든 .mov 파일 일괄 처리
- `find_mov_files()`: 입력 폴더에서 .mov 파일 검색

**기술 스택**:
- `ffmpeg`를 subprocess로 호출하여 오디오 추출
- 샘플레이트 16kHz (Whisper 최적화), 모노 채널로 변환
- 이미 추출된 파일 건너뛰기 옵션 지원

---

### 3. `stt_transcriber.py` - 음성 인식
**역할**: 오디오 파일을 텍스트로 전사 (Speech-to-Text)

**주요 클래스**: `STTTranscriber`

**지원 모델**:
1. **OpenAI Whisper**: 오픈소스 Whisper 모델
   - 모델 이름: "base", "small", "medium", "large"
   - 커스텀 모델 경로 지원
2. **MLX Whisper**: Apple Silicon 최적화 Whisper
   - 모델: "whisper-large-v3-mlx" 또는 "whisper-large-v3-turbo"
   - Hugging Face Hub에서 모델 로드

**주요 메서드**:
- `transcribe_audio()`: 단일 오디오 파일 전사
- `transcribe_all()`: 여러 오디오 파일 일괄 전사 (진행률 표시)
- `_load_model()`: 모델 타입에 따라 적절한 Whisper 모델 로드

**특징**:
- 한국어 전사 특화 (language="ko")
- tqdm으로 진행률 표시
- 이미 전사된 파일 건너뛰기 옵션
- 전사 시간 및 파일 크기 정보 출력

---

### 4. `text_processor.py` - 텍스트 구조화
**역할**: 전사된 텍스트를 GPT로 구조화된 마크다운/HTML로 변환

**주요 클래스**: `TextProcessor`

**주요 메서드**:
- `process_single_file()`: 단일 텍스트 파일 처리
- `process_all_files()`: 폴더 내 모든 텍스트 파일 일괄 처리
- `process_text_with_gpt()`: GPT API 호출하여 구조화
- `build_prompt()`: 복잡한 프롬프트 구성 (토큰 계산 포함)
- `save_structured_text()`: 마크다운/HTML 파일 저장

**프롬프트 구조**:
1. **Context Query**: 수학 교육 콘텐츠 컨텍스트
2. **Main Query**: 핵심 개념과 상세 설명 구분, 표/불릿 포인트 활용
3. **Additional Query**: 인사이트 추가, Key Takeaways 강조
4. **Math-Specific Query**: 수학 용어/표기법 보존, LaTeX 수식 포맷
5. **Timestamp Dialogue Query**: 시간 순서 대화 형식 보존
6. **Tone Query**: 간결하고 전문적인 문체

**출력 형식**:
- **마크다운 (.md)**: 날짜 접두사 포함 파일명 (예: `2025-01-19_143022_파일명.md`)
- **HTML (.html)**: MathJax 지원, 반응형 스타일링, 수식 렌더링

**토큰 관리**:
- 원본 텍스트 토큰 수 계산 (tiktoken 사용)
- 목표 토큰 범위: 원본의 1.2~1.5배 (설정 가능)
- 최대 2배까지 허용

---

### 5. `youtube_downloader.py` - YouTube 오디오 다운로드
**역할**: YouTube 비디오에서 오디오를 다운로드

**주요 클래스**: `YouTubeDownloader`

**주요 메서드**:
- `download_audio()`: 단일 URL에서 오디오 다운로드
- `download_from_csv()`: CSV 파일의 URL 목록 일괄 다운로드
- `extract_youtube_id()`: YouTube URL에서 비디오 ID 추출
- `sanitize_filename()`: 파일명 정제 (특수문자 제거)

**기술 스택**:
- `pytubefix` 라이브러리 사용
- 프록시 지원
- WAV 변환 옵션 (extracted_audio와 동일한 형식)

---

### 6. 메인 실행 스크립트

#### `main.py`
- **기능**: 오디오 추출 + STT 전사 파이프라인
- **프로세스**:
  1. `extracted_audio` 폴더에서 .mov 파일 찾기
  2. 오디오 추출 (.wav)
  3. STT 전사 (.txt)

#### `main_record_processor.py`
- **기능**: 시간 스탬프가 있는 레코드 텍스트 처리
- **특징**: `TIMESTAMP_DIALOGUE_QUERY` 프롬프트 적용
- **입력**: `record_text_raw/` 폴더의 .txt 파일
- **출력**: `structured/` 폴더의 .md/.html 파일

#### `main_text_processor.py`
- **기능**: 전사된 텍스트를 구조화
- **입력**: `transcribed/` 폴더의 .txt 파일
- **출력**: `structured/` 폴더의 .md/.html 파일

#### `main_youtube_downloader.py`
- **기능**: CSV 파일의 YouTube URL 목록 다운로드
- **입력**: `input_df.csv` (url 컬럼 필수)
- **출력**: `clips/` 폴더의 오디오 파일

#### `run_full_pipeline.py` - **통합 파이프라인**
- **기능**: 전체 파이프라인을 순차적으로 실행하고 진행 상황 추적
- **프로세스**:

  **1단계: record_text_raw → structured**
  - `record_text_raw/` 폴더의 .txt 파일 읽기
  - 시간 순서 대화 형식 특화 프롬프트 적용
  - GPT로 구조화하여 .md/.html 저장
  - 로그에 완료 표시

  **2단계: extracted_audio → transcribed → structured**
  - `extracted_audio/` 폴더의 .wav 파일 찾기
  - STT 전사하여 `transcribed/`에 .txt 저장
  - 전사된 텍스트를 GPT로 구조화하여 `structured/`에 저장
  - 각 단계별 완료 상태를 로그에 기록

- **진행 상황 추적**: `log.csv` 파일로 각 파일의 처리 단계 추적
  - 컬럼: `filename`, `extracted_audio`, `record_text_raw`, `transcribed`, `structured`
  - 값: 'O' (완료) 또는 빈 문자열 (미완료)

- **특징**:
  - 이미 처리된 파일 자동 건너뛰기
  - 중간 저장으로 중단 시 재개 가능
  - 전체 실행 시간 및 진행 상황 출력

---

## 파이프라인 플로우

### 경로 1: 레코드 텍스트 처리
```
record_text_raw/*.txt
    ↓
[GPT 구조화]
    ↓
structured/*.md, *.html
```

### 경로 2: 오디오 처리
```
.mov 파일 (INPUT_FOLDER)
    ↓
[AudioExtractor: ffmpeg]
    ↓
extracted_audio/*.wav
    ↓
[STTTranscriber: Whisper]
    ↓
transcribed/*.txt
    ↓
[TextProcessor: GPT]
    ↓
structured/*.md, *.html
```

### 경로 3: YouTube 다운로드
```
input_df.csv (YouTube URL 목록)
    ↓
[YouTubeDownloader: pytubefix]
    ↓
clips/*.wav
    ↓
[옵션: extracted_audio로 이동 후 경로 2 진행]
```

---

## 설정 및 사용법

### 필요한 환경
- Python 3.8+
- ffmpeg (오디오 추출용)
- OpenAI API 키 또는 환경변수
- MLX Whisper 사용 시: Hugging Face 모델 저장 공간

### 의존성 패키지
```
openai-whisper>=20231117
mlx-whisper>=0.1.0
openai>=1.0.0
tiktoken>=0.5.0
pytubefix>=6.0.0
pandas>=1.5.0
markdown>=3.4.0
tqdm>=4.65.0
```

### 기본 사용법

1. **설정 파일 수정** (`config.py`):
   - `INPUT_FOLDER`: 입력 비디오 폴더 경로
   - `API_KEY_PATH`: OpenAI API 키 파일 경로
   - `WHISPER_MODEL_TYPE`: 사용할 Whisper 모델 타입
   - `GPT_MODEL`: 사용할 GPT 모델

2. **전체 파이프라인 실행**:
   ```bash
   python run_full_pipeline.py
   ```

3. **개별 단계 실행**:
   ```bash
   # 오디오 추출 + STT 전사
   python main.py
   
   # 레코드 텍스트 구조화
   python main_record_processor.py
   
   # 전사된 텍스트 구조화
   python main_text_processor.py
   
   # YouTube 다운로드
   python main_youtube_downloader.py
   ```

---

## 주요 특징

### 1. 수학 콘텐츠 특화
- 수학 용어 및 표기법 정확한 보존
- LaTeX 수식 포맷 지원
- 수학 개념 계층 구조 정리
- 문제 해결 구조 명확화

### 2. 시간 순서 대화 형식 지원
- 시간 스탬프 보존 및 활용
- 화자 구분 (참석자 1, 참석자 2 등)
- 대화 흐름 및 시간적 맥락 유지

### 3. 유연한 모델 선택
- OpenAI Whisper vs MLX Whisper 선택 가능
- 다양한 GPT 모델 지원
- 커스텀 모델 경로 지원

### 4. 진행 상황 추적
- `log.csv`로 각 파일의 처리 단계 추적
- 이미 처리된 파일 자동 건너뛰기
- 중단 후 재개 가능

### 5. 다양한 출력 형식
- 마크다운 (.md)
- HTML (.html) with MathJax
- 반응형 웹 스타일링

---

## 코드 구조 요약

### 모듈 간 의존성
```
config.py (설정)
    ↑
    ├── audio_extractor.py
    ├── stt_transcriber.py
    ├── text_processor.py
    ├── youtube_downloader.py
    └── main*.py (실행 스크립트)
    
run_full_pipeline.py (통합 실행)
    ├── main_record_processor.py
    └── main_text_processor.py
```

### 핵심 데이터 흐름
1. **오디오/비디오 입력** → `AudioExtractor` → `.wav` 파일
2. **오디오 파일** → `STTTranscriber` → `.txt` 파일
3. **텍스트 파일** → `TextProcessor` + GPT → `.md` / `.html` 파일

---

## 개선 가능한 부분

1. **에러 처리**: 일부 모듈에서 예외 처리 강화 필요
2. **병렬 처리**: 여러 파일 처리 시 병렬화 가능
3. **프롬프트 조정**: 실제 출력 결과에 따라 프롬프트 최적화
4. **테스트**: 더 포괄적인 단위 테스트 추가
5. **로깅**: 더 상세한 로깅 및 에러 추적

---

## 참고사항

- MLX Whisper는 Apple Silicon (M1/M2/M3)에서 최적화됨
- OpenAI Whisper는 범용적으로 사용 가능하지만 느릴 수 있음
- GPT 모델은 비용이 발생하므로 토큰 범위 설정 중요
- HTML 출력 시 MathJax CDN 사용 (온라인 환경 필요)
