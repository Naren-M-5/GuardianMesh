type RecordValue = Record<string, unknown>;

export function eventSourceLabel(event: RecordValue): string {
  const value = event.integrity;
  const integrity: RecordValue = value && typeof value === "object" && !Array.isArray(value)
    ? value as RecordValue : {};
  if (integrity.simulation_declared === true) return "Simulation (sender-declared)";
  // Older history imports used this server-set flag before ingestion_method existed.
  // History includes Playground sessions; it is not proof of a physical camera.
  if (event.source === "ring" && (integrity.ingestion_method === "ring_history"
      || (integrity.ingestion_method == null && integrity.authenticated_source === true))) {
    return "Ring history (may include Playground)";
  }
  if (integrity.ingestion_method === "webhook") return "Webhook (origin unconfirmed)";
  return "Source unconfirmed (legacy event)";
}
