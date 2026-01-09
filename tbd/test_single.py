"""
테스트용 스크립트 - 단일 파일 처리
"""
import sys
from pathlib import Path
from config import Config
from audio_extractor import AudioExtractor
from stt_transcriber import STTTranscriber


def test_single_file():
    """첫 번째 .mov 파일 하나만 테스트 처리"""
    # 설정 준비
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
    print("테스트: 단일 파일 처리")
    print("=" * 60)
    print(f"입력 폴더: {input_folder}")
    print(f"오디오 출력 폴더: {audio_output_folder}")
    print(f"텍스트 출력 폴더: {text_output_folder}")
    print(f"모델 타입: {whisper_model_type}")
    if whisper_model_type == "mlx":
        print(f"MLX 모델: {mlx_model_name}")
        if hf_home_path:
            print(f"HF_HOME: {hf_home_path}")
    print("=" * 60)
    print()
    
    # 1단계: .mov 파일 찾기 (첫 번째 파일만)
    print("[1단계] .mov 파일 찾기")
    print("-" * 60)
    extractor = AudioExtractor(
        audio_format=audio_format,
        sample_rate=sample_rate
    )
    
    mov_files = extractor.find_mov_files(input_folder)
    
    if not mov_files:
        print("추출할 파일이 없습니다.")
        return
    
    # 파일 목록 출력
    print(f"발견된 .mov 파일: {len(mov_files)}개")
    for i, f in enumerate(mov_files[:5], 1):
        print(f"  {i}. {f.name}")
    print()
    
    # 첫 번째 파일부터 시도 (실패 시 다음 파일)
    extracted_audio = None
    for test_file in mov_files:
        print(f"시도 중: {test_file.name}")
        print()
        
        # 2단계: 오디오 추출
        print("[2단계] 오디오 추출")
        print("-" * 60)
        try:
            extracted_audio = extractor.extract_audio(
                video_path=test_file,
                output_folder=audio_output_folder
            )
            print(f"오디오 추출 완료: {extracted_audio}")
            print()
            break  # 성공하면 루프 종료
        except Exception as e:
            print(f"오디오 추출 실패: {e}")
            print("다음 파일로 시도합니다...\n")
            continue
    
    if extracted_audio is None:
        print("모든 파일 추출 실패")
        return
    
    # 3단계: STT 전사
    print("[3단계] STT 전사")
    print("-" * 60)
    try:
        transcriber = STTTranscriber(
            model_type=whisper_model_type,
            model_path=whisper_model_path,
            model_name=whisper_model_name,
            mlx_model_name=mlx_model_name,
            hf_home_path=hf_home_path
        )
        
        text = transcriber.transcribe_audio(
            audio_path=extracted_audio,
            output_folder=text_output_folder,
            language="ko"
        )
        
        print(f"\n전사 완료!")
        print(f"텍스트 길이: {len(text)} 문자")
        print()
        
    except Exception as e:
        print(f"전사 실패: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("=" * 60)
    print("테스트 완료!")
    print(f"결과 파일: {text_output_folder}")
    print("=" * 60)


if __name__ == "__main__":
    test_single_file()
