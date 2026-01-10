"""
이미 전사된 파일들에 대해 SRT 파일 생성 스크립트
"""
import sys
from pathlib import Path
from config import Config
from stt_transcriber import STTTranscriber
from tqdm import tqdm

def main():
    """SRT 파일 생성"""
    Config.create_directories()
    
    audio_folder = Config.AUDIO_OUTPUT_FOLDER
    text_folder = Config.TEXT_OUTPUT_FOLDER
    
    # STT Transcriber 초기화
    transcriber = STTTranscriber(
        model_type=Config.WHISPER_MODEL_TYPE,
        model_path=Config.WHISPER_MODEL_PATH,
        model_name=Config.WHISPER_MODEL_NAME,
        mlx_model_name=Config.MLX_MODEL_NAME,
        hf_home_path=Config.HF_HOME_PATH
    )
    
    # .wav 파일 찾기
    wav_files = list(audio_folder.glob("*.wav"))
    
    if not wav_files:
        print("처리할 오디오 파일이 없습니다.")
        return
    
    # txt 파일은 있지만 SRT 파일이 없는 파일 찾기
    files_to_process = []
    for wav_file in wav_files:
        txt_file = text_folder / f"{wav_file.stem}.txt"
        srt_file = text_folder / f"{wav_file.stem}_SRT.srt"
        
        if txt_file.exists() and not srt_file.exists():
            files_to_process.append(wav_file)
    
    if not files_to_process:
        print("모든 파일에 SRT 파일이 이미 존재합니다.")
        return
    
    print(f"SRT 파일 생성 대상: {len(files_to_process)}개 파일")
    print("=" * 60)
    
    # SRT 파일 생성 (word_timestamps=True로 재전사)
    for wav_file in tqdm(files_to_process, desc="SRT 파일 생성", unit="파일"):
        try:
            print(f"\n처리 중: {wav_file.name}")
            
            # word_timestamps=True로 재전사하여 SRT 생성
            transcriber.transcribe_audio(
                audio_path=wav_file,
                output_folder=text_folder,
                language="ko",
                extract_srt=True  # SRT 파일 생성
            )
            
            srt_file = text_folder / f"{wav_file.stem}_SRT.srt"
            if srt_file.exists():
                print(f"✓ 완료: {srt_file.name}")
            else:
                print(f"✗ 경고: SRT 파일이 생성되지 않았습니다: {wav_file.name}")
                
        except Exception as e:
            print(f"✗ 오류 ({wav_file.name}): {e}")
            continue
    
    print("\n" + "=" * 60)
    print("SRT 파일 생성 완료!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
