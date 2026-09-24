import json
from pathlib import Path

from final_output import validate_pipeline
from human_review import human_review_and_finalize
from normalizer import normalize_tickets
from ticket_predictor import predict_triage


def run_pipeline() -> None:
    state = "INIT"
    root = Path(__file__).resolve().parent
    normalized_path = root / "normalized_tickets.json"
    prediction_path = root / "triage_predictions.json"

    tickets = normalize_tickets(str(root / "tickets.json"), str(normalized_path))
    state = "TICKETS_NORMALIZED"
    with open(root / "triage_config.json", encoding="utf-8") as handle:
        config = json.load(handle)
    predictions = predict_triage(tickets, str(root / "triage_config.json"), str(prediction_path))
    if len(predictions) != len(tickets):
        raise RuntimeError("Prediction stage did not produce exactly one result per ticket.")
    state = "TRIAGE_PREDICTED"
    human_review_and_finalize(str(root / "triage_config.json"), str(prediction_path), root)
    state = "HUMAN_REVIEW_COMPLETE"
    state = "FINAL_QUEUE_GENERATED"
    validate_pipeline(root)
    state = "VALIDATION_COMPLETE"
    state = "RESULTS_FINALISED"
    print(f"Pipeline complete: {state} ({len(tickets)} tickets, {len(config['allowed_categories'])} configured categories).")


if __name__ == "__main__":
    run_pipeline()