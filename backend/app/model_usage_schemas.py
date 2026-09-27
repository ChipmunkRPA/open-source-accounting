"""Aggregate operational estimates only; no prompts or principal identifiers."""
from pydantic import BaseModel, ConfigDict


class AgentCostCohort(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tracked_runs: int
    completed_runs: int
    active_runs: int
    orphaned_agent_attempts_in_window: int
    unknown_cost_attempts: int
    known_estimate_subtotal_usd: str
    estimated_model_usd_per_completed_run: str | None


class ModelUsageReport(BaseModel):
    model_config = ConfigDict(extra='forbid')
    start_at: int
    end_at: int
    attempts: int
    mock_attempts: int
    pending_attempts: int
    unknown_cost_attempts: int
    known_estimate_subtotal_usd: str
    complete_estimate_usd: str | None
    agent_cohort: AgentCostCohort
    basis: str
