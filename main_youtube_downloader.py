"""
Main script for YouTube audio downloader.
YouTube에서 오디오를 다운로드하는 메인 스크립트입니다.
"""
import sys
from pathlib import Path
from config import Config
from youtube_downloader import YouTubeDownloader


def main():
    """메인 실행 함수"""
    # 설정 준비
    Config.create_directories()
    
    input_df_path = Config.INPUT_DF_PATH
    clips_folder = Config.CLIPS_OUTPUT_FOLDER
    
    print("=" * 60)
    print("YouTube 오디오 다운로더")
    print("=" * 60)
    print(f"입력 CSV: {input_df_path}")
    print(f"출력 폴더: {clips_folder}")
    print("=" * 60)
    print()
    
    # CSV 파일이 없으면 생성
    if not input_df_path.exists():
        print(f"CSV 파일이 없습니다. 샘플 파일을 생성합니다: {input_df_path}")
        import pandas as pd
        
        # 샘플 데이터
        sample_data = {
            'date': [],
            'url': [],
            'category': []
        }
        
        df = pd.DataFrame(sample_data)
        df.to_csv(input_df_path, index=False, encoding='utf-8-sig')
        print(f"샘플 CSV 파일이 생성되었습니다. {input_df_path}에 URL을 추가하세요.")
        print("\nCSV 형식:")
        print("date,url,category")
        print("2025-01-01,https://www.youtube.com/watch?v=VIDEO_ID,수학")
        return
    
    # YouTubeDownloader 초기화
    # proxy는 필요시 설정 (기본값: None)
    proxy = None  # {"http": "socks5://proxy_address", "https": "socks5://proxy_address"}
    
    downloader = YouTubeDownloader(
        download_path=clips_folder,
        proxy=proxy
    )
    
    # CSV에서 다운로드
    # convert_to_wav=True로 설정하면 extracted_audio와 동일한 wav 형식으로 저장
    downloaded_files = downloader.download_from_csv(
        csv_path=input_df_path,
        url_column="url",
        convert_to_wav=True,  # extracted_audio와 동일한 형식
        skip_existing=True
    )
    
    print()
    print("=" * 60)
    print(f"다운로드 완료: {len(downloaded_files)}개 파일")
    print(f"저장 위치: {clips_folder}")
    print("=" * 60)


def download_single_url(url: str):
    """단일 URL 다운로드 테스트"""
    Config.create_directories()
    
    clips_folder = Config.CLIPS_OUTPUT_FOLDER
    
    print("=" * 60)
    print("단일 URL 다운로드 테스트")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"출력 폴더: {clips_folder}")
    print("=" * 60)
    print()
    
    downloader = YouTubeDownloader(
        download_path=clips_folder,
        proxy=None
    )
    
    result = downloader.download_audio(url, convert_to_wav=True)
    
    if result:
        full_path, filename, video_id, video_len, channel_id, channel_url = result
        print(f"\n다운로드 성공!")
        print(f"파일: {filename}")
        print(f"비디오 ID: {video_id}")
        print(f"길이: {video_len}초")
    else:
        print("\n다운로드 실패")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # URL을 인자로 받으면 단일 다운로드
        url = sys.argv[1]
        download_single_url(url)
    else:
        # CSV 파일에서 일괄 다운로드
        main()
