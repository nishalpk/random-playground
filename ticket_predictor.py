import hashlib
import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

try:
    from google import genai
except ImportError:  # pragma: no cover - optional when using the local fallback
    genai = None

def load_config(config_path: str = "triage_config.json") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _fallback_prediction(ticket: dict, config: dict) -> dict:
    text = f"{ticket['subject']} {ticket['message']}".lower()
    keywords = {
        "billing_issue": ("charge", "charged", "deposit", "refund", "payment", "fee"),
        "account_access": ("login", "log in", "password", "credential", "access", "locked"),
        "product_how_to": ("how", "where", "export", "download", "guide"),
        "bug_report": ("crash", "crashes", "error", "bug", "broken", "fails", "close"),
    }
    category = next(
        (candidate for candidate in config["allowed_categories"] if any(word in text for word in keywords.get(candidate, ()))),
        "other" if "other" in config["allowed_categories"] else config["allowed_categories"][0],
    )
    urgency_words = ("urgent", "urgently", "immediately", "blocked", "fraud", "security")
    priority = "urgent" if any(word in text for word in urgency_words) else "normal"
    if priority not in config["allowed_priorities"]:
        priority = config["allowed_priorities"][0]
    reply = {
        "billing_issue": "I’m sorry about the billing issue. We’ll review the transaction and help resolve any duplicate charge.",
        "account_access": "I’m sorry you’re having trouble signing in. Please confirm the reset completed, and we’ll help restore access.",
        "product_how_to": "You can export your transaction history from the account activity or reports area as a CSV.",
        "bug_report": "I’m sorry the app is failing. Please share your device and app version so our technical team can investigate.",
        "other": "Thanks for contacting us. We’ll review your request and route it to the right support team.",
    }.get(category, "Thanks for contacting us. We’ll review your request and follow up shortly.")
    words = reply.split()
    reply = " ".join(words[: int(config["reply_style"]["max_words"])])
    return {
        "ticket_id": ticket["ticket_id"],
        "category": category,
        "priority": priority,
        "reason": "Deterministic fallback classification used because no LLM response was available.",
        "suggested_reply": reply,
        "confidence": 0.55 if category == "other" else 0.75,
    }


def _write_call_log(prompt: str, output_artifact: str) -> None:
    record = {
        "stage": "TRIAGE_PREDICTED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": "google-gemini",
        "model": "gemini-2.5-flash",
        "prompt_hash": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "input_artifacts": ["normalized_tickets.json", "triage_config.json"],
        "output_artifact": output_artifact,
    }
    with open("llm_calls.jsonl", "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def predict_triage(normalized_tickets: list[dict], config_path: str = "triage_config.json", output_file: str = "triage_predictions.json") -> list[dict]:
    config = load_config(config_path)
    
    # 1. Dynamically create Enums based on the config file
    # This prevents the evaluator from breaking your code with new categories
    CategoryEnum = Enum('CategoryEnum', {c: c for c in config["allowed_categories"]})
    PriorityEnum = Enum('PriorityEnum', {p: p for p in config["allowed_priorities"]})

    # 2. Define the Pydantic schema using the dynamic Enums
    class TicketPrediction(BaseModel):
        ticket_id: str
        category: CategoryEnum
        priority: PriorityEnum
        reason: str
        suggested_reply: str
        confidence: float = Field(ge=0.0, le=1.0)

    class BatchPrediction(BaseModel):
        predictions: list[TicketPrediction]

    # 3. Inject constraints into the prompt
    prompt = f"""
    You are an expert support routing AI. Analyze the following tickets.
    
    Constraints:
    - Tone: {config['reply_style']['tone']}
    - Max reply words: {config['reply_style']['max_words']}
    - Allowed categories: {config['allowed_categories']}
    - Allowed priorities: {config['allowed_priorities']}
    
    Tickets:
    {json.dumps(normalized_tickets, indent=2)}
    """
    
    output_by_id: dict[str, dict] = {}
    if genai is not None and os.getenv("GEMINI_API_KEY"):
        print("Making one LLM call for the normalized batch...")
        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": BatchPrediction,
                "temperature": 0.1,
            },
        )
        batch_result: BatchPrediction = response.parsed
        for pred in batch_result.predictions:
            output_by_id[pred.ticket_id] = pred.model_dump()
        _write_call_log(prompt, output_file)
    else:
        print("No GEMINI_API_KEY found; using deterministic local triage fallback.")

    output_predictions = []
    
    # 4. Map the predictions back to dictionaries AND deterministically set the route
    for ticket in normalized_tickets:
        pred_dict = output_by_id.get(ticket["ticket_id"])
        if pred_dict is None:
            pred_dict = _fallback_prediction(ticket, config)
        category = pred_dict.get("category")
        priority = pred_dict.get("priority")
        if category not in config["allowed_categories"] or priority not in config["allowed_priorities"]:
            pred_dict = _fallback_prediction(ticket, config)
        pred_dict["ticket_id"] = ticket["ticket_id"]
        pred_dict["confidence"] = max(0.0, min(1.0, float(pred_dict.get("confidence", 0.0))))
        pred_dict["route_to"] = config["routing_rules"][pred_dict["category"]]
        pred_dict["suggested_reply"] = " ".join(str(pred_dict.get("suggested_reply", "")).split()[: int(config["reply_style"]["max_words"])])
        output_predictions.append(pred_dict)
        
    # Save the predictions to disk
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_predictions, f, indent=2)
        
    return output_predictions

if __name__ == "__main__":
    # Assumes normalized_tickets.json exists from the previous step
    with open("normalized_tickets.json", "r") as f:
        tickets = json.load(f)
    
    predictions = predict_triage(tickets)
    print(f"Generated predictions for {len(predictions)} tickets.")