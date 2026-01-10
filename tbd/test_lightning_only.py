"""
Lightning-SimulWhisper 단독 테스트 스크립트
MLX Whisper 없이 Lightning-SimulWhisper만 테스트
"""
import sys
import time
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from stt_lightning_simulwhisper import LightningSimulWhisperTranscriber


def test_lightning_only(audio_path: Path):
    """Lightning-SimulWhisper만 테스트"""
    if not audio_path.exists():
        print(f"오류: 오디오 파일을 찾을 수 없습니다: {audio_path}")
        return
    
    print("=" * 80)
    print("Lightning-SimulWhisper 단독 테스트")
    print("=" * 80)
    print(f"파일: {audio_path.name}")
    print(f"크기: {audio_path.stat().st_size / (1024 * 1024):.1f} MB")
    print("=" * 80)
    
    # 출력 폴더 설정
    output_folder = project_root / "test_output" / "lightning_simulwhisper"
    output_folder.mkdir(parents=True, exist_ok=True)
    
    try:
        print("\nLightning-SimulWhisper 트랜스크라이버 초기화 중...")
        transcriber = LightningSimulWhisperTranscriber(
            model_name=Config.LIGHTNING_SIMUL_MODEL_NAME,
            model_path=Config.LIGHTNING_SIMUL_MODEL_PATH,
            use_coreml=Config.LIGHTNING_SIMUL_USE_COREML,
            language="ko",
            hf_home_path=Config.HF_HOME_PATH
        )
        
        print("\n전사 시작...")
        start_time = time.time()
        
        text = transcriber.transcribe_audio(
            audio_path=audio_path,
            output_folder=output_folder,
            language="ko",
            extract_srt=Config.EXTRACT_SRT
        )
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "-" * 80)
        print("테스트 완료!")
        print(f"처리 시간: {elapsed_time:.2f}초")
        print(f"텍스트 길이: {len(text)} 문자")
        print(f"출력 파일: {output_folder / audio_path.stem}.txt")
        print("-" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    # 테스트 파일 선택
    audio_folder = Config.AUDIO_OUTPUT_FOLDER
    if not audio_folder.exists():
        print(f"오류: 오디오 폴더를 찾을 수 없습니다: {audio_folder}")
        return
    
    audio_files = list(audio_folder.glob("*.wav"))
    if not audio_files:
        print(f"오류: {audio_folder}에 .wav 파일이 없습니다.")
        return
    
    if len(sys.argv) > 1:
        # 명령행 인자로 파일 지정
        test_file = Path(sys.argv[1])
        if not test_file.exists():
            test_file = audio_folder / sys.argv[1]
        test_lightning_only(test_file)
    else:
        # 첫 번째 파일로 테스트
        print(f"사용 가능한 오디오 파일: {len(audio_files)}개")
        print(f"\n첫 번째 파일로 테스트: {audio_files[0].name}\n")
        test_lightning_only(audio_files[0])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
