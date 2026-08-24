const form = document.querySelector("#diagnostic-form");
const question = document.querySelector("#question");
const submitButton = form.querySelector("button");
const state = document.querySelector("#run-state");
const summary = document.querySelector("#result-summary");
const observation = document.querySelector("#observation");

function setState(label, tone = "") {
  state.textContent = label;
  state.className = `status-chip ${tone}`;
}

function json(value) {
  return JSON.stringify(value, null, 2);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitButton.disabled = true;
  observation.hidden = true;
  summary.className = "empty-state";
  summary.textContent = "Responses API와 Backend Diagnostics API를 호출하는 중입니다.";
  setState("RUNNING");

  try {
    const response = await fetch("/api/diagnostics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: json({ question: question.value.trim() }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "진단 요청에 실패했습니다.");
    }

    summary.textContent = payload.report.summary;
    document.querySelector("#selected-tool").textContent = payload.observation.selected_tool;
    document.querySelector("#tool-arguments").textContent = json(payload.observation.tool_arguments);
    document.querySelector("#tool-result").textContent = json(payload.observation.tool_result);
    document.querySelector("#tool-latency").textContent = `${payload.observation.tool_latency_ms.toFixed(2)} ms`;
    document.querySelector("#usage").textContent = payload.usage
      ? `${payload.usage.input_tokens} input / ${payload.usage.output_tokens} output / ${payload.usage.total_tokens} total`
      : "Responses API usage unavailable";
    observation.hidden = false;
    setState("SUCCESS", "success");
  } catch (error) {
    summary.className = "empty-state error-message";
    summary.textContent = error.message;
    setState("ERROR", "error");
  } finally {
    submitButton.disabled = false;
  }
});
