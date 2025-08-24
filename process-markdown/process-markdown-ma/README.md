Process-markdown-ma — Instructions to run the Multi-Agent (MA) prototype
======================================================================

This folder is a safe copy of the original process-markdown pipeline. It calls the GPT-Researcher Multi-Agent (MA) flow once per input markdown and saves the MA-produced report to the temp reports directory.

Prerequisites
- Python 3.11+ (match repo expectations)
- A virtual environment (recommended)
- Required API keys (put them in repo .env files or in your shell env):
  - OPENAI_API_KEY (if using OpenAI models)
  - GOOGLE_API_KEY (if using Gemini grounding)
  - OPENROUTER_API_KEY (if routing through OpenRouter)
- Install Python dependencies (recommended in venv):
  - pip install -r requirements.txt
  - Also install multi_agents extras if needed:
    - pip install -r gptr-eval-process/gpt-researcher-3.2.9/multi_agents/requirements.txt
  - If you will use Google grounding, install google-genai and dependencies per its docs.

Files of interest
- process_markdown.py — orchestrator that reads process-markdown config and calls the MA runner.
- ma_runner.py — creates a temp copy of gpt-researcher multi_agents, writes a per-run task.json, imports and calls multi_agents.main.run_research_task, saves report to temp_gpt_researcher_reports/.
- ma_task_templates/default_task.json — (optional) template to control default task fields. If not present, ma_runner uses the original multi_agents/task.json as template.
- temp_gpt_researcher_reports/ — output folder where MA reports are saved.

Quick setup (one-time)
1. Create & activate virtualenv:
   - python -m venv .venv
   - .venv\Scripts\activate   (Windows) or source .venv/bin/activate (macOS/Linux)

2. Install repo requirements:
   - pip install -r requirements.txt
   - pip install -r gptr-eval-process/gpt-researcher-3.2.9/requirements.txt
   - pip install -r gptr-eval-process/gpt-researcher-3.2.9/multi_agents/requirements.txt

3. Ensure API keys are available:
   - Copy gptr-eval-process/gpt-researcher-3.2.9/.env.example -> gptr-eval-process/gpt-researcher-3.2.9/.env and fill keys
   - Or export keys in shell:
     - set OPENAI_API_KEY=...
     - set GOOGLE_API_KEY=...
     - set OPENROUTER_API_KEY=...

Prepare a minimal test input
1. Create an input folder, e.g. c:/dev/postop/test_input
2. Create a sample markdown file:
   - test_input/example.md
     ```
     # Example Query
     What are the main trends in AI last year?
     ```
3. Create an instructions file (use the repo test instructions as example):
   - gptr-eval-process/test/instructions.txt
   - Ensure process-markdown/config.yaml points input_folder to your test_input and instructions_file to the instructions path.

Configure process-markdown config (it uses the original config file)
- Edit: gptr-eval-process/process-markdown/config.yaml
  - Set input_folder: path to your test_input
  - Set output_folder: path for final reports
  - Set instructions_file: path to instructions.txt
  - Optionally set one_file_only: true for quick runs

Run the MA prototype
- From repo root (c:/dev/postop):
  - cd gptr-eval-process/process-markdown-ma
  - python process_markdown.py
- The script will:
  - Read the original config yaml,
  - For each markdown, build a query prompt and call ma_runner.run_ma_for_query(...),
  - Save the MA generated report to temp_gpt_researcher_reports and copy it to the configured output location.

Troubleshooting & logs
- If MA fails to import/run:
  - Ensure multi_agents dependencies (langgraph etc.) are installed in your venv.
  - Check stdout/stderr for the exception — ma_runner prints import/run errors.
- If the MA run hangs:
  - Check network connectivity and API key validity.
  - MA may run long (minutes) depending on model & multi-agent configuration.
- If LangChain/clients error on unknown kwargs, update LangChain / provider SDK versions or remove unsupported kwargs.

Advanced notes
- Per-run task customization:
  - You can add process-markdown-ma/ma_task_templates/default_task.json (copy of gpt-researcher-3.2.9/multi_agents/task.json) and edit defaults. ma_runner will prefer this template if present.
  - You can pass task_overrides from process_markdown.py into run_ma_for_query to change model, language, or sections for that run.
- Concurrency:
  - The temp-copy approach isolates each run so concurrent runs won’t clobber the same task.json.
- Integrating with evaluation:
  - The current prototype simply copies the MA report to the output location. You can then run llm-doc-eval on that output as normal (or extend the script to call llm_doc_eval_client.evaluate_reports).

If you want, next I will:
- Add a sample `ma_task_templates/default_task.json` into this copy (based on the repository multi_agents/task.json).
- Add a simple test script that creates the test_input markdown and runs the prototype automatically.

Tell me which of those you'd like next.
