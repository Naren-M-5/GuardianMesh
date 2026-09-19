from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    decision: str
    reason: str


ALLOWED = {"create_incident", "send_dashboard_alert", "send_owner_notification",
           "preserve_evidence", "generate_summary", "close_incident"}
CONFIRM = {"activate_deterrence", "request_external_contact"}
DENIED = {"claim_police_contacted", "diagnose_medical_condition",
          "identify_unknown_person", "autonomous_emergency_call"}


def authorize(action: str) -> PolicyDecision:
    if action in DENIED:
        return PolicyDecision("deny", "This action violates a hard safety boundary.")
    if action in CONFIRM:
        return PolicyDecision("require_confirmation", "Human confirmation is required.")
    if action in ALLOWED:
        return PolicyDecision("allow", "The action is permitted by the V1 policy.")
    return PolicyDecision("deny", "Unknown actions are denied by default.")
