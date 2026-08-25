const form = document.querySelector("#diagnostic-form");
const question = document.querySelector("#question");
const submitButton = form.querySelector("button");
const state = document.querySelector("#run-state");
const summary = document.querySelector("#result-summary");
const comparison = document.querySelector("#comparison");

function setState(label, tone = "") {
  state.textContent = label;
  state.className = `status-chip ${tone}`;
}

function json(value) {
  return JSON.stringify(value, null, 2);
}

function usage(value) {
  if (!value) return "Usage unavailable";
  return `${value.input_tokens} input / ${value.output_tokens} output / ${value.total_tokens} total`;
}

function renderExecution(card, execution) {
  card.querySelector('[data-field="summary"]').textContent = execution.report.summary;
  card.querySelector('[data-field="tool-calls"]').textContent = json(execution.tool_calls);
  card.querySelector('[data-field="llm-requests"]').textContent = execution.llm_requests;
  card.querySelector('[data-field="usage"]').textContent = usage(execution.usage);
  card.querySelector('[data-field="end-to-end"]').textContent = `${execution.end_to_end_ms.toFixed(2)} ms`;
  card.querySelector('[data-field="evidence"]').textContent = execution.required_evidence.join(", ");
  card.querySelector('[data-field="trace"]').textContent = execution.trace
    ? `${execution.trace.trace_id} / ${execution.trace.span_types.join(", ")}`
    : "Not applicable";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitButton.disabled = true;
  comparison.hidden = true;
  summary.className = "empty-state";
  summary.textContent = "Workflow와 Agents SDK 기반 Diagnostics Agent를 실행 중입니다.";
  setState("RUNNING");

  try {
    const response = await fetch("/api/diagnostics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: json({ question: question.value.trim() }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "진단 요청에 실패했습니다.");

    const cards = comparison.querySelectorAll(".execution-card");
    renderExecution(cards[0], payload.workflow);
    renderExecution(cards[1], payload.agent);
    summary.textContent = "동일 조건의 실제 실행 결과입니다.";
    comparison.hidden = false;
    setState("SUCCESS", "success");
  } catch (error) {
    summary.className = "empty-state error-message";
    summary.textContent = error.message;
    setState("ERROR", "error");
  } finally {
    submitButton.disabled = false;
  }
});
