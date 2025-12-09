"""Pydantic schemas for Payme payment integration.

This module defines all request and response schemas for Payme JSON-RPC 2.0 protocol.
Payme uses JSON-RPC 2.0 for merchant API communication.

Reference: https://developer.help.paycom.uz/
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# JSON-RPC 2.0 Base Schemas
class JSONRPCRequest(BaseModel):
    """Base JSON-RPC 2.0 request schema."""
    jsonrpc: str = "2.0"
    id: int
    method: str
    params: Dict[str, Any]


class JSONRPCResponse(BaseModel):
    """Base JSON-RPC 2.0 response schema."""
    jsonrpc: str = "2.0"
    id: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


# Payme Method-Specific Schemas
class AccountParams(BaseModel):
    """Account parameters for identifying the promo_code/user."""
    promo_code_id: int = Field(..., description="Promo code ID being purchased")


class CheckPerformTransactionParams(BaseModel):
    """Parameters for CheckPerformTransaction method."""
    amount: int = Field(..., description="Transaction amount in tiyin (1 UZS = 100 tiyin)")
    account: AccountParams


class CreateTransactionParams(BaseModel):
    """Parameters for CreateTransaction method."""
    id: str = Field(..., description="Unique transaction ID from Payme")
    time: int = Field(..., description="Transaction creation timestamp in milliseconds")
    amount: int = Field(..., description="Transaction amount in tiyin")
    account: AccountParams


class PerformTransactionParams(BaseModel):
    """Parameters for PerformTransaction method."""
    id: str = Field(..., description="Transaction ID from Payme")


class CancelTransactionParams(BaseModel):
    """Parameters for CancelTransaction method."""
    id: str = Field(..., description="Transaction ID from Payme")
    reason: int = Field(..., description="Cancellation reason code")


class CheckTransactionParams(BaseModel):
    """Parameters for CheckTransaction method."""
    id: str = Field(..., description="Transaction ID from Payme")


class GetStatementParams(BaseModel):
    """Parameters for GetStatement method."""
    from_: int = Field(..., alias="from", description="Start timestamp in milliseconds")
    to: int = Field(..., description="End timestamp in milliseconds")

    model_config = {"populate_by_name": True}


# Response Result Schemas
class TransactionResult(BaseModel):
    """Transaction result for various Payme methods."""
    create_time: int = Field(..., description="Transaction creation time in milliseconds")
    perform_time: int = Field(0, description="Transaction perform time in milliseconds")
    cancel_time: int = Field(0, description="Transaction cancel time in milliseconds")
    transaction: str = Field(..., description="Internal transaction ID")
    state: int = Field(..., description="Transaction state")
    reason: Optional[int] = Field(None, description="Cancellation reason")

    model_config = {"populate_by_name": True}


class CheckPerformTransactionResult(BaseModel):
    """Result for CheckPerformTransaction method."""
    allow: bool = Field(True, description="Whether transaction is allowed")

    model_config = {"populate_by_name": True}


class PerformTransactionResult(TransactionResult):
    """Result for PerformTransaction method."""
    pass


class CancelTransactionResult(TransactionResult):
    """Result for CancelTransaction method."""
    pass


class CheckTransactionResult(TransactionResult):
    """Result for CheckTransaction method."""
    pass


class GetStatementResult(BaseModel):
    """Result for GetStatement method."""
    transactions: list[TransactionResult]


# Error Schema
class PaymeError(BaseModel):
    """Payme error response schema."""
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message in English")
    data: Optional[str] = Field(None, description="Additional error details")


# Payment Initialization (for frontend)
class PaymentInitRequest(BaseModel):
    """Request to initialize a payment (from mobile app/frontend)."""
    user_id: int = Field(..., description="User ID making the payment")
    promo_code_id: int = Field(..., description="Promo code ID to purchase")
    amount: Optional[int] = Field(None, description="Payment amount in tiyin (defaults to APP_PRICE)")


class PaymentInitResponse(BaseModel):
    """Response with payment URL for frontend."""
    payment_url: str = Field(..., description="Payme checkout URL")
    merchant_id: str = Field(..., description="Merchant ID")
    amount: int = Field(..., description="Amount in tiyin")
    promo_code_id: int = Field(..., description="Promo code ID")


# Transaction Status Check (for frontend)
class TransactionStatusRequest(BaseModel):
    """Request to check transaction status."""
    transaction_id: str = Field(..., description="Payme transaction ID")


class TransactionStatusResponse(BaseModel):
    """Response with transaction status."""
    transaction_id: str
    status: int = Field(..., description="Transaction status")
    status_display: str = Field(..., description="Human-readable status")
    amount: int
    user_id: int
    promo_code_id: int
    created_at: datetime
    perform_time: Optional[datetime] = None
    cancel_time: Optional[datetime] = None
    reason: Optional[int] = None
    reason_display: Optional[str] = None


# Transaction List (for user history)
class TransactionListResponse(BaseModel):
    """Response with list of user transactions."""
    transactions: list[TransactionStatusResponse]
    total: int = Field(..., description="Total number of transactions")
