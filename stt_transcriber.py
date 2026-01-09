"""
Speech-to-Text transcription module using Whisper.
Whisper 모델을 사용한 STT 전사 모듈입니다.
openai-whisper와 mlx-whisper를 모두 지원합니다.
"""
import os
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm


class STTTranscriber:
    """Whisper 기반 STT 전사 클래스"""
    
    def __init__(
        self,
        model_type: str = "openai",  # "openai" 또는 "mlx"
        model_path: Optional[Path] = None,
        model_name: str = "base",  # OpenAI Whisper 모델 이름
        mlx_model_name: str = "turbo",  # MLX Whisper 모델 이름 ("large" 또는 "turbo")
        hf_home_path: Optional[Path] = None
    ):
        """
        STTTranscriber 초기화
        
        Args:
            model_type: 모델 타입 ("openai" 또는 "mlx")
            model_path: Whisper 모델 파일 경로 (None이면 기본 모델 사용)
            model_name: OpenAI Whisper 기본 모델 이름 ("base", "small", "medium", "large")
            mlx_model_name: MLX Whisper 모델 이름 ("large" 또는 "turbo")
            hf_home_path: Hugging Face 홈 디렉토리 경로
        """
        self.model_type = model_type.lower()
        self.model_path = model_path
        self.model_name = model_name
        self.mlx_model_name = mlx_model_name
        self.hf_home_path = hf_home_path
        self.model = None
        self._load_model()
    
    def _mlx_model_selection(self, mlx_model: str) -> str:
        """
        MLX 모델 이름 매핑 (p03_speech2text 참고)
        
        Args:
            mlx_model: "large" 또는 "turbo"
            
        Returns:
            MLX 모델 이름
        """
        model_mapping = {
            "large": "whisper-large-v3-mlx",
            "turbo": "whisper-large-v3-turbo"
        }
        return model_mapping.get(mlx_model, "whisper-large-v3-turbo")
    
    def _load_model(self):
        """Whisper 모델 로드"""
        try:
            if self.model_type == "mlx":
                # MLX Whisper 모델 사용
                try:
                    import mlx_whisper
                except ImportError:
                    raise RuntimeError(
                        "mlx_whisper가 설치되어 있지 않습니다. "
                        "pip install mlx-whisper를 실행하세요."
                    )
                
                # HF_HOME 환경변수 설정
                if self.hf_home_path:
                    os.environ["HF_HOME"] = str(self.hf_home_path)
                    print(f"HF_HOME 설정: {self.hf_home_path}")
                
                selected_model = self._mlx_model_selection(self.mlx_model_name)
                print(f"MLX Whisper 모델 사용: {selected_model}")
                # MLX는 실제 전사 시 로드하므로 여기서는 모델 이름만 저장
                self.model = f"mlx-community/{selected_model}"
                
            else:
                # OpenAI Whisper 모델 사용
                import whisper
                
                if self.model_path and self.model_path.exists():
                    print(f"커스텀 모델 로드 중: {self.model_path}")
                    # 커스텀 모델 로드 (경로가 지정된 경우)
                    if self.model_path.is_file():
                        # .pt 파일인 경우
                        self.model = whisper.load_model(str(self.model_path))
                    else:
                        # 디렉토리인 경우
                        self.model = whisper.load_model(str(self.model_path))
                else:
                    print(f"OpenAI Whisper 모델 로드 중: {self.model_name}")
                    self.model = whisper.load_model(self.model_name)
            
            print("모델 로드 완료")
        except Exception as e:
            raise RuntimeError(f"모델 로드 실패: {e}")
    
    def transcribe_audio(
        self,
        audio_path: Path,
        output_folder: Optional[Path] = None,
        output_filename: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """
        오디오 파일을 텍스트로 전사합니다.
        
        Args:
            audio_path: 오디오 파일 경로
            output_folder: 텍스트 파일 저장 폴더 (None이면 저장 안 함)
            output_filename: 출력 파일명 (None이면 자동 생성)
            language: 언어 코드 (예: "ko", "en"). None이면 자동 감지
            
        Returns:
            전사된 텍스트
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        
        try:
            # Whisper 전사
            if self.model_type == "mlx":
                # MLX Whisper 전사
                import mlx_whisper
                
                # MLX Whisper는 자체적으로 진행률을 표시하므로
                # verbose=False로 설정하여 출력 최소화 (tqdm과 충돌 방지)
                try:
                    result = mlx_whisper.transcribe(
                        str(audio_path),
                        word_timestamps=False,
                        path_or_hf_repo=self.model,
                        verbose=False  # False로 설정하여 MLX의 자체 진행률 표시 최소화
                    )
                    text = result["text"].strip()
                    
                except Exception as mlx_error:
                    raise RuntimeError(f"MLX Whisper 전사 중 오류: {mlx_error}")
            else:
                # OpenAI Whisper 전사
                if language:
                    result = self.model.transcribe(
                        str(audio_path),
                        language=language
                    )
                else:
                    result = self.model.transcribe(str(audio_path))
                
                text = result["text"].strip()
            
            # 텍스트 파일로 저장
            if output_folder:
                output_folder.mkdir(parents=True, exist_ok=True)
                
                if output_filename is None:
                    output_filename = audio_path.stem + ".txt"
                
                output_path = output_folder / output_filename
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(text)
            
            return text
            
        except Exception as e:
            raise RuntimeError(f"전사 실패 ({audio_path.name}): {e}")
    
    def transcribe_all(
        self,
        audio_files: List[Path],
        output_folder: Path,
        language: Optional[str] = None,
        skip_existing: bool = True
    ) -> List[str]:
        """
        여러 오디오 파일을 일괄 전사합니다.
        
        Args:
            audio_files: 오디오 파일 경로 리스트
            output_folder: 텍스트 파일 저장 폴더
            language: 언어 코드 (None이면 자동 감지)
            skip_existing: True이면 이미 전사된 파일 건너뛰기
            
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
                    # 이미 있는 파일의 텍스트 읽기
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
        print(f"\n총 {len(files_to_process)}개의 파일을 전사합니다...")
        print("(MLX Whisper는 각 파일당 2-10분 정도 소요될 수 있습니다)")
        print("(큰 파일의 경우 더 오래 걸릴 수 있습니다)\n")
        
        import time as time_module
        
        for idx, audio_file in enumerate(tqdm(files_to_process, desc="STT 전사 진행", unit="파일"), 1):
            try:
                # 파일 정보 및 크기 출력
                file_size_mb = audio_file.stat().st_size / (1024 * 1024)
                tqdm.write(f"\n[{idx}/{len(files_to_process)}] 처리 중: {audio_file.name} ({file_size_mb:.1f} MB)")
                
                start_time = time_module.time()
                
                text = self.transcribe_audio(
                    audio_file,
                    output_folder,
                    language=language
                )
                
                elapsed_time = time_module.time() - start_time
                
                transcribed_texts.append(text)
                tqdm.write(f"  ✓ 완료: {audio_file.name} ({elapsed_time/60:.1f}분 소요, {len(text)} 문자)")
                
            except KeyboardInterrupt:
                tqdm.write(f"\n\n사용자에 의해 중단되었습니다.")
                tqdm.write(f"진행 상황: {idx-1}/{len(files_to_process)} 완료")
                break
            except Exception as e:
                elapsed = time_module.time() - start_time if 'start_time' in locals() else 0
                error_msg = f"  ✗ 오류 발생 ({audio_file.name}): {e}"
                tqdm.write(error_msg)
                if elapsed > 0:
                    tqdm.write(f"  경과 시간: {elapsed/60:.1f}분")
                continue
        
        return transcribed_texts
