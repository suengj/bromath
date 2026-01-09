"""
Main script for processing record text files with time stamps.
시간 스탬프가 있는 레코드 텍스트 파일을 구조화하는 메인 스크립트입니다.
"""
import sys
from pathlib import Path
from config import Config
from text_processor import TextProcessor


def build_record_prompt():
    """레코드 텍스트용 프롬프트 구성"""
    # 기존 프롬프트에 시간 순서 대화 형식 요구사항 추가
    context_query = Config.CONTEXT_QUERY
    main_query = Config.MAIN_QUERY
    additional_query = Config.ADDITIONAL_QUERY
    math_specific_query = Config.MATH_SPECIFIC_QUERY
    timestamp_dialogue_query = Config.TIMESTAMP_DIALOGUE_QUERY
    example_query = Config.EXAMPLE_QUERY
    tone_query = Config.TONE_QUERY
    
    # 시간 순서 정보를 포함한 컨텍스트
    enhanced_context = context_query + "\n\n**Important**: This content is from a time-stamped dialogue recording with chronological markers (e.g., \"참석자 1 00:30\")."
    
    return (
        enhanced_context,
        main_query,
        additional_query,
        math_specific_query + "\n\n" + timestamp_dialogue_query,  # 수학 요구사항 + 시간 순서 요구사항 결합
        example_query,
        tone_query
    )


def main():
    """메인 실행 함수"""
    # 설정 준비
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
    
    print("=" * 60)
    print("레코드 텍스트 구조화 파이프라인 (시간 순서 대화 형식)")
    print("=" * 60)
    print(f"입력 폴더: {record_folder}")
    print(f"출력 폴더: {output_folder}")
    print(f"GPT 모델: {model}")
    print("=" * 60)
    print()
    
    # TextProcessor 초기화
    try:
        processor = TextProcessor(
            api_key_path=api_key_path if api_key_path else None,
            api_key_file=api_key_file,
            model=model
        )
    except Exception as e:
        print(f"초기화 실패: {e}")
        print("\n해결 방법:")
        print(".env 파일에 OPENAI_API_KEY를 설정해주세요.")
        return
    
    # 모든 파일 처리
    processed_files = processor.process_all_files(
        text_folder=record_folder,
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
    
    print()
    print("=" * 60)
    md_count = len(processed_files)
    html_count = sum(1 for _, html_path in processed_files if html_path is not None)
    print(f"처리 완료: {md_count}개 마크다운 파일")
    if save_html:
        print(f"HTML 파일: {html_count}개")
    print(f"결과 폴더: {output_folder}")
    print("=" * 60)


def process_single_file_test():
    """단일 파일 테스트용"""
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
    
    print("=" * 60)
    print("단일 레코드 파일 테스트")
    print("=" * 60)
    
    try:
        processor = TextProcessor(
            api_key_path=api_key_path if api_key_path else None,
            api_key_file=api_key_file,
            model=model
        )
    except Exception as e:
        print(f"초기화 실패: {e}")
        print("\n해결 방법:")
        print(".env 파일에 OPENAI_API_KEY를 설정해주세요.")
        return
    
    # 첫 번째 파일만 처리
    text_files = processor.find_text_files(record_folder)
    if not text_files:
        print("처리할 파일이 없습니다.")
        return
    
    test_file = text_files[0]
    print(f"테스트 파일: {test_file.name}\n")
    
    result = processor.process_single_file(
        text_file=test_file,
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
        md_path, html_path = result
        print(f"\n테스트 완료:")
        print(f"  마크다운: {md_path}")
        if html_path:
            print(f"  HTML: {html_path}")
    else:
        print("\n테스트 실패")


if __name__ == "__main__":
    # 명령행 인자 확인
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        process_single_file_test()
    else:
        main()
