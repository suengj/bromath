# Lightning-SimulWhisper 설정 가이드

## 개요

Lightning-SimulWhisper는 Apple Silicon에서 Whisper 모델을 실시간으로 동작시키기 위한 초고속 로컬 음성 인식 시스템입니다. 이 가이드는 p10_bromath 프로젝트에서 Lightning-SimulWhisper를 테스트 환경으로 설정하는 방법을 설명합니다.

## 주요 특징

- **인코딩 속도**: PyTorch 기반 Whisper 대비 최대 18배 빠름 (CoreML 가속)
- **디코딩 속도**: 최대 15배 빠름 (MLX 프레임워크)
- **전력 효율**: Apple Neural Engine 가속으로 배터리 소모 최소화
- **실시간 스트리밍**: Simultaneous Speech Recognition 지원

## 설치 방법

### 1. Lightning-SimulWhisper 프로젝트 클론

```bash
cd /Users/suengj/Documents/Code/Python/PJT
git clone https://github.com/altalt-org/Lightning-SimulWhisper.git
cd Lightning-SimulWhisper
```

### 2. 기본 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. CoreML 가속 설치 (권장)

CoreML 가속을 사용하면 인코딩 속도가 최대 18배 향상됩니다:

```bash
pip install coremltools ane_transformers
```

### 4. CoreML 모델 변환 (선택사항)

CoreML 가속을 사용하려면 Whisper 모델을 CoreML 형식으로 변환해야 합니다:

```bash
# whisper.cpp 프로젝트 클론
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp

# 모델 변환 스크립트 실행
./scripts/generate_coreml_encoder.sh base
# 또는 다른 모델: tiny, small, medium, large-v3, large-v3-turbo 등
```

## 설정

### 1. 환경변수 설정 (선택사항)

프로젝트 경로를 환경변수로 설정할 수 있습니다:

```bash
export LIGHTNING_SIMUL_WHISPER_PATH=/path/to/Lightning-SimulWhisper
```

### 2. config.py 설정

`p10_bromath/config.py` 파일에서 다음 설정을 조정하세요:

```python
# Lightning-SimulWhisper 설정 (테스팅용)
LIGHTNING_SIMUL_WHISPER_ENABLED = True  # 테스팅 활성화
LIGHTNING_SIMUL_WHISPER_PATH = None  # None이면 자동 탐색
LIGHTNING_SIMUL_MODEL_NAME = "base"  # 사용할 모델
LIGHTNING_SIMUL_USE_COREML = True  # CoreML 가속 사용 (권장)
```

## 사용 방법

### 1. 단일 파일 테스트

```bash
cd /Users/suengj/Documents/Code/Python/PJT/p10_bromath
conda activate ai
python tbd/test_lightning_simulwhisper.py /path/to/audio.wav
```

### 2. 대화형 테스트

```bash
python tbd/test_lightning_simulwhisper.py
```

실행 후 다음 옵션 중 선택:
1. 단일 파일 테스트
2. 여러 파일 일괄 테스트 (처음 3개)
3. 모든 파일 테스트

### 3. 코드에서 직접 사용

```python
from stt_lightning_simulwhisper import LightningSimulWhisperTranscriber
from pathlib import Path

# 트랜스크라이버 초기화
transcriber = LightningSimulWhisperTranscriber(
    model_name="base",
    use_coreml=True,
    language="ko"
)

# 오디오 파일 전사
audio_path = Path("audio.wav")
text = transcriber.transcribe_audio(
    audio_path=audio_path,
    output_folder=Path("output"),
    language="ko",
    extract_srt=True  # SRT 파일도 생성
)
```

## 성능 비교

테스트 스크립트를 실행하면 다음과 같은 비교 결과를 확인할 수 있습니다:

- **처리 시간**: MLX Whisper vs Lightning-SimulWhisper
- **속도 향상**: x배 빠른지 표시
- **텍스트 길이**: 두 엔진의 출력 텍스트 길이 비교
- **출력 파일**: 각각의 결과 파일 저장 (비교 가능)

## 출력 파일 구조

테스트 결과는 `test_output/` 폴더에 저장됩니다:

```
test_output/
├── mlx_whisper/
│   ├── audio_file.txt
│   └── audio_file_SRT.srt
└── lightning_simulwhisper/
    ├── audio_file.txt
    └── audio_file_SRT.srt
```

## 지원 모델

Lightning-SimulWhisper는 다음 모델을 지원합니다:

- `tiny`, `tiny.en`
- `base`, `base.en`
- `small`, `small.en`
- `medium`, `medium.en`
- `large-v1`, `large-v2`, `large-v3`, `large-v3-turbo`

## 문제 해결

### 1. 모듈을 찾을 수 없음

**에러**: `Lightning-SimulWhisper 프로젝트를 찾을 수 없습니다`

**해결**:
- Lightning-SimulWhisper 프로젝트가 올바른 경로에 있는지 확인
- 환경변수 `LIGHTNING_SIMUL_WHISPER_PATH` 설정
- 또는 `config.py`의 `LIGHTNING_SIMUL_WHISPER_PATH`에 경로 지정

### 2. CoreML 관련 오류

**에러**: `coremltools를 찾을 수 없습니다`

**해결**:
```bash
pip install coremltools ane_transformers
```

또는 `config.py`에서 `LIGHTNING_SIMUL_USE_COREML = False`로 설정

### 3. 모델 로드 실패

**해결**:
- 모델 이름이 올바른지 확인
- 모델이 다운로드되었는지 확인
- Hugging Face 홈 경로가 올바르게 설정되었는지 확인

## 참고 자료

- **GitHub**: https://github.com/altalt-org/Lightning-SimulWhisper
- **원문 블로그**: https://discuss.pytorch.kr/t/lightning-simulwhisper-apple-silicon-feat-whisper/8070
- **Alt 앱**: https://altalt.io (Lightning-SimulWhisper를 사용하는 강의/회의 필기앱)

## 주의사항

- Lightning-SimulWhisper는 **Apple Silicon (M1/M2/M3/M4) 전용**입니다
- Intel Mac에서는 작동하지 않을 수 있습니다
- CoreML 가속 사용 시 Apple Neural Engine이 필요합니다
- 이 구현은 **테스팅용**이며, 실제 프로덕션 사용 시 추가 검증이 필요합니다
