"""
Main script for audio extraction and STT transcription pipeline.
오디오 추출 및 STT 전사 파이프라인의 메인 스크립트입니다.
"""
import sys
from pathlib import Path
from config import Config
from audio_extractor import AudioExtractor
from stt_transcriber import STTTranscriber


def main():
    """메인 실행 함수"""
    # 설정에서 경로 가져오기
    Config.create_directories()
    
    input_folder = Config.INPUT_FOLDER
    audio_output_folder = Config.AUDIO_OUTPUT_FOLDER
    text_output_folder = Config.TEXT_OUTPUT_FOLDER
    whisper_model_type = Config.WHISPER_MODEL_TYPE
    hf_home_path = Config.HF_HOME_PATH
    whisper_model_path = Config.WHISPER_MODEL_PATH
    whisper_model_name = Config.WHISPER_MODEL_NAME
    mlx_model_name = Config.MLX_MODEL_NAME
    audio_format = Config.AUDIO_FORMAT
    sample_rate = Config.AUDIO_SAMPLE_RATE
    
    print("=" * 60)
    print("오디오 추출 및 STT 전사 파이프라인")
    print("=" * 60)
    print(f"입력 폴더: {input_folder}")
    print(f"오디오 출력 폴더: {audio_output_folder}")
    print(f"텍스트 출력 폴더: {text_output_folder}")
    print(f"모델 타입: {whisper_model_type}")
    if whisper_model_type == "mlx":
        print(f"MLX 모델: {mlx_model_name}")
        if hf_home_path:
            print(f"HF_HOME: {hf_home_path}")
    else:
        print(f"OpenAI Whisper 모델: {whisper_model_path or whisper_model_name}")
    print(f"오디오 형식: {audio_format}")
    print("=" * 60)
    print()
    
    # 1단계: 오디오 추출
    print("[1단계] .mov 파일에서 오디오 추출")
    print("-" * 60)
    extractor = AudioExtractor(
        audio_format=audio_format,
        sample_rate=sample_rate
    )
    
    extracted_audio_files = extractor.extract_all(
        input_folder=input_folder,
        output_folder=audio_output_folder,
        skip_existing=True  # 이미 추출된 파일 건너뛰기
    )
    
    if not extracted_audio_files:
        print("추출된 오디오 파일이 없어 전사를 건너뜁니다.")
        return
    
    print(f"\n총 {len(extracted_audio_files)}개의 오디오 파일 준비 완료")
    print()
    
    # 2단계: STT 전사
    print("[2단계] 오디오를 텍스트로 전사")
    print("-" * 60)
    transcriber = STTTranscriber(
        model_type=whisper_model_type,
        model_path=whisper_model_path,
        model_name=whisper_model_name,
        mlx_model_name=mlx_model_name,
        hf_home_path=hf_home_path
    )
    
    extract_srt = Config.EXTRACT_SRT
    
    transcribed_texts = transcriber.transcribe_all(
        audio_files=extracted_audio_files,
        output_folder=text_output_folder,
        language="ko",  # 한국어로 설정 (자동 감지하려면 None)
        skip_existing=True,  # 이미 전사된 파일 건너뛰기
        extract_srt=extract_srt
    )
    
    print(f"\n총 {len(transcribed_texts)}개의 파일 전사 완료")
    print()
    print("=" * 60)
    print("모든 작업이 완료되었습니다!")
    print("=" * 60)


def update_config_from_args():
    """
    명령행 인자로 설정 업데이트
    사용법:
        python main.py --input_folder /path/to/input --whisper_model /path/to/model
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="오디오 추출 및 STT 전사 파이프라인"
    )
    parser.add_argument(
        "--input_folder",
        type=str,
        help=".mov 파일이 있는 입력 폴더 경로"
    )
    parser.add_argument(
        "--audio_output",
        type=str,
        help="추출된 오디오 파일 저장 폴더 경로"
    )
    parser.add_argument(
        "--text_output",
        type=str,
        help="전사된 텍스트 파일 저장 폴더 경로"
    )
    parser.add_argument(
        "--whisper_model_type",
        type=str,
        choices=["openai", "mlx"],
        help="모델 타입 (openai 또는 mlx)"
    )
    parser.add_argument(
        "--hf_home_path",
        type=str,
        help="Hugging Face 홈 디렉토리 경로"
    )
    parser.add_argument(
        "--whisper_model_path",
        type=str,
        help="Whisper 모델 파일 경로"
    )
    parser.add_argument(
        "--whisper_model_name",
        type=str,
        default="base",
        help="OpenAI Whisper 기본 모델 이름 (base, small, medium, large)"
    )
    parser.add_argument(
        "--mlx_model_name",
        type=str,
        choices=["large", "turbo"],
        help="MLX Whisper 모델 이름 (large 또는 turbo)"
    )
    parser.add_argument(
        "--audio_format",
        type=str,
        choices=["mp3", "wav"],
        help="오디오 형식 (mp3 또는 wav)"
    )
    
    args = parser.parse_args()
    
    # 설정 업데이트
    Config.update_paths(
        input_folder=args.input_folder,
        audio_output=args.audio_output,
        text_output=args.text_output,
        whisper_model_type=args.whisper_model_type,
        hf_home_path=args.hf_home_path,
        whisper_model_path=args.whisper_model_path,
        whisper_model_name=args.whisper_model_name,
        mlx_model_name=args.mlx_model_name,
        audio_format=args.audio_format
    )


if __name__ == "__main__":
    # 명령행 인자가 있으면 설정 업데이트
    if len(sys.argv) > 1:
        update_config_from_args()
    
    main()
