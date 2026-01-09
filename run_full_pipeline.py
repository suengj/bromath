"""
전체 파이프라인 실행 스크립트
(1) record_text_raw → structured (.md/.html)
(2) extracted_audio → transcribed (.txt) → structured (.md/.html)
각 단계별 완료 상태를 log.csv에 기록
"""
import sys
import csv
import time
from pathlib import Path
from datetime import datetime
from config import Config
from text_processor import TextProcessor
from stt_transcriber import STTTranscriber
from main_record_processor import build_record_prompt
from main_text_processor import main as process_transcribed_texts


class PipelineLogger:
    """파이프라인 진행 상황 로거"""
    
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.records = {}
        self._load_existing_log()
    
    def _load_existing_log(self):
        """기존 로그 파일 읽기"""
        if self.log_path.exists():
            try:
                with open(self.log_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        filename = row['filename']
                        self.records[filename] = {
                            'extracted_audio': row.get('extracted_audio', ''),
                            'record_text_raw': row.get('record_text_raw', ''),
                            'transcribed': row.get('transcribed', ''),
                            'structured': row.get('structured', '')
                        }
            except Exception as e:
                print(f"기존 로그 파일 읽기 오류 (새로 시작): {e}")
                self.records = {}
    
    def mark_complete(self, filename: str, stage: str):
        """단계 완료 표시"""
        if filename not in self.records:
            self.records[filename] = {
                'extracted_audio': '',
                'record_text_raw': '',
                'transcribed': '',
                'structured': ''
            }
        self.records[filename][stage] = 'O'
    
    def save(self):
        """로그 파일 저장"""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.log_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'extracted_audio', 'record_text_raw', 
                           'transcribed', 'structured'])
            
            for filename in sorted(self.records.keys()):
                record = self.records[filename]
                writer.writerow([
                    filename,
                    record.get('extracted_audio', ''),
                    record.get('record_text_raw', ''),
                    record.get('transcribed', ''),
                    record.get('structured', '')
                ])


def process_record_texts(logger: PipelineLogger):
    """(1) record_text_raw 폴더의 .txt 파일들을 .md/.html로 변환"""
    print("\n" + "=" * 60)
    print("[1단계] record_text_raw → structured (.md/.html)")
    print("=" * 60)
    
    Config.create_directories()
    
    record_folder = Config.RECORD_TEXT_RAW_FOLDER
    output_folder = Config.STRUCTURED_OUTPUT_FOLDER
    api_key_path = Config.API_KEY_PATH
    api_key_file = Config.OPENAI_API_KEY_FILE
    model = Config.GPT_MODEL
    
    # 레코드 텍스트용 프롬프트 구성
    (context_query, main_query, additional_query, 
     math_specific_query, example_query, tone_query) = build_record_prompt()
    
    token_range = Config.TOKEN_RANGE
    language = Config.LANGUAGE
    style = Config.OUTPUT_STYLE
    save_html = Config.SAVE_HTML
    html_template = Config.HTML_TEMPLATE
    
    # TextProcessor 초기화
    try:
        processor = TextProcessor(
            api_key_path=api_key_path if api_key_path else None,
            api_key_file=api_key_file,
            model=model
        )
    except Exception as e:
        print(f"초기화 실패: {e}")
        return False
    
    # 모든 .txt 파일 찾기
    text_files = processor.find_text_files(record_folder)
    
    if not text_files:
        print("처리할 파일이 없습니다.")
        return True
    
    print(f"총 {len(text_files)}개의 파일을 처리합니다.\n")
    
    processed_count = 0
    for text_file in text_files:
        try:
            # 이미 처리된 파일 확인
            base_name = text_file.stem
            existing_md = list(output_folder.glob(f"*_{base_name}.md"))
            
            if existing_md:
                print(f"건너뛰기 (이미 처리됨): {text_file.name}")
                logger.mark_complete(text_file.name, 'record_text_raw')
                logger.mark_complete(text_file.name, 'structured')
                continue
            
            # process_single_file 내부에서 메시지 출력하므로 여기서는 출력하지 않음
            result = processor.process_single_file(
                text_file=text_file,
                output_folder=output_folder,
                context_query=context_query,
                main_query=main_query,
                additional_query=additional_query,
                math_specific_query=math_specific_query,
                example_query=example_query,
                tone_query=tone_query,
                token_range=token_range,
                language=language,
                style=style,
                save_html=save_html,
                html_template=html_template
            )
            
            if result:
                logger.mark_complete(text_file.name, 'record_text_raw')
                logger.mark_complete(text_file.name, 'structured')
                processed_count += 1
                logger.save()  # 중간 저장
                print(f"✓ 완료: {text_file.name}\n")
            else:
                print(f"✗ 실패: {text_file.name}\n")
                
        except Exception as e:
            print(f"✗ 오류 ({text_file.name}): {e}\n")
            continue
    
    print(f"\n[1단계 완료] {processed_count}개 파일 처리")
    logger.save()
    return True


def process_audio_files(logger: PipelineLogger):
    """(2) extracted_audio의 .wav 파일들을 transcribed → structured로 변환"""
    print("\n" + "=" * 60)
    print("[2단계] extracted_audio → transcribed → structured")
    print("=" * 60)
    
    Config.create_directories()
    
    audio_folder = Config.AUDIO_OUTPUT_FOLDER
    text_folder = Config.TEXT_OUTPUT_FOLDER
    structured_folder = Config.STRUCTURED_OUTPUT_FOLDER
    
    # 2-1: 오디오 → 텍스트 전사
    print("\n[2-1] 오디오 → 텍스트 전사")
    print("-" * 60)
    
    whisper_model_type = Config.WHISPER_MODEL_TYPE
    hf_home_path = Config.HF_HOME_PATH
    whisper_model_path = Config.WHISPER_MODEL_PATH
    whisper_model_name = Config.WHISPER_MODEL_NAME
    mlx_model_name = Config.MLX_MODEL_NAME
    
    # STT Transcriber 초기화
    transcriber = STTTranscriber(
        model_type=whisper_model_type,
        model_path=whisper_model_path,
        model_name=whisper_model_name,
        mlx_model_name=mlx_model_name,
        hf_home_path=hf_home_path
    )
    
    # .wav 파일 찾기
    wav_files = list(audio_folder.glob("*.wav"))
    
    if not wav_files:
        print("처리할 오디오 파일이 없습니다.")
        return True
    
    # 모든 wav 파일에 대해 extracted_audio 단계 완료 표시
    for wav_file in wav_files:
        logger.mark_complete(wav_file.name, 'extracted_audio')
    
    # 이미 전사된 파일 필터링
    files_to_transcribe = []
    for wav_file in wav_files:
        expected_txt = text_folder / f"{wav_file.stem}.txt"
        if expected_txt.exists():
            print(f"건너뛰기 (이미 전사됨): {wav_file.name}")
            logger.mark_complete(wav_file.name, 'transcribed')
        else:
            files_to_transcribe.append(wav_file)
    
    if files_to_transcribe:
        # transcribe_all 내부에서 메시지를 출력하므로 여기서는 출력하지 않음
        transcribed_texts = transcriber.transcribe_all(
            audio_files=files_to_transcribe,
            output_folder=text_folder,
            language="ko",
            skip_existing=False  # 이미 필터링했으므로
        )
        
        # 로그 업데이트
        for wav_file in files_to_transcribe:
            expected_txt = text_folder / f"{wav_file.stem}.txt"
            if expected_txt.exists():
                logger.mark_complete(wav_file.name, 'transcribed')
        
        logger.save()
        print(f"\n전사 완료: {len(transcribed_texts)}개 파일")
    else:
        print("모든 파일이 이미 전사되었습니다.")
    
    # 2-2: 전사된 텍스트 → structured
    print("\n[2-2] 전사된 텍스트 → structured (.md/.html)")
    print("-" * 60)
    
    # 전사된 텍스트 파일들을 structured로 변환
    text_files = list(text_folder.glob("*.txt"))
    
    if not text_files:
        print("처리할 텍스트 파일이 없습니다.")
        return True
    
    # 이미 처리된 파일 필터링
    files_to_structure = []
    for txt_file in text_files:
        base_name = txt_file.stem
        existing_md = list(structured_folder.glob(f"*_{base_name}.md"))
        
        if existing_md:
            print(f"건너뛰기 (이미 처리됨): {txt_file.name}")
            # wav 파일명으로 로그 기록 (txt 파일명에서 .txt 제거하면 wav 파일명)
            wav_filename = base_name + ".wav"
            logger.mark_complete(wav_filename, 'structured')
        else:
            files_to_structure.append(txt_file)
    
    if not files_to_structure:
        print("모든 파일이 이미 구조화되었습니다.")
        logger.save()
        return True
    
    print(f"총 {len(files_to_structure)}개의 파일을 구조화합니다...\n")
    
    # TextProcessor 초기화
    api_key_path = Config.API_KEY_PATH
    api_key_file = Config.OPENAI_API_KEY_FILE
    model = Config.GPT_MODEL
    
    try:
        processor = TextProcessor(
            api_key_path=api_key_path if api_key_path else None,
            api_key_file=api_key_file,
            model=model
        )
    except Exception as e:
        print(f"초기화 실패: {e}")
        return False
    
    # 프롬프트 설정 (일반 transcribed 텍스트용)
    context_query = Config.CONTEXT_QUERY
    main_query = Config.MAIN_QUERY
    additional_query = Config.ADDITIONAL_QUERY
    math_specific_query = Config.MATH_SPECIFIC_QUERY
    example_query = Config.EXAMPLE_QUERY
    tone_query = Config.TONE_QUERY
    token_range = Config.TOKEN_RANGE
    language = Config.LANGUAGE
    style = Config.OUTPUT_STYLE
    save_html = Config.SAVE_HTML
    html_template = Config.HTML_TEMPLATE
    
    processed_count = 0
    for txt_file in files_to_structure:
        try:
            # process_single_file 내부에서 메시지 출력하므로 여기서는 출력하지 않음
            result = processor.process_single_file(
                text_file=txt_file,
                output_folder=structured_folder,
                context_query=context_query,
                main_query=main_query,
                additional_query=additional_query,
                math_specific_query=math_specific_query,
                example_query=example_query,
                tone_query=tone_query,
                token_range=token_range,
                language=language,
                style=style,
                save_html=save_html,
                html_template=html_template
            )
            
            if result:
                # wav 파일명으로 로그 기록
                wav_filename = txt_file.stem + ".wav"
                logger.mark_complete(wav_filename, 'structured')
                processed_count += 1
                logger.save()  # 중간 저장
                print(f"✓ 완료: {txt_file.name}\n")
            else:
                print(f"✗ 실패: {txt_file.name}\n")
                
        except Exception as e:
            print(f"✗ 오류 ({txt_file.name}): {e}\n")
            continue
    
    print(f"\n[2-2 완료] {processed_count}개 파일 처리")
    logger.save()
    return True


def main():
    """메인 실행 함수"""
    start_time = time.time()
    
    print("=" * 60)
    print("전체 파이프라인 실행")
    print("=" * 60)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 로거 초기화
    log_path = Config.PROJECT_ROOT / "log.csv"
    logger = PipelineLogger(log_path)
    
    # (1) record_text_raw → structured
    success_1 = process_record_texts(logger)
    
    if not success_1:
        print("\n[1단계 실패] 파이프라인 중단")
        logger.save()
        return
    
    # (2) extracted_audio → transcribed → structured
    success_2 = process_audio_files(logger)
    
    if not success_2:
        print("\n[2단계 실패] 파이프라인 중단")
        logger.save()
        return
    
    # 최종 로그 저장
    logger.save()
    
    # 완료 요약
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 60)
    print("전체 파이프라인 완료!")
    print("=" * 60)
    print(f"소요 시간: {elapsed_time/60:.1f}분 ({elapsed_time:.0f}초)")
    print(f"로그 파일: {log_path}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
        print("진행 상황은 log.csv에 저장되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n치명적 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
