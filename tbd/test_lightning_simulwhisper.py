"""
Lightning-SimulWhisper 성능 및 기능 테스트 스크립트
기존 MLX Whisper와 Lightning-SimulWhisper 비교 테스트
"""
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from stt_transcriber import STTTranscriber
from stt_lightning_simulwhisper import LightningSimulWhisperTranscriber


class PerformanceComparison:
    """성능 비교 테스트 클래스"""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
    
    def test_single_file(
        self,
        audio_path: Path,
        output_base_folder: Path,
        test_name: Optional[str] = None
    ):
        """
        단일 파일로 두 엔진 비교 테스트
        
        Args:
            audio_path: 테스트할 오디오 파일 경로
            output_base_folder: 출력 폴더 (하위에 mlx, lightning 폴더 생성)
            test_name: 테스트 이름 (None이면 파일명 사용)
        """
        if not audio_path.exists():
            print(f"오류: 오디오 파일을 찾을 수 없습니다: {audio_path}")
            return
        
        test_name = test_name or audio_path.stem
        print("\n" + "=" * 80)
        print(f"테스트: {test_name}")
        print(f"파일: {audio_path.name}")
        print("=" * 80)
        
        # 출력 폴더 설정
        mlx_output = output_base_folder / "mlx_whisper"
        lightning_output = output_base_folder / "lightning_simulwhisper"
        mlx_output.mkdir(parents=True, exist_ok=True)
        lightning_output.mkdir(parents=True, exist_ok=True)
        
        results = {
            "audio_file": audio_path.name,
            "file_size_mb": audio_path.stat().st_size / (1024 * 1024),
            "mlx": {},
            "lightning": {}
        }
        
        # 1. MLX Whisper 테스트
        print("\n[1/2] MLX Whisper 테스트 시작...")
        try:
            mlx_transcriber = STTTranscriber(
                model_type="mlx",
                mlx_model_name=Config.MLX_MODEL_NAME,
                hf_home_path=Config.HF_HOME_PATH
            )
            
            start_time = time.time()
            mlx_text = mlx_transcriber.transcribe_audio(
                audio_path=audio_path,
                output_folder=mlx_output,
                language="ko",
                extract_srt=Config.EXTRACT_SRT
            )
            mlx_time = time.time() - start_time
            
            results["mlx"] = {
                "success": True,
                "time_seconds": mlx_time,
                "text_length": len(mlx_text),
                "output_path": mlx_output / f"{audio_path.stem}.txt"
            }
            print(f"  ✓ 완료: {mlx_time:.2f}초, {len(mlx_text)} 문자")
            
        except Exception as e:
            results["mlx"] = {
                "success": False,
                "error": str(e)
            }
            print(f"  ✗ 실패: {e}")
        
        # 2. Lightning-SimulWhisper 테스트
        print("\n[2/2] Lightning-SimulWhisper 테스트 시작...")
        try:
            lightning_transcriber = LightningSimulWhisperTranscriber(
                model_name=Config.LIGHTNING_SIMUL_MODEL_NAME,
                model_path=Config.LIGHTNING_SIMUL_MODEL_PATH,
                use_coreml=Config.LIGHTNING_SIMUL_USE_COREML,
                language="ko",
                hf_home_path=Config.HF_HOME_PATH
            )
            
            start_time = time.time()
            lightning_text = lightning_transcriber.transcribe_audio(
                audio_path=audio_path,
                output_folder=lightning_output,
                language="ko",
                extract_srt=Config.EXTRACT_SRT
            )
            lightning_time = time.time() - start_time
            
            results["lightning"] = {
                "success": True,
                "time_seconds": lightning_time,
                "text_length": len(lightning_text),
                "output_path": lightning_output / f"{audio_path.stem}.txt"
            }
            print(f"  ✓ 완료: {lightning_time:.2f}초, {len(lightning_text)} 문자")
            
        except Exception as e:
            results["lightning"] = {
                "success": False,
                "error": str(e)
            }
            print(f"  ✗ 실패: {e}")
        
        # 3. 성능 비교
        if results["mlx"].get("success") and results["lightning"].get("success"):
            mlx_time = results["mlx"]["time_seconds"]
            lightning_time = results["lightning"]["time_seconds"]
            speedup = mlx_time / lightning_time if lightning_time > 0 else 0
            
            print("\n" + "-" * 80)
            print("성능 비교 결과:")
            print(f"  MLX Whisper:          {mlx_time:.2f}초")
            print(f"  Lightning-SimulWhisper: {lightning_time:.2f}초")
            print(f"  속도 향상:            {speedup:.2f}x {'(Lightning이 빠름)' if speedup > 1 else '(MLX가 빠름)'}")
            
            # 텍스트 길이 비교
            mlx_len = results["mlx"]["text_length"]
            lightning_len = results["lightning"]["text_length"]
            len_diff = abs(mlx_len - lightning_len)
            print(f"\n텍스트 길이:")
            print(f"  MLX Whisper:          {mlx_len} 문자")
            print(f"  Lightning-SimulWhisper: {lightning_len} 문자")
            print(f"  차이:                 {len_diff} 문자")
        
        self.results[test_name] = results
        return results
    
    def test_multiple_files(
        self,
        audio_files: List[Path],
        output_base_folder: Path
    ):
        """
        여러 파일로 일괄 비교 테스트
        
        Args:
            audio_files: 테스트할 오디오 파일 경로 리스트
            output_base_folder: 출력 폴더
        """
        print(f"\n{'=' * 80}")
        print(f"일괄 비교 테스트 시작: {len(audio_files)}개 파일")
        print(f"{'=' * 80}\n")
        
        for idx, audio_file in enumerate(audio_files, 1):
            print(f"\n[{idx}/{len(audio_files)}]")
            self.test_single_file(audio_file, output_base_folder)
        
        # 전체 통계
        self.print_summary()
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 80)
        print("전체 테스트 결과 요약")
        print("=" * 80)
        
        total_tests = len(self.results)
        successful_both = sum(
            1 for r in self.results.values()
            if r["mlx"].get("success") and r["lightning"].get("success")
        )
        
        print(f"\n총 테스트: {total_tests}개")
        print(f"양쪽 모두 성공: {successful_both}개")
        
        if successful_both > 0:
            mlx_times = [
                r["mlx"]["time_seconds"]
                for r in self.results.values()
                if r["mlx"].get("success")
            ]
            lightning_times = [
                r["lightning"]["time_seconds"]
                for r in self.results.values()
                if r["lightning"].get("success")
            ]
            
            avg_speedup = sum(
                r["mlx"]["time_seconds"] / r["lightning"]["time_seconds"]
                for r in self.results.values()
                if r["mlx"].get("success") and r["lightning"].get("success") and r["lightning"]["time_seconds"] > 0
            ) / successful_both
            
            print(f"\n평균 처리 시간:")
            if mlx_times:
                print(f"  MLX Whisper:          {sum(mlx_times)/len(mlx_times):.2f}초")
            if lightning_times:
                print(f"  Lightning-SimulWhisper: {sum(lightning_times)/len(lightning_times):.2f}초")
            print(f"\n평균 속도 향상: {avg_speedup:.2f}x")


def main():
    """메인 테스트 함수"""
    print("=" * 80)
    print("Lightning-SimulWhisper vs MLX Whisper 성능 비교 테스트")
    print("=" * 80)
    
    # 설정 확인
    if not Config.LIGHTNING_SIMUL_WHISPER_ENABLED:
        print("\n경고: Config.LIGHTNING_SIMUL_WHISPER_ENABLED가 False로 설정되어 있습니다.")
        print("테스트를 진행하려면 config.py에서 True로 변경하세요.")
        response = input("그래도 계속하시겠습니까? (y/n): ")
        if response.lower() != 'y':
            return
    
    # 테스트 파일 선택
    audio_folder = Config.AUDIO_OUTPUT_FOLDER
    if not audio_folder.exists():
        print(f"오류: 오디오 폴더를 찾을 수 없습니다: {audio_folder}")
        return
    
    # 사용 가능한 오디오 파일 목록
    audio_files = list(audio_folder.glob("*.wav"))
    if not audio_files:
        print(f"오류: {audio_folder}에 .wav 파일이 없습니다.")
        return
    
    print(f"\n사용 가능한 오디오 파일: {len(audio_files)}개")
    
    # 단일 파일 테스트 또는 일괄 테스트 선택
    if len(sys.argv) > 1:
        # 명령행 인자로 파일 지정
        test_file = Path(sys.argv[1])
        if not test_file.exists():
            print(f"오류: 파일을 찾을 수 없습니다: {test_file}")
            return
        
        comparator = PerformanceComparison()
        output_folder = project_root / "test_output"
        comparator.test_single_file(test_file, output_folder)
    else:
        # 대화형 선택
        print("\n테스트 방법 선택:")
        print("1. 단일 파일 테스트")
        print("2. 여러 파일 일괄 테스트 (처음 3개)")
        print("3. 모든 파일 테스트")
        
        choice = input("\n선택 (1/2/3): ").strip()
        
        comparator = PerformanceComparison()
        output_folder = project_root / "test_output"
        
        if choice == "1":
            # 파일 목록 표시
            print("\n사용 가능한 파일:")
            for idx, f in enumerate(audio_files[:10], 1):
                size_mb = f.stat().st_size / (1024 * 1024)
                print(f"  {idx}. {f.name} ({size_mb:.1f} MB)")
            
            file_idx = int(input("\n파일 번호 선택: ")) - 1
            if 0 <= file_idx < len(audio_files):
                comparator.test_single_file(audio_files[file_idx], output_folder)
            else:
                print("잘못된 번호입니다.")
        
        elif choice == "2":
            comparator.test_multiple_files(audio_files[:3], output_folder)
        
        elif choice == "3":
            confirm = input(f"\n{len(audio_files)}개 파일을 모두 테스트합니다. 계속하시겠습니까? (y/n): ")
            if confirm.lower() == 'y':
                comparator.test_multiple_files(audio_files, output_folder)
        
        else:
            print("잘못된 선택입니다.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
