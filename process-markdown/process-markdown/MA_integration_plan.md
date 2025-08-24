# Project Plan — Integrate Multi-Agent (MA) into process-markdown (copy-first approach)

Objective
- Create a safe working copy of the process-markdown pipeline that calls the GPT-Researcher Multi-Agent (MA) flow once for a single input file.
- Keep original code unchanged. Work iteratively from the copy; verify the single-MA-run end-to-end, then expand/iterate.

Deliverable
- A new directory: `process-markdown-ma/` (copy of current `process-markdown/`) with a small integration that:
  - Writes a per-run `task.json` into a temp MA copy,
  - Calls MA to produce one report for the given markdown input,
  - Saves the MA-generated report to `temp_gpt_researcher_reports/` and returns its path so the rest of the pipeline can evaluate it (or copy to output).

High-level approach (why copy)
- Isolate changes from main pipeline.
- Allow concurrent runs later by using temp copies.
- Keep integration minimal: produce one MA report per input file; retain existing GPTResearcher code path for fallback.

Checklist (project tasks)
- [ ] Create new working copy directory `process-markdown-ma/` by copying `process-markdown/`.
- [ ] Add a module `ma_runner.py` implementing the temp-copy + run_research_task approach.
- [ ] Add a config template `ma_task_templates/default_task.json` to hold base MA task values.
- [ ] Modify the copied orchestrator (`process_markdown.py` in the copy) to:
  - Accept `use_multi_agent` mode (default true for the copy),
  - For each input markdown (respecting one_file_only), call `ma_runner.run_ma_for_query(query, overrides)` instead of `gpt_researcher_client.run_concurrent_research(...)`.
- [ ] Implement `ma_runner.run_ma_for_query(query, task_overrides)`:
  - Create a temp directory.
  - Copy `gpt-researcher-3.2.9/multi_agents/` into that temp directory.
  - Write a `task.json` in the temp multi_agents with merge(template + task_overrides + query).
  - Add the temp dir to sys.path and import `multi_agents.main.run_research_task`.
  - Await the coroutine and capture the returned report (string).
  - Save report to `temp_gpt_researcher_reports/ma_report_<uuid>.md` and return its path.
  - Cleanup temp dir and remove sys.path entry.
- [ ] Add minimal logging and error handling; ensure exceptions are caught and readable.
- [ ] Add an example `ma_task_templates/default_task.json` (copy existing multi_agents/task.json), include placeholders for model/language/sections.
- [ ] Add a short README in `process-markdown-ma/` explaining usage and environment requirements (API keys, env vars).
- [ ] Manual test: create a single markdown input and run the copied pipeline; confirm MA produced a report file in `temp_gpt_researcher_reports/`.
- [ ] If test passes, iterate: add configuration flags, concurrency-safe behavior, and optional fallback to original GPTResearcher path.

Detailed implementation notes
- Temp-copy location:
  - Use Python's tempfile.mkdtemp(prefix="gptr_ma_run_") to create isolated dirs.
  - Copy tree with shutil.copytree(src_multi_agents, dst_multi_agents).
- Import mechanics:
  - Insert dst_multi_agents parent directory into sys.path so `import multi_agents.main` resolves to the temp copy.
  - Use asyncio.run or await the coroutine (our pipeline is async, so prefer awaiting from an async context).
- task.json merging:
  - Load template JSON, update fields with task_overrides provided by process_markdown (report formatting, model, language).
  - Always override the `query` field with the current markdown's query prompt or title.
- Environment:
  - Ensure the process inherits .env / environment variables for API keys (OPENAI_API_KEY, GOOGLE_API_KEY).
  - For MA-specific overrides (DEEP_RESEARCH_* or REASONING_EFFORT), either set them as environment variables before calling run_research_task (in the process) or include them in the task.json if recognized by MA.
- Output:
  - MA returns a report string (multi_agents.main.run_research_task returns research_report). Save to file and hand back path to the caller.

Files to create/edit (in the copy)
- process-markdown-ma/ (full copy of process-markdown/)
  - ma_runner.py (new)
  - ma_task_templates/default_task.json (new)
  - process_markdown.py (modified to call MA runner)
  - README.md (new) — quick usage and env var notes

Testing plan
1. Setup:
   - Create venv, install repository requirements.
   - Add API keys to gpt-researcher-3.2.9/.env or root .env.
2. Run:
   - Place one small markdown in input folder configured in config.yaml.
   - Run `python process-markdown-ma/process_markdown.py` (in the copy) — it should call MA and produce a report file.
3. Verify:
   - Check `temp_gpt_researcher_reports/ma_report_*.md` exists and contains content.
   - Inspect logs for errors.

Risks & mitigations
- Risk: MA depends on extra packages (langgraph, langchain etc). Mitigation: state requirements in README and install `multi_agents/requirements.txt`.
- Risk: API keys missing or rate-limited. Mitigation: fail gracefully and print actionable error.
- Risk: LangChain client API changes may reject extra kwargs. Mitigation: use `extra_body` fallback or recommend dependency versions.

Estimated effort
- Prototype implementation: ~1–2 hours (create copy, add ma_runner, wiring).
- Testing & debugging (with API keys): additional 1–2 hours.

Next action (I will perform if you confirm)
- Create the `process-markdown-ma/` copy and implement `ma_runner.py` + template + modify process_markdown.py in the copy to call MA once per input file.
- Run static checks (no network calls). Then you can run the copied pipeline locally with API keys to produce an MA report.

Confirm and I will start implementing Option 1 (temp-copy concurrent-safe MA integration) now.
</response>
</plan_mode_respond>
