import json
import os
from collections import Counter

def human_review_and_finalize():
    # Load configuration and predictions
    with open("triage_config.json", "r") as f:
        config = json.load(f)
    
    with open("triage_predictions.json", "r") as f:
        predictions = json.load(f)

    print("\n--- HUMAN REVIEW CHECKPOINT ---")
    print("Predicted Tickets:")
    for p in predictions:
        print(f"[{p['ticket_id']}] Category: {p['category']} | Priority: {p['priority']}")
    
    print("\nEnter any overrides as: ticket_id,category,priority")
    print("Press Enter on an empty line when done.")
    
    overrides = []
    
    # Review loop
    while True:
        user_input = input("> ").strip()
        if not user_input:
            break
        
        try:
            tid, new_cat, new_pri = [x.strip() for x in user_input.split(",")]
            
            # Validate against config
            if new_cat not in config["allowed_categories"]:
                print(f"Invalid category. Allowed: {config['allowed_categories']}")
                continue
            if new_pri not in config["allowed_priorities"]:
                print(f"Invalid priority. Allowed: {config['allowed_priorities']}")
                continue
                
            # Find the ticket and apply override
            for p in predictions:
                if p["ticket_id"] == tid:
                    overrides.append({
                        "ticket_id": tid,
                        "old_category": p["category"],
                        "new_category": new_cat,
                        "old_priority": p["priority"],
                        "new_priority": new_pri
                    })
                    p["category"] = new_cat
                    p["priority"] = new_pri
                    p["was_overridden"] = True
                    
                    # Recompute route if category changed
                    p["route_to"] = config["routing_rules"].get(new_cat, config["routing_rules"]["other"])
                    print(f"✅ Override applied to {tid}")
                    break
            else:
                print(f"Ticket {tid} not found.")
                
        except ValueError:
            print("Invalid format. Use: ticket_id,category,priority")

    # Save overrides log
    with open("review_overrides.json", "w") as f:
        json.dump(overrides, f, indent=2)

    # Generate Final Queue
    final_queue = []
    escalations = []
    
    for p in predictions:
        final_ticket = {
            "ticket_id": p["ticket_id"],
            "final_category": p["category"],
            "final_priority": p["priority"],
            "final_route_to": p["route_to"],
            "suggested_reply": p["suggested_reply"],
            "was_overridden": p.get("was_overridden", False)
        }
        final_queue.append(final_ticket)
        
        # Apply escalation logic deterministically
        if p["category"] == "other" or p.get("confidence", 1.0) < 0.60:
            escalations.append(p)

    # Save outputs
    with open("final_queue.json", "w") as f:
        json.dump(final_queue, f, indent=2)
        
    with open("escalations.json", "w") as f:
        json.dump(escalations, f, indent=2)

    # Generate Markdown Summary
    total_tickets = len(final_queue)
    cat_counts = Counter([t["final_category"] for t in final_queue])
    pri_counts = Counter([t["final_priority"] for t in final_queue])
    route_counts = Counter([t["final_route_to"] for t in final_queue])
    overridden_ids = [o["ticket_id"] for o in overrides]

    summary = f"""# Queue Summary

**Total Tickets Processed:** {total_tickets}

## By Category
"""
    for cat, count in cat_counts.items():
        summary += f"- **{cat}**: {count}\n"
        
    summary += "\n## By Priority\n"
    for pri, count in pri_counts.items():
        summary += f"- **{pri}**: {count}\n"

    summary += "\n## Queue Breakdown (Routing)\n"
    for route, count in route_counts.items():
        summary += f"- **{route}**: {count}\n"

    summary += "\n## Manual Overrides\n"
    if overridden_ids:
        for tid in overridden_ids:
            summary += f"- {tid}\n"
    else:
        summary += "- No overrides applied.\n"

    with open("queue_summary.md", "w") as f:
        f.write(summary)
        
    print("✅ Stage 3 & 4 Complete. Final queue and summaries generated.")

if __name__ == "__main__":
    human_review_and_finalize()