"""
단일 파일 STT 전사 테스트 (디버깅용)
"""
import sys
from pathlib import Path
from config import Config
from stt_transcriber import STTTranscriber
import time

def test_single_transcribe():
    """단일 파일만 전사 테스트"""
    Config.create_directories()
    
    audio_output_folder = Config.AUDIO_OUTPUT_FOLDER
    text_output_folder = Config.TEXT_OUTPUT_FOLDER
    whisper_model_type = Config.WHISPER_MODEL_TYPE
    hf_home_path = Config.HF_HOME_PATH
    whisper_model_path = Config.WHISPER_MODEL_PATH
    whisper_model_name = Config.WHISPER_MODEL_NAME
    mlx_model_name = Config.MLX_MODEL_NAME
    
    print("=" * 60)
    print("단일 파일 STT 전사 테스트")
    print("=" * 60)
    
    # 처리되지 않은 wav 파일 찾기
    wav_files = list(audio_output_folder.glob("*.wav"))
    transcribed_files = {f.stem for f in text_output_folder.glob("*.txt")}
    
    files_to_process = [f for f in wav_files if f.stem not in transcribed_files]
    
    if not files_to_process:
        print("처리할 파일이 없습니다.")
        return
    
    # 첫 번째 파일 선택
    test_file = files_to_process[0]
    print(f"\n테스트 파일: {test_file.name}")
    print(f"파일 크기: {test_file.stat().st_size / (1024*1024):.2f} MB")
    print()
    
    # STT 초기화
    print("모델 로딩 중...")
    start_time = time.time()
    
    transcriber = STTTranscriber(
        model_type=whisper_model_type,
        model_path=whisper_model_path,
        model_name=whisper_model_name,
        mlx_model_name=mlx_model_name,
        hf_home_path=hf_home_path
    )
    
    load_time = time.time() - start_time
    print(f"모델 로딩 완료: {load_time:.2f}초\n")
    
    # 전사 시작
    print("전사 시작...")
    print("-" * 60)
    transcribe_start = time.time()
    
    try:
        text = transcriber.transcribe_audio(
            audio_path=test_file,
            output_folder=text_output_folder,
            language="ko"
        )
        
        transcribe_time = time.time() - transcribe_start
        
        print("-" * 60)
        print(f"\n전사 완료!")
        print(f"처리 시간: {transcribe_time:.2f}초 ({transcribe_time/60:.1f}분)")
        print(f"텍스트 길이: {len(text)} 문자")
        print(f"결과: {text_output_folder / test_file.stem}.txt")
        
    except Exception as e:
        import traceback
        print(f"\n오류 발생: {e}")
        print("\n상세 에러:")
        traceback.print_exc()

if __name__ == "__main__":
    test_single_transcribe()
