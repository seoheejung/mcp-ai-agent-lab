from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from openai import AsyncOpenAI
from pydantic import ValidationError

from .config import Settings
from .errors import FunctionToolError, LlmResponseError, StructuredOutputError
from .models import (
    DiagnosticReport,
    DiagnosticRunResult,
    ResponseUsage,
    StreamingCheckResult,
    ToolObservation,
)
from .tools import FUNCTION_TOOLS, FunctionTools

REPORT_FORMAT = {
    "type": "json_schema",
    "name": "diagnostic_report",
    "schema": DiagnosticReport.model_json_schema(),
    "strict": True,
}


class ToolCallingRunner:
    def __init__(
        self,
        settings: Settings,
        tools: FunctionTools,
        client: AsyncOpenAI | Any | None = None,
    ) -> None:
        self._settings = settings
        self._tools = tools
        self._client = client

    async def run(self, question: str) -> DiagnosticRunResult:
        api_key, model = self._settings.require_openai()
        client = self._client or AsyncOpenAI(api_key=api_key)
        initial = await client.responses.create(
            model=model,
            instructions=(
                "Select exactly one diagnostics function that directly answers the user's "
                "question. Do not call any function more than once."
            ),
            input=question,
            tools=FUNCTION_TOOLS,
            tool_choice="auto",
            parallel_tool_calls=False,
        )
        calls = [item for item in initial.output if getattr(item, "type", None) == "function_call"]
        if len(calls) != 1:
            raise FunctionToolError("Expected exactly one function call from the model")

        call = calls[0]
        try:
            arguments = json.loads(call.arguments)
        except json.JSONDecodeError as error:
            raise FunctionToolError("Model returned invalid function arguments") from error
        if not isinstance(arguments, dict):
            raise FunctionToolError("Model returned function arguments that are not an object")

        started_at = perf_counter()
        tool_result = await self._tools.execute(call.name, arguments)
        tool_latency_ms = (perf_counter() - started_at) * 1000

        final = await client.responses.create(
            model=model,
            instructions=(
                "Create a concise diagnostic report from the supplied function result. "
                "Return only the required JSON schema."
            ),
            input=[
                *initial.output,
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(tool_result),
                },
            ],
            text={"format": REPORT_FORMAT},
        )
        try:
            report = DiagnosticReport.model_validate_json(final.output_text)
        except (ValidationError, ValueError) as error:
            raise StructuredOutputError("Model response failed DiagnosticReport validation") from error

        return DiagnosticRunResult(
            report=report,
            observation=ToolObservation(
                selected_tool=call.name,
                tool_arguments=arguments,
                tool_result=tool_result,
                tool_latency_ms=tool_latency_ms,
            ),
            usage=_response_usage(initial, final),
        )

    async def verify_streaming(self) -> StreamingCheckResult:
        api_key, model = self._settings.require_openai()
        client = self._client or AsyncOpenAI(api_key=api_key)
        stream = await client.responses.create(
            model=model,
            input="Return one short sentence confirming streaming is active.",
            stream=True,
        )
        event_types: list[str] = []
        async for event in stream:
            event_type = getattr(event, "type", None)
            if isinstance(event_type, str):
                event_types.append(event_type)
        if not event_types:
            raise LlmResponseError("Responses API streaming returned no events")
        return StreamingCheckResult(event_types=event_types)


def _response_usage(*responses: Any) -> ResponseUsage | None:
    input_tokens = 0
    output_tokens = 0
    found = False
    for response in responses:
        usage = getattr(response, "usage", None)
        if usage is None:
            continue
        input_tokens += usage.input_tokens
        output_tokens += usage.output_tokens
        found = True
    if not found:
        return None
    return ResponseUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
    )
