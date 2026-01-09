"""
작은 파일로 STT 전사 테스트
"""
import sys
from pathlib import Path
from config import Config
from stt_transcriber import STTTranscriber
import time

def find_smallest_wav():
    """가장 작은 wav 파일 찾기"""
    audio_output_folder = Config.AUDIO_OUTPUT_FOLDER
    text_output_folder = Config.TEXT_OUTPUT_FOLDER
    
    wav_files = list(audio_output_folder.glob("*.wav"))
    transcribed_files = {f.stem for f in text_output_folder.glob("*.txt")}
    
    files_to_process = [(f, f.stat().st_size) for f in wav_files if f.stem not in transcribed_files]
    
    if not files_to_process:
        print("처리할 파일이 없습니다.")
        return None
    
    # 가장 작은 파일 선택
    files_to_process.sort(key=lambda x: x[1])
    smallest_file, size_mb = files_to_process[0]
    
    print(f"가장 작은 파일: {smallest_file.name}")
    print(f"크기: {size_mb / (1024*1024):.2f} MB")
    print()
    
    return smallest_file

def test_small_file():
    """작은 파일로 테스트"""
    Config.create_directories()
    
    text_output_folder = Config.TEXT_OUTPUT_FOLDER
    whisper_model_type = Config.WHISPER_MODEL_TYPE
    hf_home_path = Config.HF_HOME_PATH
    whisper_model_path = Config.WHISPER_MODEL_PATH
    whisper_model_name = Config.WHISPER_MODEL_NAME
    mlx_model_name = Config.MLX_MODEL_NAME
    
    print("=" * 60)
    print("작은 파일 STT 전사 테스트")
    print("=" * 60)
    
    test_file = find_smallest_wav()
    if not test_file:
        return
    
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
        print(f"\n✓ 전사 완료!")
        print(f"  처리 시간: {transcribe_time:.2f}초 ({transcribe_time/60:.1f}분)")
        print(f"  텍스트 길이: {len(text)} 문자")
        print(f"  결과 파일: {text_output_folder / test_file.stem}.txt")
        
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        import traceback
        elapsed = time.time() - transcribe_start
        print(f"\n✗ 오류 발생 (경과 시간: {elapsed:.1f}초)")
        print(f"  에러: {e}")
        print("\n상세:")
        traceback.print_exc()

if __name__ == "__main__":
    test_small_file()
