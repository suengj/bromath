"""
YouTube audio downloader module.
YouTube에서 오디오를 다운로드하는 모듈입니다.
p03_speech2text의 stt_function_v2.py를 참고하여 작성되었습니다.
"""
import os
import re
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs
from pytubefix import YouTube


class YouTubeDownloader:
    """YouTube 오디오 다운로더 클래스"""
    
    def __init__(self, download_path: Path, proxy: Optional[dict] = None):
        """
        YouTubeDownloader 초기화
        
        Args:
            download_path: 다운로드한 파일을 저장할 폴더 경로
            proxy: 프록시 설정 (None이면 사용 안 함)
        """
        self.download_path = Path(download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.proxy = proxy
    
    @staticmethod
    def sanitize_filename(filename: str, replacement: str = "_", max_length: int = 100) -> str:
        """
        파일명을 안전하게 변경합니다.
        
        Args:
            filename: 원본 파일명
            replacement: 특수문자 대체 문자
            max_length: 최대 길이
            
        Returns:
            정제된 파일명
        """
        # 확장자 분리
        if "." in filename:
            base_name, extension = filename.rsplit(".", 1)
        else:
            base_name, extension = filename, ""
        
        # 특수문자 제거
        invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
        sanitized = re.sub(invalid_chars, replacement, base_name)
        
        # 앞뒤 공백 및 점 제거
        sanitized = sanitized.strip(" ").rstrip(".")
        
        # 길이 제한
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # 확장자와 결합
        if extension:
            return f"{sanitized}.{extension}"
        
        return sanitized
    
    @staticmethod
    def extract_youtube_id(url: str) -> str:
        """
        YouTube URL에서 비디오 ID를 추출합니다.
        
        Args:
            url: YouTube URL
            
        Returns:
            비디오 ID
        """
        parsed_url = urlparse(url)
        
        # 'youtu.be' 단축 링크 처리
        if parsed_url.netloc == "youtu.be":
            return parsed_url.path[1:]  # Video ID is in the path
        
        # 'youtube.com' 링크 처리
        if parsed_url.netloc in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
            query_params = parse_qs(parsed_url.query)
            video_id = query_params.get("v", [None])[0]
            if video_id:
                return video_id
        
        raise ValueError(f"Invalid YouTube URL: {url}")
    
    def download_audio(
        self,
        url: str,
        convert_to_wav: bool = False
    ) -> Optional[Tuple[str, str, str, int, str, str]]:
        """
        YouTube에서 오디오를 다운로드합니다.
        
        Args:
            url: YouTube URL
            convert_to_wav: True이면 wav 형식으로 변환 (extracted_audio와 동일한 형식)
            
        Returns:
            (full_saved_path, filename, video_id, video_len, channel_id, channel_url)
            실패 시 None
        """
        try:
            # YouTube 객체 생성
            if self.proxy:
                yt = YouTube(url, proxies=self.proxy)
            else:
                yt = YouTube(url)
            
            # 비디오 정보
            video_id = self.extract_youtube_id(url)
            video_len = yt.length if yt.length else 0
            channel_id = yt.channel_id if hasattr(yt, 'channel_id') else "unknown"
            channel_url = yt.channel_url if hasattr(yt, 'channel_url') else "unknown"
            
            # 오디오 스트림 가져오기
            audio_stream = yt.streams.get_audio_only()
            
            # 파일명 정제
            original_filename = audio_stream.default_filename
            filename = self.sanitize_filename(original_filename)
            
            # 다운로드
            print(f"다운로드 중: {yt.title}")
            audio_stream.download(output_path=str(self.download_path), filename=filename)
            
            full_saved_path = str(self.download_path / filename)
            
            # wav로 변환 요청된 경우
            if convert_to_wav and not filename.lower().endswith('.wav'):
                from audio_extractor import AudioExtractor
                wav_path = Path(full_saved_path).with_suffix('.wav')
                extractor = AudioExtractor(audio_format="wav")
                try:
                    extractor.extract_audio(
                        video_path=Path(full_saved_path),
                        output_folder=self.download_path
                    )
                    # 원본 파일 삭제 (선택적)
                    # Path(full_saved_path).unlink()
                    filename = wav_path.name
                    full_saved_path = str(wav_path)
                except Exception as e:
                    print(f"WAV 변환 실패 (원본 파일 유지): {e}")
            
            print(f"다운로드 완료: {filename}")
            
            return (full_saved_path, filename, video_id, video_len, channel_id, channel_url)
            
        except Exception as e:
            print(f"다운로드 실패 ({url}): {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def download_from_csv(
        self,
        csv_path: Path,
        url_column: str = "url",
        convert_to_wav: bool = False,
        skip_existing: bool = True
    ) -> list:
        """
        CSV 파일에서 URL 목록을 읽어서 다운로드합니다.
        
        Args:
            csv_path: CSV 파일 경로
            url_column: URL이 있는 컬럼명
            convert_to_wav: True이면 wav 형식으로 변환
            skip_existing: True이면 이미 다운로드된 파일 건너뛰기
            
        Returns:
            다운로드 성공한 파일 정보 리스트
        """
        import pandas as pd
        
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
        
        # CSV 읽기
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
        except:
            try:
                df = pd.read_csv(csv_path, encoding='cp949')
            except:
                raise ValueError(f"CSV 파일을 읽을 수 없습니다: {csv_path}")
        
        if url_column not in df.columns:
            raise ValueError(f"CSV에 '{url_column}' 컬럼이 없습니다. 사용 가능한 컬럼: {df.columns.tolist()}")
        
        urls = df[url_column].dropna().tolist()
        print(f"총 {len(urls)}개의 URL을 처리합니다.")
        
        downloaded_files = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] {url}")
            
            # 이미 다운로드된 파일 확인
            if skip_existing:
                try:
                    video_id = self.extract_youtube_id(url)
                    # 간단한 체크: video_id로 시작하는 파일이 있는지 확인
                    existing_files = list(self.download_path.glob(f"*{video_id}*"))
                    if existing_files:
                        print(f"이미 다운로드된 파일이 있습니다: {existing_files[0].name}")
                        continue
                except:
                    pass  # URL 파싱 실패 시 계속 진행
            
            # 다운로드
            result = self.download_audio(url, convert_to_wav=convert_to_wav)
            
            if result:
                downloaded_files.append(result)
        
        return downloaded_files
