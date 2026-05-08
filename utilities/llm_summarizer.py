import os
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import httpx
import typing


from utilities.pipeline_context import PipelineContext


class LLMSummarizer:
    """Handles LLM-based summarization of transcripts."""

    def __init__(
        self,
        api_endpoint: str,
        api_key: Optional[str] = None,
        model_arch: Optional[str] = None,
        tokenizer_model: Optional[str] = None,
        verbose: int = 0,
        confirm_before_send: bool = True,
        summary_output: Optional[str] = None,
        summarization_prompt: Optional[str] = None,
    ):
        """
        Initialize the LLM summarizer.

        Args:
            api_endpoint: OpenAPI-compatible API endpoint URL
            api_key: API key for authentication
            model_arch: Model architecture to use for generation
            tokenizer_model: Model to use for token counting (defaults to model_arch)
            verbose: Verbosity level (0-5, where 0=quiet, 5=most verbose)
            confirm_before_send: Whether to ask for confirmation before sending
            summary_output: Output path for summary markdown
            summarization_prompt: Fully assembled summarization prompt
        """
        load_dotenv()

        self.api_endpoint = api_endpoint or os.getenv("LLM_API_ENDPOINT")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model_arch = model_arch or os.getenv("LLM_MODEL_ARCH", "nvidia/nemotron-3-super-120b-a12b:free")
        self.tokenizer_model = tokenizer_model or os.getenv("LLM_TOKENIZER_MODEL", "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16")
        self.verbose = verbose
        self.confirm_before_send = confirm_before_send
        self.summary_output = summary_output
        self.summarization_prompt = summarization_prompt

        self._validate_config()

        # Type assertions: after validation, these are guaranteed to be str
        assert self.api_endpoint is not None
        assert self.api_key is not None

    def _validate_config(self) -> None:
        """Validate that required configuration is present."""
        if not self.api_endpoint:
            raise ValueError(
                "LLM_API_ENDPOINT is required. Set it in .env or pass as argument."
            )
        if not self.api_key:
            raise ValueError(
                "LLM_API_KEY is required. Set it in .env or pass as argument."
            )

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using the transformers tokenizer.

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens
        """
        try:
            from transformers import AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(
                self.tokenizer_model, trust_remote_code=True
            )
            token_ids = tokenizer.encode(text)
            return len(token_ids)
        except Exception as e:
            if self.verbose > 0:
                print(f"[TOKEN COUNT WARNING] Could not count tokens: {e}")
            return -1

    def send_request(self, context: str) -> Dict[str, Any]:
        """
        Send the summarization request to the LLM API.

        Args:
            context: The assembled summarization context

        Returns:
            Dictionary with response data
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "SessionTranscriber",
        }

        payload = {
            "model": self.model_arch,
            "messages": [
                {"role": "user", "content": context}
            ],
            "temperature": 0.7,
            "max_tokens": 4000,
        }

        if self.verbose > 0:
            print(f"[API REQUEST] Sending to: {self.api_endpoint}")
            print(f"[API REQUEST] Model: {self.model_arch}")
            print(f"[API REQUEST] Context length: {len(context)} characters")

        try:
            response = httpx.post(
                self.api_endpoint,  # type: str
                headers=headers,
                json=payload,
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()

            if self.verbose > 0:
                print(f"[API RESPONSE] Status: {response.status_code}")

            return {
                "success": True,
                "summary": data["choices"][0]["message"]["content"],
                "model": data.get("model", self.model_arch),
                "usage": data.get("usage", {}),
            }

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            if self.verbose > 0:
                print(f"[API ERROR] {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            if self.verbose > 0:
                print(f"[API ERROR] {error_msg}")
            return {"success": False, "error": error_msg}

    def summarize(
        self,
        transcript_path: str,
    ) -> Dict[str, Any]:
        """
        Full summarization pipeline: build context from prompt and transcript,
        count tokens, optionally confirm, send request, and save results.

        Args:
            transcript_path: Path to the transcript file

        Returns:
            Dictionary with summary and metadata
        """
        print("\n" + "="*60)
        print("SUMMARIZATION PHASE")
        print("="*60)

        if not transcript_path or not os.path.exists(transcript_path):
            print("[WARNING] Transcript file not found.")
            return {"success": False, "error": "Transcript file not found"}

        print(f"[TRANSCRIPT] {os.path.basename(transcript_path)}")

        # Read transcript
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_content = f.read()

        # Build context by combining prompts with transcript
        parts = []
        if self.summarization_prompt:
            parts.append(self.summarization_prompt.strip())
            parts.append("")

        parts.append(transcript_content.strip())
        context = "\n".join(parts)

        # Count tokens
        token_count = self.count_tokens(context)
        if self.verbose > 0 or token_count >= 0:
            print(f"[TOKEN COUNT] {token_count} tokens")

        # Preview (verbosity level 2+)
        if self.verbose > 1:
            lines = transcript_content.strip().split("\n")
            preview_lines = lines[:3] + (["..."] if len(lines) > 4 else []) + lines[-1:]
            print(f"\n[PREVIEW]")
            for line in preview_lines:
                print(f"  {line}")
            print()

        # Confirm before sending
        if self.confirm_before_send:
            try:
                response = input(
                    f"\nSend summarization request? (y/n) "
                    f"[model={self.model_arch}, tokens={token_count}]: "
                ).strip().lower()
                if response not in ("y", "yes"):
                    return {"success": False, "error": "User cancelled"}
            except (EOFError, KeyboardInterrupt):
                return {"success": False, "error": "User cancelled"}

        # Send request
        result = self.send_request(context)

        if result["success"]:
            if self.verbose > 0:
                print(f"\n[SUCCESS] Summary generated!")
                print(f"\n{result['summary']}")

            # Determine output path
            output = self.summary_output
            if not output:
                base = os.path.splitext(os.path.basename(transcript_path))[0]
                output = os.path.join(os.path.dirname(transcript_path), f"{base}_summary.md")

            self.save_summary_markdown(
                result["summary"],
                output,
                transcript_path,
                result.get("usage"),
            )

        return result

    def save_summary_markdown(
        self,
        summary: str,
        output_path: str,
        transcript_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Save the summary as a markdown file with metadata.

        Args:
            summary: The summary text
            output_path: Path to save the markdown file
            transcript_path: Path to the source transcript
            metadata: Optional metadata dictionary
        """
        import datetime

        lines = []
        lines.append("# Summary")
        lines.append("")
        lines.append(f"**Source:** `{os.path.basename(transcript_path)}`")
        lines.append(f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if metadata:
            if "model" in metadata:
                lines.append(f"**Model:** {metadata['model']}")
            if "usage" in metadata:
                usage = metadata["usage"]
                lines.append(f"**Usage:** {json.dumps(usage)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(summary.strip())

        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        if self.verbose > 0:
            print(f"[SAVED] Summary written to: {output_path}")


class LLMSummarizerBuilder:
    """Builder for creating LLMSummarizer instances."""

    def __init__(self, verbosity: int = 0):
        self._api_endpoint: Optional[str] = None
        self._api_key: Optional[str] = None
        self._model_arch: Optional[str] = None
        self._tokenizer_model: Optional[str] = None
        self._verbose: int = verbosity
        self._confirm_before_send: bool = True
        self._summary_output: Optional[str] = None
        self._pipeline_context: Optional[PipelineContext] = None
        self._summarization_prompt: Optional[str] = None

        if verbosity < 0 or verbosity > 5:
            raise ValueError("Verbosity must be an integer, 0 <= verbosity <= 5")

    def with_api_endpoint(self, endpoint: str) -> "LLMSummarizerBuilder":
        self._api_endpoint = endpoint
        return self

    def with_api_key(self, key: str) -> "LLMSummarizerBuilder":
        self._api_key = key
        return self

    def with_model(self, model: str) -> "LLMSummarizerBuilder":
        self._model_arch = model
        return self

    def with_tokenizer_model(self, model: str) -> "LLMSummarizerBuilder":
        self._tokenizer_model = model
        return self

    def with_verbosity(self, verbose: int) -> "LLMSummarizerBuilder":
        """Set verbosity level (0-5). Can also be set in constructor."""
        if verbose < 0 or verbose > 5:
            raise ValueError("Verbosity must be an integer, 0 <= verbosity <= 5")
        self._verbose = verbose
        return self

    def with_confirmation(self, confirm: bool) -> "LLMSummarizerBuilder":
        self._confirm_before_send = confirm
        return self

    def with_summary_output(self, output: str) -> "LLMSummarizerBuilder":
        self._summary_output = output
        return self

    def with_pipeline_context(self, context: PipelineContext) -> "LLMSummarizerBuilder":
        """Use a PipelineContext to extract prompts for summarization."""
        self._pipeline_context = context
        self._summarization_prompt = context.get_summarization_prompt()
        return self

    def with_assembled_summarization_prompt(self, prompt: str) -> "LLMSummarizerBuilder":
        self._summarization_prompt = prompt
        return self

    def build(self) -> LLMSummarizer:
        """Build the LLMSummarizer instance after validating required fields."""
        # Fail-fast validation
        required_fields = []
        
        # if self._api_endpoint is None:
        #     required_fields.append("api_endpoint (use with_api_endpoint())")
        
        if self._summary_output is None:
            required_fields.append("summary_output (use with_summary_output())")
            
        if self._summarization_prompt is None:
            required_fields.append("summarization_prompt (use with_assembled_summarization_prompt() or with_pipeline_context())")
        
        # Need at least one of model_arch or tokenizer_model
        # if self._model_arch is None and self._tokenizer_model is None:
        #     required_fields.append("model_arch (use with_model()) or tokenizer_model (use with_tokenizer_model())")
        
        if required_fields:
            raise ValueError(
                "Cannot build LLMSummarizer. Missing required fields:\n  - " 
                + "\n  - ".join(required_fields)
            )
        
        return LLMSummarizer(
            api_endpoint=self._api_endpoint,
            api_key=self._api_key,
            model_arch=self._model_arch,
            tokenizer_model=self._tokenizer_model,
            verbose=self._verbose,
            confirm_before_send=self._confirm_before_send,
            summary_output=self._summary_output,
            summarization_prompt=self._summarization_prompt,
        )

