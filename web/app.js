const verifyButton = document.querySelector("#verify-mcp");
const state = document.querySelector("#run-state");
const summary = document.querySelector("#result-summary");
const verification = document.querySelector("#verification");
const discovery = document.querySelector("#tool-discovery");
const toolCalls = document.querySelector("#tool-calls");
const endToEnd = document.querySelector("#end-to-end");

function setState(label, tone = "") {
  state.textContent = label;
  state.className = `status-chip ${tone}`;
}

verifyButton.addEventListener("click", async () => {
  verifyButton.disabled = true;
  verification.hidden = true;
  summary.className = "empty-state";
  summary.textContent = "stdio MCP Server에 연결해 Tool Discovery와 Tool Call을 실행 중입니다.";
  setState("RUNNING");

  try {
    const response = await fetch("/api/mcp/verification", { method: "POST" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "MCP 검증 요청에 실패했습니다.");

    discovery.textContent = JSON.stringify(payload.tools, null, 2);
    toolCalls.textContent = JSON.stringify(payload.tool_calls, null, 2);
    endToEnd.textContent = `END-TO-END TIME / ${payload.end_to_end_ms.toFixed(2)} ms`;
    summary.textContent = "실제 stdio MCP Discovery와 세 Tool Call 결과입니다.";
    verification.hidden = false;
    setState("SUCCESS", "success");
  } catch (error) {
    summary.className = "empty-state error-message";
    summary.textContent = error.message;
    setState("ERROR", "error");
  } finally {
    verifyButton.disabled = false;
  }
});
