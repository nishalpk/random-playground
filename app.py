from normalizer import normalize_tickets
from ticket_predictor import predict_triage
from human_review import human_review_and_finalize
from final_output import validate_pipeline

normalized_tickets = normalize_tickets()
predictions = predict_triage(normalized_tickets)
human_review_and_finalize()
validate_pipeline()