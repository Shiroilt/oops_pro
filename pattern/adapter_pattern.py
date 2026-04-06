"""
File: patterns/adapter_pattern.py
Purpose: Re-exports and documents the Adapter pattern classes from payment/adapter.py.
         This file exists to keep the patterns/ folder as a clear reference
         for all design patterns used in the system.

ADAPTER PATTERN SUMMARY:
─────────────────────────────────────────────────────────────────
Problem:
    CreditCard, UPI, and Digital Wallet all have different incompatible APIs.
    The kiosk cannot depend on any specific provider.

Solution:
    Define a common PaymentProcessor interface (Target).
    Wrap each third-party API in an Adapter that implements PaymentProcessor.
    The kiosk only depends on PaymentProcessor — provider can be swapped freely.

Participants:
    Target      → PaymentProcessor       (payment/payment_interface.py)
    Adaptee 1   → UPISystemAPI           (payment/upi_payment.py)
    Adaptee 2   → CardGatewayAPI         (payment/card_payment.py)
    Adaptee 3   → DigitalWalletAPI       (payment/adapter.py)
    Adapter 1   → UPIAdapter             (payment/adapter.py)
    Adapter 2   → CardAdapter            (payment/adapter.py)
    Adapter 3   → DigitalWalletAdapter   (payment/adapter.py)
    Client      → KioskInterface         (core/kiosk_interface.py)
─────────────────────────────────────────────────────────────────
"""

# Re-export for convenience
from payment.adapter import UPIAdapter, CardAdapter, DigitalWalletAdapter
from payment.payment_interface import PaymentProcessor

__all__ = ["PaymentProcessor", "UPIAdapter", "CardAdapter", "DigitalWalletAdapter"]
