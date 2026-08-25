const runButton = document.querySelector("#run-comparison");
const state = document.querySelector("#run-state");
const summary = document.querySelector("#result-summary");
const comparison = document.querySelector("#comparison");

function setState(label, tone = "") {
  state.textContent = label;
  state.className = `status-chip ${tone}`;
}

function usage(value) {
  if (!value) return "Usage unavailable";
  return `${value.input_tokens} input / ${value.output_tokens} output / ${value.total_tokens} total`;
}

function toolTime(calls) {
  return `${calls.reduce((total, call) => total + call.tool_latency_ms, 0).toFixed(2)} ms`;
}

function renderExecution(card, execution) {
  card.querySelector('[data-field="summary"]').textContent = execution.report.summary;
  card.querySelector('[data-field="success"]').textContent = execution.success ? "true" : "false";
  card.querySelector('[data-field="tool-calls"]').textContent = JSON.stringify(execution.tool_calls, null, 2);
  card.querySelector('[data-field="llm-requests"]').textContent = execution.llm_requests;
  card.querySelector('[data-field="usage"]').textContent = usage(execution.usage);
  card.querySelector('[data-field="end-to-end"]').textContent = `${execution.end_to_end_ms.toFixed(2)} ms`;
  card.querySelector('[data-field="tool-time"]').textContent = toolTime(execution.tool_calls);
  card.querySelector('[data-field="evidence"]').textContent = execution.required_evidence.join(", ");
  card.querySelector('[data-field="trace"]').textContent = execution.trace
    ? `${execution.trace.trace_id} / ${execution.trace.span_types.join(", ")}`
    : "Unavailable";
}

runButton.addEventListener("click", async () => {
  runButton.disabled = true;
  comparison.hidden = true;
  summary.className = "empty-state";
  summary.textContent = "동일한 Diagnostics Agent를 Local Function과 MCP stdio로 실행 중입니다.";
  setState("RUNNING");

  try {
    const response = await fetch("/api/agent-mcp/comparison", { method: "POST" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Agent MCP 비교 요청에 실패했습니다.");

    const cards = comparison.querySelectorAll(".execution-card");
    renderExecution(cards[0], payload.local_function);
    renderExecution(cards[1], payload.mcp);
    summary.textContent = "동일 조건의 Local Function과 MCP Tool 실제 실행 결과입니다.";
    comparison.hidden = false;
    setState("SUCCESS", "success");
  } catch (error) {
    summary.className = "empty-state error-message";
    summary.textContent = error.message;
    setState("ERROR", "error");
  } finally {
    runButton.disabled = false;
  }
});
