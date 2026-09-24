# AI Support Ticket Triage Pipeline

An automated, replayable pipeline that classifies customer support tickets using LLMs. This project combines strict deterministic preprocessing/routing with the reasoning capabilities of Gemini 2.5 Flash, enforcing a controlled label set via Pydantic structured outputs and including a human-in-the-loop review checkpoint.

## 🏗️ Architecture

The pipeline strictly enforces these sequential stages to prevent LLM hallucinations from breaking downstream systems:

1. **Deterministic Normalization (`normalizer.py`)**: Reads raw `tickets.json` and deterministically builds the exact text strings the model will see.
2. **LLM Prediction (`ticket_predictor.py`)**: Uses the `google-genai` SDK and Pydantic `BaseModel` to dynamically enforce the allowed categories, priorities, and reply guidelines from `triage_config.json`.
3. **Deterministic Routing**: Maps the predicted category to a specific queue using hardcoded configuration rules. *The LLM is explicitly prevented from guessing routes.*
4. **Human Review Checkpoint (`human_review.py`)**: An interactive CLI that pauses execution, allowing an agent to override the model's predictions. Routing is re-calculated automatically if a category is changed.
5. **Output Generation**: Produces the final structured queue (`final_queue.json`) and a Markdown summary (`queue_summary.md`).
6. **Validation (`final_output.py`)**: A strict verification script ensuring all final artifacts adhere to the original configuration constraints.

## ⚙️ Prerequisites

- Python 3.10+
- A valid Google Gemini API Key
- `pip install google-genai pydantic`

## 🚀 Setup & Execution

1. Clone the repository and navigate to the project directory.
2. Export your API key:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
Run the pipeline:

Bash
python main.py
Follow the interactive CLI prompts to review or override the LLM's predictions.

📂 Project Structure
main.py: The orchestrator script that executes the pipeline stages sequentially.

tickets.json: Input file containing raw customer support tickets.

triage_config.json: Dynamic configuration file dictating allowed categories, priorities, and routing rules.

normalizer.py: Handles deterministic ticket preparation.

ticket_predictor.py: Manages the LLM inference and structured data extraction.

human_review.py: Manages the CLI checkpoint and final output generation.

final_output.py: The validation script to ensure data integrity.

📊 Artifacts Generated
Running the pipeline will deterministically generate the following artifacts from a clean state:

normalized_tickets.json

triage_predictions.json

review_overrides.json (Logs any human interventions)

final_queue.json (The final state sent to the agent dashboard)

queue_summary.md (Analytics and routing breakdown)

escalations.json (Tickets requiring immediate manual attention)