const startButton = document.querySelector("#start-run");
const approveButton = document.querySelector("#approve-run");
const rejectButton = document.querySelector("#reject-run");
const state = document.querySelector("#run-state");
const summary = document.querySelector("#result-summary");
const approvalRequest = document.querySelector("#approval-request");
const approvalDetail = document.querySelector("#approval-detail");
const runResult = document.querySelector("#run-result");

let pendingRunId = null;

function setState(label, tone = "") {
  state.textContent = label;
  state.className = `status-chip ${tone}`;
}

function usage(value) {
  if (!value) return "Usage unavailable";
  return `${value.input_tokens} input / ${value.output_tokens} output / ${value.total_tokens} total`;
}

function renderResult(result) {
  document.querySelector("#report-summary").textContent = result.report?.summary || "Approval pending";
  document.querySelector("#fixture-status").textContent = result.service_status.status;
  document.querySelector("#approval-state").textContent = result.approval_decision || "pending";
  document.querySelector("#tool-calls").textContent = JSON.stringify(result.tool_calls, null, 2);
  document.querySelector("#llm-requests").textContent = result.llm_requests;
  document.querySelector("#usage").textContent = usage(result.usage);
  document.querySelector("#end-to-end").textContent = `${result.end_to_end_ms.toFixed(2)} ms`;
  document.querySelector("#approval-wait").textContent = `${result.approval_wait_ms.toFixed(2)} ms`;
  document.querySelector("#evidence").textContent = result.required_evidence.join(", ");
  document.querySelector("#trace").textContent = result.trace
    ? `${result.trace.trace_id} / ${result.trace.span_types.join(", ")}`
    : "Unavailable";
  runResult.hidden = false;
}

function setDecisionDisabled(disabled) {
  approveButton.disabled = disabled;
  rejectButton.disabled = disabled;
}

async function request(url) {
  const response = await fetch(url, { method: "POST" });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Approval 요청에 실패했습니다.");
  return payload;
}

startButton.addEventListener("click", async () => {
  startButton.disabled = true;
  approvalRequest.hidden = true;
  runResult.hidden = true;
  summary.className = "empty-state";
  summary.textContent = "Read Tool 실행 후 restart_service 승인 요청을 대기 중입니다.";
  setState("RUNNING");

  try {
    const result = await request("/api/human-approval/start");
    pendingRunId = result.run_id;
    renderResult(result);
    approvalDetail.textContent = `${result.approval.tool_name} ${JSON.stringify(result.approval.tool_arguments)}`;
    approvalRequest.hidden = false;
    setDecisionDisabled(false);
    summary.textContent = "restart_service는 아직 실행되지 않았습니다. 승인 또는 거절을 선택하세요.";
    setState("WAITING APPROVAL", "warning");
  } catch (error) {
    summary.className = "empty-state error-message";
    summary.textContent = error.message;
    setState("ERROR", "error");
  } finally {
    if (!pendingRunId) startButton.disabled = false;
  }
});

async function resolve(decision) {
  if (!pendingRunId) return;
  setDecisionDisabled(true);
  summary.textContent = "동일한 RunState를 재개하는 중입니다.";
  setState("RESUMING");

  try {
    const result = await request(`/api/human-approval/${pendingRunId}/${decision}`);
    renderResult(result);
    approvalRequest.hidden = true;
    pendingRunId = null;
    startButton.disabled = false;
    summary.textContent = decision === "approve"
      ? "승인 후 restart_service가 실행되었습니다."
      : "거절 후 restart_service는 실행되지 않았습니다.";
    setState("COMPLETED", "success");
  } catch (error) {
    summary.className = "empty-state error-message";
    summary.textContent = error.message;
    setState("ERROR", "error");
  }
}

approveButton.addEventListener("click", () => resolve("approve"));
rejectButton.addEventListener("click", () => resolve("reject"));
