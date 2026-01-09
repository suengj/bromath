"""
Audio extraction module for .mov files.
.mov 파일에서 오디오를 추출하는 모듈입니다.
"""
import subprocess
import os
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm


class AudioExtractor:
    """오디오 추출 클래스"""
    
    def __init__(self, audio_format: str = "wav", sample_rate: int = 16000):
        """
        AudioExtractor 초기화
        
        Args:
            audio_format: 출력 오디오 형식 ("mp3" 또는 "wav")
            sample_rate: 오디오 샘플레이트 (Hz)
        """
        self.audio_format = audio_format.lower()
        self.sample_rate = sample_rate
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """ffmpeg가 설치되어 있는지 확인"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "ffmpeg가 설치되어 있지 않습니다. "
                "macOS: brew install ffmpeg\n"
                "Ubuntu: sudo apt-get install ffmpeg\n"
                "Windows: https://ffmpeg.org/download.html"
            )
    
    def find_mov_files(self, input_folder: Path) -> List[Path]:
        """
        입력 폴더에서 .mov 파일을 찾습니다.
        
        Args:
            input_folder: 검색할 폴더 경로
            
        Returns:
            .mov 파일 경로 리스트
        """
        if not input_folder.exists():
            raise FileNotFoundError(f"입력 폴더를 찾을 수 없습니다: {input_folder}")
        
        mov_files = list(input_folder.glob("*.mov"))
        mov_files.extend(input_folder.glob("*.MOV"))
        
        if not mov_files:
            print(f"경고: {input_folder}에서 .mov 파일을 찾을 수 없습니다.")
        
        return mov_files
    
    def extract_audio(
        self,
        video_path: Path,
        output_folder: Path,
        output_filename: Optional[str] = None
    ) -> Path:
        """
        비디오 파일에서 오디오를 추출합니다.
        
        Args:
            video_path: 비디오 파일 경로
            output_folder: 오디오 파일 저장 폴더
            output_filename: 출력 파일명 (None이면 자동 생성)
            
        Returns:
            추출된 오디오 파일 경로
        """
        # 출력 폴더 생성
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # 출력 파일명 생성
        if output_filename is None:
            output_filename = video_path.stem + f".{self.audio_format}"
        
        output_path = output_folder / output_filename
        
        # ffmpeg 명령어 구성
        if self.audio_format == "mp3":
            codec = "libmp3lame"
            output_path = output_path.with_suffix(".mp3")
        elif self.audio_format == "wav":
            codec = "pcm_s16le"
            output_path = output_path.with_suffix(".wav")
        else:
            raise ValueError(f"지원하지 않는 오디오 형식: {self.audio_format}")
        
        # ffmpeg 명령어 실행
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",  # 비디오 스트림 제거
            "-acodec", codec,
            "-ar", str(self.sample_rate),  # 샘플레이트
            "-ac", "1",  # 모노 채널
            "-y",  # 파일 덮어쓰기 허용
            str(output_path)
        ]
        
        try:
            print(f"오디오 추출 중: {video_path.name} -> {output_path.name}")
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"완료: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            raise RuntimeError(
                f"오디오 추출 실패 ({video_path.name}): {error_msg}"
            )
    
    def extract_all(
        self,
        input_folder: Path,
        output_folder: Path,
        skip_existing: bool = True
    ) -> List[Path]:
        """
        입력 폴더의 모든 .mov 파일에서 오디오를 추출합니다.
        
        Args:
            input_folder: .mov 파일이 있는 폴더
            output_folder: 추출된 오디오 저장 폴더
            skip_existing: True이면 이미 추출된 파일 건너뛰기
            
        Returns:
            추출된 오디오 파일 경로 리스트
        """
        mov_files = self.find_mov_files(input_folder)
        
        if not mov_files:
            print("추출할 파일이 없습니다.")
            return []
        
        # 이미 추출된 파일 필터링
        files_to_process = []
        extracted_files = []
        
        if skip_existing:
            for mov_file in mov_files:
                expected_output = output_folder / f"{mov_file.stem}.{self.audio_format}"
                if expected_output.exists():
                    print(f"건너뛰기 (이미 추출됨): {mov_file.name}")
                    extracted_files.append(expected_output)
                else:
                    files_to_process.append(mov_file)
        else:
            files_to_process = mov_files
        
        if not files_to_process:
            print("모든 파일이 이미 추출되었습니다.")
            return extracted_files
        
        # tqdm으로 진행률 표시하며 추출
        print(f"\n총 {len(files_to_process)}개의 파일을 추출합니다...")
        for mov_file in tqdm(files_to_process, desc="오디오 추출 진행"):
            try:
                output_path = self.extract_audio(mov_file, output_folder)
                extracted_files.append(output_path)
            except Exception as e:
                tqdm.write(f"오류 발생 ({mov_file.name}): {e}")
                continue
        
        return extracted_files
