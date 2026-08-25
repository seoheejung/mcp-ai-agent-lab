const experimentButtons = document.querySelectorAll("[data-experiment]");
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

function setExperimentDisabled(disabled) {
  experimentButtons.forEach((button) => { button.disabled = disabled; });
}

function renderResult(result) {
  document.querySelector("#report-summary").textContent = result.report?.summary || "Approval pending";
  document.querySelector("#experiment").textContent = result.experiment;
  document.querySelector("#handoffs").textContent = result.handoffs.length
    ? result.handoffs.map((handoff) => `${handoff.from_agent} → ${handoff.to_agent}`).join(", ")
    : "None observed";
  document.querySelector("#fixture-status").textContent = result.service_status.status;
  document.querySelector("#approval-state").textContent = result.approval_decision || (result.approval ? "pending" : "not requested");
  document.querySelector("#tool-calls").textContent = JSON.stringify(result.tool_calls, null, 2);
  document.querySelector("#llm-requests").textContent = result.llm_requests;
  document.querySelector("#usage").textContent = usage(result.usage);
  document.querySelector("#end-to-end").textContent = `${result.end_to_end_ms.toFixed(2)} ms`;
  document.querySelector("#approval-wait").textContent = `${result.approval_wait_ms.toFixed(2)} ms`;
  document.querySelector("#trace").textContent = result.trace
    ? `Recorded / ${result.trace.span_types.join(", ")}`
    : "Unavailable";
  runResult.hidden = false;
}

async function request(url) {
  const response = await fetch(url, { method: "POST" });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Multi-Agent 요청에 실패했습니다.");
  return payload;
}

experimentButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    const experiment = button.dataset.experiment;
    setExperimentDisabled(true);
    approvalRequest.hidden = true;
    runResult.hidden = true;
    summary.className = "empty-state";
    summary.textContent = "Diagnostics Agent 실행과 Operations Handoff를 대기 중입니다.";
    setState("RUNNING");
    try {
      const result = await request(`/api/multi-agent/${experiment}/start`);
      renderResult(result);
      if (result.state === "pending_approval") {
        pendingRunId = result.run_id;
        approvalDetail.textContent = `${result.approval.tool_name} ${JSON.stringify(result.approval.tool_arguments)}`;
        approvalRequest.hidden = false;
        approveButton.disabled = false;
        rejectButton.disabled = false;
        summary.textContent = "Operations Agent의 restart_service는 아직 실행되지 않았습니다.";
        setState("WAITING APPROVAL", "warning");
      } else {
        pendingRunId = null;
        summary.textContent = "Agent 실행이 완료됐습니다.";
        setState("COMPLETED", "success");
        setExperimentDisabled(false);
      }
    } catch (error) {
      summary.className = "empty-state error-message";
      summary.textContent = error.message;
      setState("ERROR", "error");
      setExperimentDisabled(false);
    }
  });
});

async function resolve(decision) {
  if (!pendingRunId) return;
  approveButton.disabled = true;
  rejectButton.disabled = true;
  summary.textContent = "동일한 RunState를 재개하는 중입니다.";
  setState("RESUMING");
  try {
    const result = await request(`/api/multi-agent/${pendingRunId}/${decision}`);
    renderResult(result);
    approvalRequest.hidden = true;
    pendingRunId = null;
    summary.textContent = decision === "approve"
      ? "Operations Agent가 승인 후 restart_service를 실행했습니다."
      : "restart_service가 거절되어 실행되지 않았습니다.";
    setState("COMPLETED", "success");
    setExperimentDisabled(false);
  } catch (error) {
    summary.className = "empty-state error-message";
    summary.textContent = error.message;
    setState("ERROR", "error");
  }
}

approveButton.addEventListener("click", () => resolve("approve"));
rejectButton.addEventListener("click", () => resolve("reject"));
