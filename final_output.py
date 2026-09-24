import json
import os

def validate_pipeline():
    required_files = [
        "tickets.json",
        "triage_config.json",
        "normalized_tickets.json",
        "triage_predictions.json",
        "review_overrides.json",
        "final_queue.json",
        "queue_summary.md"
    ]
    
    print("Running Pipeline Validation...")
    
    # 1. Check if files exist
    for f in required_files:
        assert os.path.exists(f), f"❌ Missing required file: {f}"
    print("✅ All required artifacts present.")
    
    # Load data
    with open("tickets.json", "r") as f:
        raw = json.load(f)
    with open("triage_config.json", "r") as f:
        config = json.load(f)
    with open("final_queue.json", "r") as f:
        final_queue = json.load(f)
        
    # 2. Check counts
    assert len(raw) == len(final_queue), "❌ Final queue count does not match input count."
    print("✅ Ticket counts match.")
    
    # 3. Check constraints on final data
    max_words = config["reply_style"]["max_words"]
    
    for ticket in final_queue:
        # Verify strict enums
        assert ticket["final_category"] in config["allowed_categories"], f"❌ Invalid category in {ticket['ticket_id']}"
        assert ticket["final_priority"] in config["allowed_priorities"], f"❌ Invalid priority in {ticket['ticket_id']}"
        
        # Verify deterministic routing
        expected_route = config["routing_rules"].get(ticket["final_category"])
        assert ticket["final_route_to"] == expected_route, f"❌ Route mismatch for {ticket['ticket_id']}"
        
        # Verify reply length
        word_count = len(ticket["suggested_reply"].split())
        assert word_count <= max_words, f"❌ Reply too long for {ticket['ticket_id']} ({word_count} words)"
        
    print("✅ All categories, priorities, and routes strictly follow the configuration.")
    print("✅ Reply word limits respected.")
    print("\n🎉 Validation passed successfully!")

if __name__ == "__main__":
    validate_pipeline()