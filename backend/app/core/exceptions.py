from typing import Any, Dict, Optional


class MeshBaseException(Exception):
    """Base exception for Federated Agentic Mesh."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(MeshBaseException):
    """Raised when authentication fails."""
    pass


class PermissionDeniedError(MeshBaseException):
    """Raised when an operation violates department or role boundaries."""
    pass


class NotFoundError(MeshBaseException):
    """Raised when a requested resource is not found."""
    pass


class GatewayPolicyError(MeshBaseException):
    """Raised when the Federation Gateway blocks a cross-department request."""
    pass


class ApprovalRequiredError(MeshBaseException):
    """Raised when an operation requires explicit human approval before execution."""
    def __init__(self, message: str, approval_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.approval_id = approval_id


class LLMServiceUnavailableError(MeshBaseException):
    """Raised when local Ollama service is unreachable or errors."""
    pass


class DocumentProcessingError(MeshBaseException):
    """Raised when document ingestion or chunking fails."""
    pass
