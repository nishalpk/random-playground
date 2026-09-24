import json
import os

def normalize_tickets(input_file: str = "tickets.json", output_file: str = "normalized_tickets.json") -> list[dict]:
    """
    Reads raw tickets, deterministically builds the text for the model,
    calculates character counts, and saves the normalized data.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file {input_file} not found.")

    with open(input_file, "r", encoding="utf-8") as f:
        raw_tickets = json.load(f)

    normalized_tickets = []
    
    for ticket in raw_tickets:
        # Deterministically build the string that the LLM will see
        text_for_model = f"Subject: {ticket['subject']}\nMessage: {ticket['message']}"
        
        normalized_ticket = {
            "ticket_id": ticket["ticket_id"],
            "subject": ticket["subject"],
            "message": ticket["message"],
            "channel": ticket["channel"],
            "created_at": ticket["created_at"],
            "text_for_model": text_for_model,
            "char_count": len(text_for_model)
        }
        
        normalized_tickets.append(normalized_ticket)

    # Save to disk
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(normalized_tickets, f, indent=2)
        
    print(f"✅ Normalization complete. Saved {len(normalized_tickets)} tickets to {output_file}")
    
    return normalized_tickets

# Example execution if run directly
if __name__ == "__main__":
    normalize_tickets()