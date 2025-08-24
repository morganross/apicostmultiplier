todo: import fpf to do one-shots. upgrade fpf to use search


this codebase, and or python in general suffers from an extremem problem that has halted development on most functions. There is a major unsolved issue with this code. Extreme long term work must be done to improve its path handling. A new, totally seperate, robust program, python or otherwise, likey a binary or whatever is most robustly compatabile, folder containtng new software project that ensures all paths are setup correctly in the code before any and every script is run. its a new program to veryify the quality of the code, and the quality of the inputs in the config files. massive comprehensive reports will be generated describing the way path handling is done by each and every step of code in each and every script. the final result must be robust enough to run on as many systems as possible.

This issue has dogged the progrct and prevented its further productive development. We program as far as we can, then when this probelm becomes unworkaroundable, we start over from scratch, getting further each time, untill we run into the same problem. Development on all projects is halted untill i develop new better software or interpertive language that understands windows filesystem syntax.

Restarting development and re learning relitive paths in python have not resulted in progress, therefore all work is shifted towords a new software project, existing in a folder alongside this projects other sopftwares.

One perfect example just occured. a first time user put relitive paths in a config file and broke the whole software. our new **MANHATTENPROJECT** will make that scenario literyally deterministicly impossible. before any other programatic functions occur. we will evem add a ai multi agent vailiadtor even after our programatic vailidator.


# Import Style Guide

This project primarily utilizes **absolute imports** for Python modules and packages. This approach ensures clarity, avoids ambiguity, and promotes a more robust and maintainable codebase by explicitly stating the full path from the project's root or a recognized package. Relative imports are generally avoided unless strictly necessary for specific internal package structures.

---

# gptr-eval-process


the root/main script starts the process markdown script, and gets the files from process markdown

the main script then sends those files to eval

the main scirpt then writes that file to the correct location

the input folder and output folder are specifyed by a config file

THE PROCESS-MARKDOWN script is repsonsible for getting the query together, sending it to gpt-R and obtaining its results

the process markdown FOLDER contains the process markdown script and a config file AND a seperate file that contains the logic for creating output files and dir, becuase we use it from differnt places.

This project serves as a central orchestrator for integrating and managing workflows involving:
- `gpt-researcher`: For generating research reports.
- `llm-doc-eval`: For evaluating documents.
- `process_markdown`: A new module for markdown processing utilities.
- `review-revise`: A module for future review and revision functionalities.

All project dependencies are managed in the central `requirements.txt` file located in this root directory.

## Configuration Files

Key configuration files within this project include:

*   [`gptr-eval-process/llm-doc-eval/config.yaml`](gptr-eval-process/llm-doc-eval/config.yaml)
*   [`gptr-eval-process/llm-doc-eval/criteria.yaml`](gptr-eval-process/llm-doc-eval/criteria.yaml)
*   [`gptr-eval-process/gpt-researcher/.env.example`](gptr-eval-process/gpt-researcher/.env.example)
*   [`gptr-eval-process/gpt-researcher/gpt_researcher/config/variables/default.py`](gptr-eval-process/gpt-researcher/gpt_researcher/config/variables/default.py)
*   [`gptr-eval-process/process_markdown/config.md`](gptr-eval-process/process_markdown/config.md)

also the multi agent config in task.json

## Documentation

For more detailed information, please refer to the following documentation files:

*   [`gptr-eval-process/README.md`](gptr-eval-process/README.md) (Main project README)(this file)
*   [`gptr-eval-process/process-markdown/Readme-process-markdown.md`](gptr-eval-process/process-markdown/Readme-process-markdown.md) (Main project README)(this file)
*   [`gptr-eval-process/gpt-researcher/README.md`](gptr-eval-process/gpt-researcher/README.md) (GPT-Researcher project README)
*   [`gptr-eval-process/llm-doc-eval/README.md`](gptr-eval-process/llm-doc-eval/README.md) (LLM-Doc-Eval project README)



*   [`gptr-eval-process/gpt-researcher/backend/report_type/deep_research/README.md`](gptr-eval-process/gpt-researcher/backend/report_type/deep_research/README.md)
*   [`gptr-eval-process/gpt-researcher/backend/report_type/detailed_report/README.md`](gptr-eval-process/gpt-researcher/backend/report_type/detailed_report/README.md)



*   [`gptr-eval-process/gpt-researcher/docs/docs/welcome.md`](gptr-eval-process/gpt-researcher/docs/docs/welcome.md)


*   [`gptr-eval-process/gpt-researcher/docs/docs/contribute.md`](gptr-eval-process/gpt-researcher/docs/docs/contribute.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/examples/detailed_report.md`](gptr-eval-process/gpt-researcher/docs/docs/examples/detailed_report.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/examples/examples.md`](gptr-eval-process/gpt-researcher/docs/docs/examples/examples.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/examples/hybrid_research.md`](gptr-eval-process/gpt-researcher/docs/docs/examples/hybrid_research.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/faq.md`](gptr-eval-process/gpt-researcher/docs/docs/faq.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/context/azure-storage.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/context/azure-storage.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/context/data-ingestion.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/context/data-ingestion.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/context/filtering-by-domain.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/context/filtering-by-domain.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/context/local-docs.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/context/local-docs.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/context/tailored-research.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/context/tailored-research.md)
gpt-researcher/frontend/discord-bot.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/querying-the-backend.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/querying-the-backend.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/getting-started/cli.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/getting-started/cli.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/getting-started/getting-started.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/getting-started/getting-started.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/getting-started/how-to-choose.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/getting-started/how-to-choose.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/getting-started/introduction.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/getting-started/introduction.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/getting-started/linux-deployment.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/getting-started/linux-deployment.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/automated-tests.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/automated-tests.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/config.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/config.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/deep_research.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/deep_research.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/example.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/example.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/npm-package.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/npm-package.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/pip-package.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/pip-package.md)

*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/scraping.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/scraping.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/troubleshooting.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/gptr/troubleshooting.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/handling-logs/all-about-logs.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/handling-logs/all-about-logs.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/handling-logs/langsmith-logs.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/handling-logs/langsmith-logs.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/handling-logs/simple-logs-example.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/handling-logs/simple-logs-example.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/llms/llms.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/llms/llms.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/llms/running-with-azure.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/llms/running-with-azure.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/llms/running-with-ollama.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/llms/running-with-ollama.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/llms/supported-llms.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/llms/supported-llms.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/llms/testing-your-llm.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/llms/testing-your-llm.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/multi_agents/langgraph.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/multi_agents/langgraph.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/search-engines/retrievers.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/search-engines/retrievers.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/search-engines/test-your-retriever.md`](gptr-eval-process/gpt-researcher/docs/docs/gpt-researcher/search-engines/test-your-retriever.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/reference/config/config.md`](gptr-eval-process/gpt-researcher/docs/docs/reference/config/config.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/reference/config/singleton.md`](gptr-eval-process/gpt-researcher/docs/docs/reference/config/singleton.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/reference/processing/html.md`](gptr-eval-process/gpt-researcher/docs/docs/reference/processing/html.md)
*   [`gptr-eval-process/gpt-researcher/docs/docs/reference/processing/text.md`](gptr-eval-process/gpt-researcher/docs/docs/reference/processing/text.md)

## Troubleshooting and Solutions

### Resolved: `RuntimeWarning: coroutine '...' was never awaited` in `llm-doc-eval` CLI

**Problem:**
When running `llm-doc-eval` CLI commands, particularly `run-all-evaluations`, a `RuntimeWarning: coroutine '...' was never awaited` and a `RuntimeError: asyncio.run() cannot be called from a running event loop` were encountered. This was due to the `@sync_command` decorator (which internally calls `asyncio.run()`) being applied to both the top-level command (`run_all_evaluations`) and its internally called sub-commands (`run_single`, `run_pairwise`). This led to an invalid attempt to create nested `asyncio` event loops.

**Solution:**
The fix involved modifying `gptr-eval-process/llm-doc-eval/cli.py`. The `@sync_command` decorator was removed from the `run_single` and `run_pairwise` function definitions. The `@sync_command` decorator was retained only on the top-level `run_all_evaluations` command. This ensures that `asyncio.run()` is called only once at the entry point of the CLI command, allowing internal `async` function calls to proceed within the same event loop without conflict.

**Verification:**
The fix was verified by successfully executing `python cli.py run-all-evaluations ../test/finaldocs` from the `gptr-eval-process/llm-doc-eval` directory. The command completed without any `RuntimeWarning` or `RuntimeError`, confirming the resolution of the asynchronous execution issue.
