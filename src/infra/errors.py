"""
Error handling module for the application.
Defines custom exceptions and error response models following RFC 7807.
"""
from dataclasses import dataclass
from typing import Optional
from abc import ABC, abstractmethod
from fastapi import status

@dataclass
class ErrorDetail:
    """Model for RFC 7807 Problem Details for HTTP APIs."""
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None

class AppError(ABC):
    """Base class for application errors that can be converted to HTTP responses."""
    @abstractmethod
    def to_error_detail(self) -> ErrorDetail:
        """Convert the error to a standardized error detail."""
        pass

class DomainError(Exception, AppError):
    """Base class for domain-specific errors."""
    def __init__(self, detail: str, title: str = "Domain Error") -> None:
        """
        Initialize domain error.
        
        Args:
            detail: Detailed error message
            title: Short error title
        """
        super().__init__(detail)
        self.detail = detail
        self.title = title
    
    def to_error_detail(self) -> ErrorDetail:
        """Convert to standard error detail format."""
        return ErrorDetail(
            type="https://api.pizza.com/errors/domain",
            title=self.title,
            status=status.HTTP_400_BAD_REQUEST,
            detail=self.detail
        )

class ValidationError(Exception, AppError):
    """Error for request validation failures."""
    def __init__(self, detail: str) -> None:
        """
        Initialize validation error.
        
        Args:
            detail: Validation error details
        """
        super().__init__(detail)
        self.detail = detail
    
    def to_error_detail(self) -> ErrorDetail:
        """Convert to standard error detail format."""
        return ErrorDetail(
            type="https://api.pizza.com/errors/validation",
            title="Validation Error",
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=self.detail
        )

class AuthenticationError(Exception, AppError):
    """Error for authentication failures."""
    def __init__(self, detail: str = "Authentication failed") -> None:
        """
        Initialize authentication error.
        
        Args:
            detail: Authentication error details
        """
        super().__init__(detail)
        self.detail = detail
    
    def to_error_detail(self) -> ErrorDetail:
        """Convert to standard error detail format."""
        return ErrorDetail(
            type="https://api.pizza.com/errors/auth",
            title="Authentication Error",
            status=status.HTTP_401_UNAUTHORIZED,
            detail=self.detail
        )