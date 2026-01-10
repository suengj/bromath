"""
Text processing module for structuring transcribed text using GPT.
transcribed 폴더의 텍스트 파일을 구조화하는 모듈입니다.
"""
import json
import time
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
import tiktoken
from openai import OpenAI

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("경고: markdown 라이브러리가 설치되지 않았습니다. HTML 변환을 사용하려면 'pip install markdown'을 실행하세요.")


class TextProcessor:
    """텍스트 구조화 처리 클래스"""
    
    def __init__(self, api_key_path: Path, api_key_file: str, model: str = "gpt-5-mini-2025-08-07"):
        """
        TextProcessor 초기화
        
        Args:
            api_key_path: API 키가 있는 디렉토리 경로
            api_key_file: API 키 파일명
            model: 사용할 GPT 모델 이름
        """
        self.api_key_path = api_key_path
        self.api_key_file = api_key_file
        self.model = model
        self.client = self._load_client()
    
    def _load_client(self) -> OpenAI:
        """OpenAI 클라이언트 로드 - .env 파일에서만 읽기"""
        # .env 파일에서만 API 키 읽기 (유일한 방법)
        env_path = Path(__file__).parent / '.env'
        
        if not env_path.exists():
            raise FileNotFoundError(
                f".env 파일을 찾을 수 없습니다: {env_path}\n"
                f".env 파일에 OPENAI_API_KEY를 설정해주세요."
            )
        
        try:
            api_key = None
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # 공백을 허용: "OPENAI_API_KEY = ..." 또는 "OPENAI_API_KEY=..." 모두 처리
                    if 'OPENAI_API_KEY' in line and '=' in line:
                        # 공백 제거 후 파싱
                        line_no_space = line.replace(' ', '').replace('\t', '')
                        if line_no_space.startswith('OPENAI_API_KEY='):
                            api_key = line_no_space.split('=', 1)[1].strip().strip('"').strip("'")
                            if api_key and len(api_key) > 10:  # 최소 길이 확인
                                break
            
            if not api_key:
                raise ValueError(
                    f".env 파일에 OPENAI_API_KEY가 설정되지 않았습니다.\n"
                    f".env 파일에 OPENAI_API_KEY=your-api-key 형식으로 설정해주세요."
                )
            
            print(".env 파일에서 OPENAI_API_KEY를 사용합니다.")
            return OpenAI(api_key=api_key)
            
        except FileNotFoundError as e:
            raise e
        except ValueError as e:
            raise e
        except Exception as e:
            raise RuntimeError(f"OpenAI 클라이언트 로드 실패: {e}")
    
    def find_text_files(self, text_folder: Path) -> List[Path]:
        """
        텍스트 폴더에서 .txt 파일을 찾습니다.
        
        Args:
            text_folder: 검색할 폴더 경로
            
        Returns:
            .txt 파일 경로 리스트
        """
        if not text_folder.exists():
            raise FileNotFoundError(f"텍스트 폴더를 찾을 수 없습니다: {text_folder}")
        
        txt_files = list(text_folder.glob("*.txt"))
        
        if not txt_files:
            print(f"경고: {text_folder}에서 .txt 파일을 찾을 수 없습니다.")
        
        return txt_files
    
    def read_text_file(self, file_path: Path) -> str:
        """
        텍스트 파일을 읽습니다.
        
        Args:
            file_path: 텍스트 파일 경로
            
        Returns:
            파일 내용
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content.strip()
        except Exception as e:
            raise RuntimeError(f"파일 읽기 실패 ({file_path.name}): {e}")
    
    def build_prompt(
        self,
        transcription: str,
        filename: str,
        context_query: str,
        main_query: str,
        additional_query: str,
        math_specific_query: str,
        example_query: str,
        tone_query: str,
        token_range: List[float],
        language: str = "Korean",
        style: str = "Markdown"
    ) -> str:
        """
        프롬프트 구조화 (p03_speech2text의 prompt_structure 참고)
        
        Args:
            transcription: 원본 전사 텍스트
            filename: 파일명
            context_query: 컨텍스트 설명
            main_query: 주요 요청 사항
            additional_query: 추가 요청 사항
            math_specific_query: 수학 특화 요청 사항
            example_query: 예시/참고 사항
            tone_query: 톤 설정
            token_range: 토큰 범위 [min_multiplier, max_multiplier]
            language: 출력 언어
            style: 출력 형식
            
        Returns:
            구조화된 프롬프트
        """
        # 파일명과 텍스트를 구조화
        structured_transcription = [
            {
                "title": filename,
                "transcription": transcription
            }
        ]
        
        # JSON 변환
        json_query = json.dumps(structured_transcription, indent=2, ensure_ascii=False)
        
        # 토큰 수 계산
        encoder = tiktoken.get_encoding("cl100k_base")
        tokens = encoder.encode(transcription)
        token_count = len(tokens)
        
        print(f"원본 토큰 수: {token_count}")
        print(f"목표 토큰 범위: {int(token_range[0] * token_count)} ~ {int(token_range[1] * token_count)}")
        
        # 전체 프롬프트 구성
        full_prompt = f"""
{context_query}

{main_query}

{additional_query}

{math_specific_query}

{example_query}

{tone_query}

[Requirement]

Please use the provided transcription file as {json_query}.

1. The response should follow the {style} format.
2. The content must be written in {language}.
   - If most of the content is not in Korean (e.g., English, Japanese, Chinese, etc.), translate it into Korean first, then summarize and reorganize it accordingly.

3. The number of tokens in the answer should fall between {token_range[0] * token_count} and {token_range[1] * token_count}, depending on the quality of the content.
   - Exceeding the maximum token limit is acceptable, but the total length SHOULD not exceed more than twice times than the maximum length required.

4. Ensure concise, professional organization by:
   - Distinguishing core messages from detailed messages.
   - Using tables, bullet points, or diagrams, where applicable, to enhance understanding.
5. Highlight actionable insights and label them as "Key Takeaways."
6. Add relevant external knowledge or examples to deepen insights, marked as "Insights."
7. Identify recurring themes or patterns and analyze their significance.
8. Do not return any meta-information about your response; provide only the answer related to the given content.
"""
        
        return full_prompt
    
    def process_text_with_gpt(
        self,
        text_content: str,
        filename: str,
        context_query: str,
        main_query: str,
        additional_query: str,
        math_specific_query: str,
        example_query: str,
        tone_query: str,
        token_range: List[float],
        language: str = "Korean",
        style: str = "Markdown"
    ) -> str:
        """
        GPT를 사용하여 텍스트를 구조화합니다.
        
        Args:
            text_content: 원본 텍스트 내용
            filename: 파일명
            context_query: 컨텍스트 설명
            main_query: 주요 요청 사항
            additional_query: 추가 요청 사항
            math_specific_query: 수학 특화 요청 사항
            example_query: 예시/참고 사항
            tone_query: 톤 설정
            token_range: 토큰 범위
            language: 출력 언어
            style: 출력 형식
            
        Returns:
            구조화된 텍스트
        """
        # 프롬프트 생성
        prompt = self.build_prompt(
            transcription=text_content,
            filename=filename,
            context_query=context_query,
            main_query=main_query,
            additional_query=additional_query,
            math_specific_query=math_specific_query,
            example_query=example_query,
            tone_query=tone_query,
            token_range=token_range,
            language=language,
            style=style
        )
        
        # GPT 요청
        print(f"GPT 요청 시작 (모델: {self.model})...")
        start_time = time.time()
        
        try:
            input_message = [
                {'role': 'user', 'content': prompt}
            ]
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=input_message
            )
            
            response_text = completion.choices[0].message.content
            
            elapsed_time = time.time() - start_time
            print(f"GPT 응답 완료: {elapsed_time:.2f}초")
            
            return response_text.strip()
            
        except Exception as e:
            raise RuntimeError(f"GPT 요청 실패: {e}")
    
    def save_structured_text(
        self,
        structured_text: str,
        output_folder: Path,
        original_filename: str,
        date_prefix: Optional[str] = None,
        save_html: bool = False,
        html_template: Optional[str] = None,
        output_filename_suffix: str = ""
    ) -> Tuple[Path, Optional[Path]]:
        """
        구조화된 텍스트를 마크다운 파일로 저장하고, 필요시 HTML 파일도 저장합니다.
        
        Args:
            structured_text: 구조화된 텍스트 내용 (마크다운 형식)
            output_folder: 출력 폴더 경로
            original_filename: 원본 파일명
            date_prefix: 날짜 접두사 (None이면 자동 생성)
            save_html: True이면 HTML 파일도 저장
            html_template: HTML 템플릿 (None이면 기본 템플릿 사용)
            output_filename_suffix: 출력 파일명에 추가할 접미사 (예: "_srt")
            
        Returns:
            (마크다운 파일 경로, HTML 파일 경로 또는 None)
        """
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # 날짜 및 시간 접두사 (YYYY-MM-DD_HHMMSS 형식)
        if date_prefix is None:
            date_prefix = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        # 파일명 생성 (.txt -> .md 또는 .srt -> .md)
        base_name = Path(original_filename).stem
        
        # SRT 파일의 경우 _SRT 제거
        if base_name.endswith('_SRT'):
            base_name = base_name[:-4]  # _SRT 제거
        
        # 접미사 추가
        if output_filename_suffix:
            md_filename = f"{date_prefix}_{base_name}{output_filename_suffix}.md"
        else:
            md_filename = f"{date_prefix}_{base_name}.md"
        md_path = output_folder / md_filename
        
        # 마크다운 파일 저장
        with open(md_path, 'w', encoding='utf-8-sig') as f:
            f.write(structured_text)
        
        print(f"마크다운 파일 저장 완료: {md_path}")
        
        # 마크다운 파일 저장 후 HTML 변환 (마크다운 파일 기반)
        html_path = None
        if save_html:
            if not MARKDOWN_AVAILABLE:
                print("경고: markdown 라이브러리가 없어 HTML 변환을 건너뜁니다.")
            else:
                # 마크다운 파일을 읽어서 HTML로 변환
                html_path = self._save_html_file(
                    md_file_path=md_path,
                    output_folder=output_folder,
                    html_template=html_template
                )
        
        return (md_path, html_path)
    
    def _save_html_file(
        self,
        md_file_path: Path,
        output_folder: Path,
        html_template: Optional[str] = None
    ) -> Path:
        """
        마크다운 파일을 읽어서 HTML로 변환하여 저장합니다.
        
        Args:
            md_file_path: 마크다운 파일 경로
            output_folder: 출력 폴더 경로
            html_template: HTML 템플릿 (None이면 기본 템플릿 사용)
            
        Returns:
            저장된 HTML 파일 경로
        """
        # 마크다운 파일 읽기
        with open(md_file_path, 'r', encoding='utf-8-sig') as f:
            markdown_content = f.read()
        
        # 마크다운을 HTML로 변환
        html_content = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        
        # HTML 파일명 생성 (마크다운 파일명과 동일하게, 확장자만 .html)
        html_filename = md_file_path.name.replace('.md', '.html')
        html_path = output_folder / html_filename
        
        # HTML 템플릿 적용
        title = md_file_path.stem
        if html_template:
            final_html = html_template.format(title=title, content=html_content)
        else:
            # 기본 HTML 래퍼
            final_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script>
        window.MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']]
            }}
        }};
    </script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2, h3, h4 {{
            color: #333;
            margin-top: 1.5em;
        }}
        h1 {{
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            border-bottom: 2px solid #81C784;
            padding-bottom: 8px;
            margin-top: 2em;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        hr {{
            border: none;
            border-top: 2px solid #ddd;
            margin: 2em 0;
        }}
        ul, ol {{
            margin: 1em 0;
            padding-left: 2em;
        }}
        blockquote {{
            border-left: 4px solid #4CAF50;
            margin: 1em 0;
            padding-left: 1em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
    </div>
</body>
</html>"""
        
        # HTML 파일 저장
        with open(html_path, 'w', encoding='utf-8-sig') as f:
            f.write(final_html)
        
        print(f"HTML 파일 저장 완료: {html_path}")
        return html_path
    
    def process_single_file(
        self,
        text_file: Path,
        output_folder: Path,
        context_query: str,
        main_query: str,
        additional_query: str,
        math_specific_query: str,
        example_query: str,
        tone_query: str,
        token_range: List[float],
        language: str = "Korean",
        style: str = "Markdown",
        save_html: bool = False,
        html_template: Optional[str] = None,
        output_filename_suffix: str = ""
    ) -> Optional[Tuple[Path, Optional[Path]]]:
        """
        단일 텍스트 파일을 처리합니다.
        
        Args:
            text_file: 처리할 텍스트 파일 경로
            output_folder: 출력 폴더 경로
            context_query: 컨텍스트 설명
            main_query: 주요 요청 사항
            additional_query: 추가 요청 사항
            math_specific_query: 수학 특화 요청 사항
            example_query: 예시/참고 사항
            tone_query: 톤 설정
            token_range: 토큰 범위
            language: 출력 언어
            style: 출력 형식
            output_filename_suffix: 출력 파일명에 추가할 접미사 (예: "_srt")
            
        Returns:
            저장된 마크다운 파일 경로 (실패 시 None)
        """
        print(f"처리 중: {text_file.name}")
        print("-" * 60)
        
        try:
            # 텍스트 읽기
            text_content = self.read_text_file(text_file)
            print(f"텍스트 길이: {len(text_content)} 문자")
            
            # GPT로 구조화
            structured_text = self.process_text_with_gpt(
                text_content=text_content,
                filename=text_file.name,
                context_query=context_query,
                main_query=main_query,
                additional_query=additional_query,
                math_specific_query=math_specific_query,
                example_query=example_query,
                tone_query=tone_query,
                token_range=token_range,
                language=language,
                style=style
            )
            
            # 마크다운 파일로 저장 (HTML도 함께 저장 가능)
            md_path, html_path = self.save_structured_text(
                structured_text=structured_text,
                output_folder=output_folder,
                original_filename=text_file.name,
                save_html=save_html,
                html_template=html_template,
                output_filename_suffix=output_filename_suffix
            )
            
            return (md_path, html_path)
            
        except Exception as e:
            print(f"처리 실패 ({text_file.name}): {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def process_all_files(
        self,
        text_folder: Path,
        output_folder: Path,
        context_query: str,
        main_query: str,
        additional_query: str,
        math_specific_query: str,
        example_query: str,
        tone_query: str,
        token_range: List[float],
        language: str = "Korean",
        style: str = "Markdown",
        save_html: bool = False,
        html_template: Optional[str] = None
    ) -> List[Tuple[Path, Optional[Path]]]:
        """
        모든 텍스트 파일을 처리합니다.
        
        Args:
            text_folder: 텍스트 파일이 있는 폴더
            output_folder: 출력 폴더 경로
            context_query: 컨텍스트 설명
            main_query: 주요 요청 사항
            additional_query: 추가 요청 사항
            math_specific_query: 수학 특화 요청 사항
            example_query: 예시/참고 사항
            tone_query: 톤 설정
            token_range: 토큰 범위
            language: 출력 언어
            style: 출력 형식
            
        Returns:
            성공적으로 저장된 파일 경로 리스트
        """
        text_files = self.find_text_files(text_folder)
        
        if not text_files:
            print("처리할 파일이 없습니다.")
            return []
        
        print(f"총 {len(text_files)}개의 파일을 처리합니다.")
        
        processed_files = []
        
        for i, text_file in enumerate(text_files, 1):
            print(f"\n[{i}/{len(text_files)}]")
            
            result = self.process_single_file(
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
                processed_files.append(result)
            
            # API 요청 간 딜레이 (옵션)
            if i < len(text_files):
                time.sleep(1)
        
        return processed_files
