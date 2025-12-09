"""Payme payment gateway router.

This module implements all Payme Merchant API endpoints using JSON-RPC 2.0 protocol.

Key endpoints:
1. Merchant API (JSON-RPC 2.0) - For Payme callbacks
   - CheckPerformTransaction
   - CreateTransaction
   - PerformTransaction
   - CancelTransaction
   - CheckTransaction
   - GetStatement

2. Frontend API (REST) - For mobile app/web
   - Initialize payment
   - Check transaction status
   - Get transaction history

Reference: https://developer.help.paycom.uz/
"""
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy.orm import Session

from dependencies.database import get_db
from dependencies.auth import get_current_user
from models import User, PaymeTransaction
from services.payme_service import PaymeService
from config import settings
from .schemas import (
    JSONRPCRequest,
    JSONRPCResponse,
    PaymentInitRequest,
    PaymentInitResponse,
    TransactionStatusRequest,
    TransactionStatusResponse,
    TransactionListResponse
)

logger = structlog.get_logger()
router = APIRouter()


@router.post("", response_model=JSONRPCResponse)
async def payme_merchant_api(
        request_data: JSONRPCRequest,
        request: Request,
        authorization: str = Header(None),
        db: Session = Depends(get_db)
):
    """
    Payme Merchant API endpoint (JSON-RPC 2.0).

    This endpoint handles all Payme callbacks using JSON-RPC 2.0 protocol.
    Payme will call this endpoint to process transactions.

    Endpoint URL: https://ai.mavu.app/api/v1/payme/

    Security:
        - Validates HTTP Basic Auth with PAYME_LOGIN and PAYME_KEY
        - Only accepts requests from Payme servers

    Methods:
        - CheckPerformTransaction: Check if transaction can be performed
        - CreateTransaction: Create a new transaction
        - PerformTransaction: Confirm and complete transaction
        - CancelTransaction: Cancel transaction
        - CheckTransaction: Get transaction status
        - GetStatement: Get transactions for a time period

    Note:
        This endpoint must be registered in Payme merchant dashboard as:
        https://ai.mavu.app/api/v1/payme/
    """
    # Validate authorization
    is_valid, error_msg = PaymeService.validate_auth(authorization)
    if not is_valid:
        logger.warning("Unauthorized Payme request", error=error_msg)
        return JSONRPCResponse(
            id=request_data.id,
            error={
                "code": PaymeService.ERROR_INSUFFICIENT_PRIVILEGE,
                "message": "Insufficient privilege to perform this operation",
                "data": error_msg
            }
        )

    # Route to appropriate handler based on method
    method = request_data.method
    params = request_data.params

    logger.info("Payme merchant API request", method=method, params=params)

    try:
        if method == "CheckPerformTransaction":
            return handle_check_perform_transaction(request_data, params, db)

        elif method == "CreateTransaction":
            return handle_create_transaction(request_data, params, db)

        elif method == "PerformTransaction":
            return handle_perform_transaction(request_data, params, db)

        elif method == "CancelTransaction":
            return handle_cancel_transaction(request_data, params, db)

        elif method == "CheckTransaction":
            return handle_check_transaction(request_data, params, db)

        elif method == "GetStatement":
            return handle_get_statement(request_data, params, db)

        else:
            logger.warning("Unknown method", method=method)
            return JSONRPCResponse(
                id=request_data.id,
                error={
                    "code": PaymeService.ERROR_METHOD_NOT_FOUND,
                    "message": "Method not found",
                    "data": method
                }
            )

    except Exception as e:
        logger.error("Error processing Payme request", method=method, error=str(e))
        return JSONRPCResponse(
            id=request_data.id,
            error={
                "code": PaymeService.ERROR_INTERNAL_SYSTEM,
                "message": "Internal server error",
                "data": str(e)
            }
        )


def handle_check_perform_transaction(
        request_data: JSONRPCRequest,
        params: dict,
        db: Session
) -> JSONRPCResponse:
    """Handle CheckPerformTransaction method."""
    amount = params.get("amount")
    account = params.get("account", {})
    promo_code_id = account.get("promo_code_id")

    if not amount or not promo_code_id:
        return JSONRPCResponse(
            id=request_data.id,
            error={
                "code": PaymeService.ERROR_INVALID_JSON_RPC_OBJECT,
                "message": "Invalid JSON-RPC object",
                "data": "Missing amount or promo_code_id"
            }
        )

    success, error = PaymeService.check_perform_transaction(amount, promo_code_id, db)

    if not success:
        return JSONRPCResponse(id=request_data.id, error=error)

    return JSONRPCResponse(
        id=request_data.id,
        result={"allow": True}
    )


def handle_create_transaction(
        request_data: JSONRPCRequest,
        params: dict,
        db: Session
) -> JSONRPCResponse:
    """Handle CreateTransaction method."""
    transaction_id = params.get("id")
    time = params.get("time")
    amount = params.get("amount")
    account = params.get("account", {})
    promo_code_id = account.get("promo_code_id")

    if not all([transaction_id, time, amount, promo_code_id]):
        return JSONRPCResponse(
            id=request_data.id,
            error={
                "code": PaymeService.ERROR_INVALID_JSON_RPC_OBJECT,
                "message": "Invalid JSON-RPC object",
                "data": "Missing required parameters"
            }
        )

    # For now, we'll assume user_id is part of the order context
    # In production, you might want to store user_id with the promo code
    # or pass it as part of the account parameters
    from models import PromoCode
    promo_code = db.query(PromoCode).filter(PromoCode.id == promo_code_id).first()
    if not promo_code:
        return JSONRPCResponse(
            id=request_data.id,
            error={
                "code": PaymeService.ERROR_INVALID_ACCOUNT,
                "message": "Invalid account"
            }
        )

    # Use the user_id from promo_code if it exists, otherwise use a placeholder
    # In a real scenario, the promo_code should have a user_id or you should get it from context
    user_id = promo_code.user_id if promo_code.user_id else 1  # Fallback to admin

    transaction, error = PaymeService.create_transaction(
        transaction_id, time, amount, promo_code_id, user_id, db
    )

    if error:
        return JSONRPCResponse(id=request_data.id, error=error)

    return JSONRPCResponse(
        id=request_data.id,
        result=transaction.to_payme_format()
    )


def handle_perform_transaction(
        request_data: JSONRPCRequest,
        params: dict,
        db: Session
) -> JSONRPCResponse:
    """Handle PerformTransaction method."""
    transaction_id = params.get("id")

    if not transaction_id:
        return JSONRPCResponse(
            id=request_data.id,
            error={
                "code": PaymeService.ERROR_INVALID_JSON_RPC_OBJECT,
                "message": "Invalid JSON-RPC object",
                "data": "Missing transaction id"
            }
        )

    transaction, error = PaymeService.perform_transaction(transaction_id, db)

    if error:
        return JSONRPCResponse(id=request_data.id, error=error)

    return JSONRPCResponse(
        id=request_data.id,
        result=transaction.to_payme_format()
    )


def handle_cancel_transaction(
        request_data: JSONRPCRequest,
        params: dict,
        db: Session
) -> JSONRPCResponse:
    """Handle CancelTransaction method."""
    transaction_id = params.get("id")
    reason = params.get("reason")

    if not transaction_id or reason is None:
        return JSONRPCResponse(
            id=request_data.id,
            error={
                "code": PaymeService.ERROR_INVALID_JSON_RPC_OBJECT,
                "message": "Invalid JSON-RPC object",
                "data": "Missing transaction id or reason"
            }
        )

    transaction, error = PaymeService.cancel_transaction(transaction_id, reason, db)

    if error:
        return JSONRPCResponse(id=request_data.id, error=error)

    return JSONRPCResponse(
        id=request_data.id,
        result=transaction.to_payme_format()
    )


def handle_check_transaction(
        request_data: JSONRPCRequest,
        params: dict,
        db: Session
) -> JSONRPCResponse:
    """Handle CheckTransaction method."""
    transaction_id = params.get("id")

    if not transaction_id:
        return JSONRPCResponse(
            id=request_data.id,
            error={
                "code": PaymeService.ERROR_INVALID_JSON_RPC_OBJECT,
                "message": "Invalid JSON-RPC object",
                "data": "Missing transaction id"
            }
        )

    transaction, error = PaymeService.check_transaction(transaction_id, db)

    if error:
        return JSONRPCResponse(id=request_data.id, error=error)

    return JSONRPCResponse(
        id=request_data.id,
        result=transaction.to_payme_format()
    )


def handle_get_statement(
        request_data: JSONRPCRequest,
        params: dict,
        db: Session
) -> JSONRPCResponse:
    """Handle GetStatement method."""
    from_time = params.get("from")
    to_time = params.get("to")

    if from_time is None or to_time is None:
        return JSONRPCResponse(
            id=request_data.id,
            error={
                "code": PaymeService.ERROR_INVALID_JSON_RPC_OBJECT,
                "message": "Invalid JSON-RPC object",
                "data": "Missing from or to parameters"
            }
        )

    transactions = PaymeService.get_statement(from_time, to_time, db)

    return JSONRPCResponse(
        id=request_data.id,
        result={
            "transactions": [t.to_payme_format() for t in transactions]
        }
    )


# Frontend API endpoints (REST)

@router.post("/init", response_model=PaymentInitResponse)
async def initialize_payment(
        request_data: PaymentInitRequest,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Initialize a payment for the frontend.

    This endpoint generates a Payme checkout URL that the frontend can use
    to redirect the user to Payme payment page.

    Flow:
        1. Validate user and promo code
        2. Generate payment URL with encoded parameters
        3. Return URL to frontend
        4. Frontend redirects user to Payme
        5. User completes payment
        6. Payme calls merchant API webhook
        7. Frontend checks transaction status

    Args:
        request_data: Payment initialization request
        user: Current authenticated user
        db: Database session

    Returns:
        PaymentInitResponse with Payme checkout URL
    """
    try:
        # Validate promo code exists and is available
        is_valid, error_msg, promo_code = PaymeService.validate_account(
            request_data.promo_code_id, db
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Use provided amount or default APP_PRICE
        amount = request_data.amount if request_data.amount else settings.app_price

        # Validate amount
        if not PaymeService.validate_amount(amount):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid amount. Expected {settings.app_price} tiyin"
            )

        # Generate payment URL
        payment_url = PaymeService.generate_payment_url(
            user_id=user.id,
            promo_code_id=request_data.promo_code_id,
            amount=amount
        )

        logger.info(
            "Payment initialized",
            user_id=user.id,
            promo_code_id=request_data.promo_code_id,
            amount=amount
        )

        return PaymentInitResponse(
            payment_url=payment_url,
            merchant_id=settings.payme_merchant_id,
            amount=amount,
            promo_code_id=request_data.promo_code_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error initializing payment", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize payment"
        )


@router.get("/status/{transaction_id}", response_model=TransactionStatusResponse)
async def get_transaction_status(
        transaction_id: str,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get transaction status.

    Allows users to check the status of their payment transactions.

    Args:
        transaction_id: Payme transaction ID
        user: Current authenticated user
        db: Database session

    Returns:
        TransactionStatusResponse with transaction details
    """
    try:
        transaction, error = PaymeService.check_transaction(transaction_id, db)

        if error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        # Verify transaction belongs to user
        if transaction.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        return TransactionStatusResponse(
            transaction_id=transaction.transaction_id,
            status=transaction.status,
            status_display=transaction.status_display,
            amount=transaction.amount,
            user_id=transaction.user_id,
            promo_code_id=transaction.promo_code_id,
            created_at=transaction.created_at,
            perform_time=transaction.perform_time,
            cancel_time=transaction.cancel_time,
            reason=transaction.reason,
            reason_display=transaction.reason_display
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting transaction status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transaction status"
        )


@router.get("/transactions", response_model=TransactionListResponse)
async def get_user_transactions(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get user's transaction history.

    Returns all payment transactions for the authenticated user.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        TransactionListResponse with list of transactions
    """
    try:
        transactions = db.query(PaymeTransaction).filter(
            PaymeTransaction.user_id == user.id
        ).order_by(PaymeTransaction.created_at.desc()).all()

        transaction_list = [
            TransactionStatusResponse(
                transaction_id=t.transaction_id,
                status=t.status,
                status_display=t.status_display,
                amount=t.amount,
                user_id=t.user_id,
                promo_code_id=t.promo_code_id,
                created_at=t.created_at,
                perform_time=t.perform_time,
                cancel_time=t.cancel_time,
                reason=t.reason,
                reason_display=t.reason_display
            )
            for t in transactions
        ]

        logger.info("Retrieved user transactions", user_id=user.id, count=len(transactions))

        return TransactionListResponse(
            transactions=transaction_list,
            total=len(transactions)
        )

    except Exception as e:
        logger.error("Error getting user transactions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transactions"
        )
