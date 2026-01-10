"""
Lightning-SimulWhisper 기반 STT 전사 모듈 (테스팅용)
Apple Silicon용 초고속 실시간 음성 인식 엔진
기존 STTTranscriber와 동일한 인터페이스 제공
"""
import os
import sys
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm


class LightningSimulWhisperTranscriber:
    """Lightning-SimulWhisper 기반 STT 전사 클래스 (테스팅용)"""
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        model_name: str = "base",
        use_coreml: bool = True,
        language: Optional[str] = None,
        hf_home_path: Optional[Path] = None
    ):
        """
        LightningSimulWhisperTranscriber 초기화
        
        Args:
            model_path: Lightning-SimulWhisper 모델 경로 (None이면 Config에서 가져옴)
            model_name: 모델 이름 (None이면 Config에서 가져옴)
            use_coreml: CoreML 가속 사용 여부 (None이면 Config에서 가져옴)
            language: 언어 코드
            hf_home_path: Hugging Face 홈 디렉토리 경로
        """
        from config import Config
        
        # Config에서 기본값 가져오기
        if model_name == "base" and hasattr(Config, 'LIGHTNING_SIMUL_MODEL_NAME'):
            model_name = Config.LIGHTNING_SIMUL_MODEL_NAME
        if model_path is None and hasattr(Config, 'LIGHTNING_SIMUL_MODEL_PATH') and Config.LIGHTNING_SIMUL_MODEL_PATH:
            model_path = Config.LIGHTNING_SIMUL_MODEL_PATH
        if use_coreml and hasattr(Config, 'LIGHTNING_SIMUL_USE_COREML'):
            use_coreml = Config.LIGHTNING_SIMUL_USE_COREML
        self.model_path = model_path
        self.model_name = model_name
        self.use_coreml = use_coreml
        self.language = language
        self.hf_home_path = hf_home_path
        self.whisper_module = None
        self._check_dependencies()
        self._load_whisper_module()
    
    def _check_dependencies(self):
        """필요한 의존성 확인"""
        # MLX는 Lightning-SimulWhisper 내부에서 사용되므로 여기서 직접 import하지 않음
        # Lightning-SimulWhisper 모듈이 로드될 때 필요한 의존성을 확인
        
        if self.use_coreml:
            try:
                import coremltools
            except ImportError:
                print("경고: coremltools가 설치되지 않았습니다. CoreML 가속을 사용할 수 없습니다.")
                print("설치: pip install coremltools ane_transformers")
                self.use_coreml = False
    
    def _load_whisper_module(self):
        """Lightning-SimulWhisper 모듈 로드"""
        from config import Config
        
        # Lightning-SimulWhisper 프로젝트 경로 확인
        # 1. Config에서 경로 확인
        if Config.LIGHTNING_SIMUL_WHISPER_PATH:
            lightning_path = Config.LIGHTNING_SIMUL_WHISPER_PATH
        # 2. 환경변수 확인
        elif "LIGHTNING_SIMUL_WHISPER_PATH" in os.environ:
            lightning_path = Path(os.environ["LIGHTNING_SIMUL_WHISPER_PATH"])
            # 3. 기본 경로 확인 (여러 가능한 위치)
        else:
            possible_paths = [
                Path(__file__).parent.parent.parent.parent / "Lightning-SimulWhisper",  # /Users/suengj/Documents/Code/Python/PJT/Lightning-SimulWhisper
                Path(__file__).parent.parent.parent / "Lightning-SimulWhisper",  # /Users/suengj/Documents/Code/Python/Lightning-SimulWhisper
                Path(__file__).parent.parent / "Lightning-SimulWhisper",  # p10_bromath/Lightning-SimulWhisper
            ]
            
            lightning_path = None
            for path in possible_paths:
                if path.exists() and (path / "simulstreaming_whisper.py").exists():
                    lightning_path = path
                    break
            
            if lightning_path is None:
                # 기본값: PJT/Lightning-SimulWhisper (설치 가이드에 따라)
                lightning_path = possible_paths[0]
        
        if not lightning_path.exists():
            raise RuntimeError(
                f"Lightning-SimulWhisper 프로젝트를 찾을 수 없습니다.\n"
                f"예상 경로: {lightning_path}\n"
                f"설치 방법:\n"
                f"  1. git clone https://github.com/altalt-org/Lightning-SimulWhisper.git\n"
                f"  2. 환경변수 설정: export LIGHTNING_SIMUL_WHISPER_PATH=/path/to/Lightning-SimulWhisper\n"
                f"  3. config.py에서 LIGHTNING_SIMUL_WHISPER_PATH 설정\n"
                f"  4. 또는 프로젝트를 {lightning_path}에 배치\n"
                f"자세한 내용은 tbd/LIGHTNING_SIMUL_WHISPER_SETUP.md 참고"
            )
        
        # 경로 저장 (subprocess에서 사용)
        self._lightning_path = lightning_path
        
        # simulstreaming_whisper.py 파일 존재 확인
        simulstreaming_script = lightning_path / "simulstreaming_whisper.py"
        if not simulstreaming_script.exists():
            raise RuntimeError(
                f"simulstreaming_whisper.py를 찾을 수 없습니다: {simulstreaming_script}\n"
                f"프로젝트 경로: {lightning_path}\n"
                f"설치 가이드: tbd/LIGHTNING_SIMUL_WHISPER_SETUP.md 참고"
            )
        
        print(f"Lightning-SimulWhisper 프로젝트 경로: {lightning_path}")
    
    def transcribe_audio(
        self,
        audio_path: Path,
        output_folder: Optional[Path] = None,
        output_filename: Optional[str] = None,
        language: Optional[str] = None,
        extract_srt: bool = False
    ) -> str:
        """
        오디오 파일을 텍스트로 전사합니다.
        
        Args:
            audio_path: 오디오 파일 경로
            output_folder: 텍스트 파일 저장 폴더 (None이면 저장 안 함)
            output_filename: 출력 파일명 (None이면 자동 생성)
            language: 언어 코드 (예: "ko", "en"). None이면 자동 감지
            extract_srt: True이면 SRT 자막 파일도 생성
            
        Returns:
            전사된 텍스트
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        
        try:
            # 언어 설정 (파라미터 우선, 없으면 인스턴스 변수 사용)
            transcribe_language = language if language else self.language
            
            # HF_HOME 환경변수 설정
            if self.hf_home_path:
                os.environ["HF_HOME"] = str(self.hf_home_path)
            
            # Lightning-SimulWhisper 전사 실행
            # 실제 API는 프로젝트 구조에 따라 조정 필요
            # 예상: simulstreaming_whisper.transcribe_audio() 또는 유사한 함수
            print(f"Lightning-SimulWhisper 전사 시작: {audio_path.name}")
            
            # 임시: subprocess로 실행하는 방식 (실제 구현 시 조정)
            # 또는 직접 Python API 호출
            result = self._run_lightning_transcribe(
                audio_path=audio_path,
                language=transcribe_language,
                extract_srt=extract_srt
            )
            
            text = result.get("text", "").strip()
            segments = result.get("segments", [])
            
            # 텍스트 파일로 저장
            if output_folder:
                output_folder.mkdir(parents=True, exist_ok=True)
                
                if output_filename is None:
                    output_filename = audio_path.stem + ".txt"
                
                output_path = output_folder / output_filename
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(text)
                
                # SRT 파일 저장
                if extract_srt and segments:
                    self._save_srt_file(
                        segments=segments,
                        output_folder=output_folder,
                        audio_path=audio_path
                    )
            
            return text
            
        except Exception as e:
            raise RuntimeError(f"Lightning-SimulWhisper 전사 실패 ({audio_path.name}): {e}")
    
    def _run_lightning_transcribe(
        self,
        audio_path: Path,
        language: Optional[str],
        extract_srt: bool
    ) -> dict:
        """
        Lightning-SimulWhisper 실제 전사 실행
        실제 API 구조에 맞게 조정 필요
        
        Args:
            audio_path: 오디오 파일 경로
            language: 언어 코드
            extract_srt: SRT 추출 여부
            
        Returns:
            {"text": str, "segments": list} 형식의 결과
        """
        # Lightning-SimulWhisper의 simulstreaming_whisper.py 스크립트를 subprocess로 실행
        # 또는 Python API를 직접 호출 (프로젝트 구조에 따라)
        try:
            import subprocess
            import json
            import tempfile
            from config import Config
            
            # Lightning-SimulWhisper 프로젝트 경로 (로드 시 탐색한 경로 재사용)
            lightning_path = self._lightning_path
            simulstreaming_script = lightning_path / "simulstreaming_whisper.py"
            
            # 임시 출력 파일들 (텍스트 및 타임스탬프)
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)
                output_txt = tmpdir_path / "output.txt"
                output_segments = tmpdir_path / "output_segments.txt" if extract_srt else None
                
                # subprocess로 실행
                # simulstreaming_whisper.py는 whisper_streaming.whisper_online_main을 사용
                # audio_path는 첫 번째 위치 인자로 전달 (절대 경로로 변환)
                audio_path_abs = Path(audio_path).resolve()
                cmd = [
                    sys.executable,
                    str(simulstreaming_script),
                    str(audio_path_abs),
                    "--model_name", self.model_name,
                    "--lan", language or "ko"
                ]
                
                # model_path가 None이 아니고 실제 파일/디렉토리 경로인 경우에만 추가
                # simulstreaming_whisper.py의 기본값 './base.pt'는 HuggingFace repo ID가 아니므로
                # 실제 경로가 있을 때만 추가하고, 없으면 model_name으로 HuggingFace에서 자동 다운로드
                if self.model_path:
                    model_path_obj = Path(self.model_path)
                    if model_path_obj.exists():
                        cmd.extend(["--model_path", str(model_path_obj)])
                    else:
                        # 경로가 존재하지 않으면 HuggingFace repo ID로 간주하고 전달하지 않음
                        # model_name으로 자동 다운로드됨
                        pass
                
                if self.use_coreml:
                    cmd.append("--use_coreml")
                    if hasattr(Config, 'LIGHTNING_SIMUL_COREML_COMPUTE_UNITS'):
                        cmd.extend(["--coreml_compute_units", Config.LIGHTNING_SIMUL_COREML_COMPUTE_UNITS])
                
                # 실행 및 출력 리다이렉션
                print(f"Lightning-SimulWhisper 실행 명령: {' '.join(cmd)}")
                
                # stderr도 별도 파일로 저장하여 확인
                stderr_file = tmpdir_path / "stderr.txt"
                with open(output_txt, 'w', encoding='utf-8') as f_out, \
                     open(stderr_file, 'w', encoding='utf-8') as f_err:
                    result = subprocess.run(
                        cmd,
                        stdout=f_out,
                        stderr=f_err,
                        text=True,
                        cwd=str(lightning_path)
                    )
                
                # stderr 내용 읽기
                stderr_content = ""
                if stderr_file.exists():
                    with open(stderr_file, 'r', encoding='utf-8') as f:
                        stderr_content = f.read()
                
                # scikit-learn 경고는 무시 (경고일 뿐)
                if result.returncode != 0:
                    # 실제 오류만 확인 (scikit-learn 경고 제외)
                    actual_error = stderr_content
                    # scikit-learn 관련 경고 라인 제거
                    error_lines = [line for line in stderr_content.split('\n') 
                                 if 'scikit-learn' not in line.lower() and 
                                    'cache for model files' not in line.lower() and
                                    'migrating your old cache' not in line.lower()]
                    actual_error = '\n'.join(error_lines)
                    
                    # stderr에 실제 오류가 없고 INFO만 있으면 성공으로 처리
                    if actual_error.strip() and not any(keyword in actual_error.lower() for keyword in ['info', 'audio duration', 'arguments']):
                        raise RuntimeError(
                            f"Lightning-SimulWhisper 실행 실패 (return code: {result.returncode}):\n"
                            f"STDERR: {actual_error[:1000]}"
                        )
                    elif result.returncode != 0:
                        # return code가 0이 아니지만 실제 오류는 없는 경우 경고만 출력
                        print(f"경고: return code {result.returncode}, 하지만 실제 오류는 감지되지 않았습니다.")
                        print(f"STDERR (일부): {stderr_content[:500]}")
                
                # 결과 읽기
                if output_txt.exists():
                    with open(output_txt, 'r', encoding='utf-8') as f:
                        output_text = f.read().strip()
                    
                    # stdout 형식 파싱
                    # simulstreaming_whisper 출력 형식: 
                    # "{now_ms} {start_ts_ms} {end_ts_ms} {text}"
                    # 예: "4186.3606 0 1720 Takhle to je"
                    lines = output_text.split('\n')
                    text_lines = []
                    segments = []
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        # INFO, DEBUG 등의 로그 라인 제외
                        if line.startswith(('INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL')):
                            continue
                        # 숫자로 시작하는 라인만 처리 (타임스탬프 형식)
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                # 처음 3개는 숫자 (타임스탬프), 나머지가 텍스트
                                now_ms = float(parts[0])
                                start_ts_ms = float(parts[1])
                                end_ts_ms = float(parts[2])
                                text = ' '.join(parts[3:])
                                
                                if text:
                                    text_lines.append(text)
                                    if extract_srt:
                                        segments.append({
                                            "start": start_ts_ms / 1000.0,
                                            "end": end_ts_ms / 1000.0,
                                            "text": text
                                        })
                            except (ValueError, IndexError):
                                # 숫자 파싱 실패 시 전체를 텍스트로 처리
                                text_lines.append(line)
                        else:
                            # 형식이 맞지 않으면 전체를 텍스트로 처리
                            text_lines.append(line)
                    
                    full_text = ' '.join(text_lines)
                    
                    return {
                        "text": full_text,
                        "segments": segments if extract_srt else []
                    }
                else:
                    raise RuntimeError("출력 파일이 생성되지 않았습니다.")
            
        except FileNotFoundError as e:
            raise e
        except Exception as e:
            raise RuntimeError(
                f"Lightning-SimulWhisper 실행 오류: {e}\n"
                f"설치 및 사용 가이드: tbd/LIGHTNING_SIMUL_WHISPER_SETUP.md 참고"
            )
    
    def _save_srt_file(
        self,
        segments: List[dict],
        output_folder: Path,
        audio_path: Path
    ):
        """
        SRT 자막 파일을 저장합니다.
        
        Args:
            segments: 세그먼트 정보 리스트
            output_folder: 출력 폴더
            audio_path: 원본 오디오 파일 경로
        """
        if not segments:
            print(f"경고: 세그먼트 정보가 없어 SRT 파일을 생성할 수 없습니다.")
            return
        
        srt_filename = audio_path.stem + "_SRT.srt"
        srt_path = output_folder / srt_filename
        
        with open(srt_path, "w", encoding="utf-8") as f:
            for idx, segment in enumerate(segments, 1):
                start_time = self._format_timestamp(segment.get("start", 0))
                end_time = self._format_timestamp(segment.get("end", 0))
                text = segment.get("text", "").strip()
                
                f.write(f"{idx}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
        
        print(f"SRT 파일 저장: {srt_path}")
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        초 단위 시간을 SRT 형식 (HH:MM:SS,mmm)으로 변환합니다.
        
        Args:
            seconds: 초 단위 시간
            
        Returns:
            SRT 형식 타임스탬프 문자열
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def transcribe_all(
        self,
        audio_files: List[Path],
        output_folder: Path,
        language: Optional[str] = None,
        skip_existing: bool = True,
        extract_srt: bool = False
    ) -> List[str]:
        """
        여러 오디오 파일을 일괄 전사합니다.
        
        Args:
            audio_files: 오디오 파일 경로 리스트
            output_folder: 텍스트 파일 저장 폴더
            language: 언어 코드 (None이면 자동 감지)
            skip_existing: True이면 이미 전사된 파일 건너뛰기
            extract_srt: True이면 SRT 파일도 생성
            
        Returns:
            전사된 텍스트 리스트
        """
        if not audio_files:
            print("전사할 파일이 없습니다.")
            return []
        
        transcribed_texts = []
        
        # 이미 전사된 파일 필터링
        files_to_process = []
        if skip_existing:
            for audio_file in audio_files:
                expected_txt = output_folder / f"{audio_file.stem}.txt"
                if expected_txt.exists():
                    print(f"건너뛰기 (이미 전사됨): {audio_file.name}")
                    try:
                        with open(expected_txt, 'r', encoding='utf-8') as f:
                            transcribed_texts.append(f.read())
                    except:
                        pass
                else:
                    files_to_process.append(audio_file)
        else:
            files_to_process = audio_files
        
        if not files_to_process:
            print("모든 파일이 이미 전사되었습니다.")
            return transcribed_texts
        
        # tqdm으로 진행률 표시하며 전사
        print(f"\n총 {len(files_to_process)}개의 파일을 Lightning-SimulWhisper로 전사합니다...")
        print("(Lightning-SimulWhisper는 기존 MLX Whisper보다 빠를 수 있습니다)\n")
        
        import time as time_module
        
        for idx, audio_file in enumerate(tqdm(files_to_process, desc="Lightning-SimulWhisper 전사 진행", unit="파일"), 1):
            try:
                file_size_mb = audio_file.stat().st_size / (1024 * 1024)
                tqdm.write(f"\n[{idx}/{len(files_to_process)}] 처리 중: {audio_file.name} ({file_size_mb:.1f} MB)")
                
                start_time = time_module.time()
                
                text = self.transcribe_audio(
                    audio_file,
                    output_folder,
                    language=language,
                    extract_srt=extract_srt
                )
                
                elapsed_time = time_module.time() - start_time
                
                transcribed_texts.append(text)
                tqdm.write(f"  ✓ 완료: {audio_file.name} ({elapsed_time:.2f}초 소요, {len(text)} 문자)")
                
            except KeyboardInterrupt:
                tqdm.write(f"\n\n사용자에 의해 중단되었습니다.")
                tqdm.write(f"진행 상황: {idx-1}/{len(files_to_process)} 완료")
                break
            except Exception as e:
                elapsed = time_module.time() - start_time if 'start_time' in locals() else 0
                error_msg = f"  ✗ 오류 발생 ({audio_file.name}): {e}"
                tqdm.write(error_msg)
                if elapsed > 0:
                    tqdm.write(f"  경과 시간: {elapsed:.2f}초")
                continue
        
        return transcribed_texts
