class ApplicationError(Exception):
    status_code = 500
    error_type = "application_error"


class ConfigurationError(ApplicationError):
    status_code = 503
    error_type = "configuration_error"


class BackendConnectionError(ApplicationError):
    status_code = 503
    error_type = "backend_connection_error"


class ServiceNotFoundError(ApplicationError):
    status_code = 404
    error_type = "service_not_found"


class BackendResponseError(ApplicationError):
    status_code = 502
    error_type = "backend_response_error"


class FunctionToolError(ApplicationError):
    status_code = 502
    error_type = "function_tool_error"


class StructuredOutputError(ApplicationError):
    status_code = 502
    error_type = "structured_output_error"


class LlmResponseError(ApplicationError):
    status_code = 502
    error_type = "llm_response_error"


class AgentRunError(ApplicationError):
    status_code = 502
    error_type = "agent_run_error"
