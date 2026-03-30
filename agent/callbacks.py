import logging
import time
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


class FinancialAgentCallbackHandler(BaseCallbackHandler):
    """Callback handler that logs agent activity and tool calls."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._start_time: Optional[float] = None
        self._tool_times: Dict[str, float] = {}

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        if self._start_time is None:
            self._start_time = time.time()
        if self.verbose:
            model = serialized.get("name", "LLM")
            logger.debug("[LLM] Calling %s...", model)

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized.get("name", "unknown_tool")
        self._tool_times[str(run_id)] = time.time()
        logger.info("[TOOL] Starting: %s", tool_name)
        if self.verbose:
            logger.debug("[TOOL] Input: %s", input_str[:200])

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        elapsed = time.time() - self._tool_times.pop(str(run_id), time.time())
        logger.info("[TOOL] Completed in %.2fs", elapsed)
        if self.verbose:
            logger.debug("[TOOL] Output preview: %s...", str(output)[:200])

    def on_tool_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        logger.error("[TOOL] Error: %s", str(error))

    def on_agent_finish(self, finish: Any, **kwargs: Any) -> None:
        if self._start_time:
            total = time.time() - self._start_time
            logger.info("[AGENT] Finished in %.2fs total", total)
            self._start_time = None
