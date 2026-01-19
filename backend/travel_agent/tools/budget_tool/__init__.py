"""
Budget Tool Module

This module provides budget calculation and validation for the Agentic AI Travel Planner.
It computes costs based on selected travel options (flights, hotels, activities) and
validates them against the user's budget.

Public API:
    - calculate_budget: Compute and validate trip budget
    - BudgetCalculationResult: Result object with breakdown and validation status

Architecture:
    - budget_tool.py: Pure computation and validation (no external data sources)
"""

# Lazy import to avoid circular dependencies
def __getattr__(name):
    if name == "calculate_budget":
        from .budget_tool import calculate_budget
        return calculate_budget
    elif name == "BudgetCalculationResult":
        from .budget_tool import BudgetCalculationResult
        return BudgetCalculationResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["calculate_budget", "BudgetCalculationResult"]
