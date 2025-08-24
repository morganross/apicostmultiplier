# apicostmultiplier

ACM is a GUI and a installer for 'process_markdown'. Process_markdown uses GPT-R and llm_doc_eval, whcih ACM also installs. The GUI is helpful for editing config files from seperate repos in one place.



apicostmultiplier programmatically combines Doc2saurus, FilePromptForge, GPT-Researcher, and LLM_doc_eval, and a GUI to produce written reports from a list. 

apicostmultiplier aims to improve output from any LLM by subdiving tasks to overcome context window limitations, and by including iteration, evaluation and revison.

apicostmultipler maximizes LLM api cost effecintcy by using a post evaluation cost efectivness calculator. It can run a massive number of LLM api calls to evaluate LLM output, as indicated by the name apicostmultiplier.

apicostmultiplier can produce a massive number of documents from a single list, and use a massive number of LLM api calls to generate a single document.



On install, this software will download other software codebases from github into folders. apicostmultiplier is a process flow orchestrator for using the downloaded software. It can be used to interact with one or more of the downloaded softwares, and can use the output from one as the input for another.  can be used from the command line, in a python script, or from the apicostmultiplier GUI.

The gui allows for configuring bredth, depth, quality, and quantity, with cost estimation.


apicostmultiplier can further be combined with *newsintake, saruos2diseminate, and WebformFoundry to automaticly communicate topical documents. Which allows for sending a high number of high quality documents to a high number of endpoints while minimizing cost, all from a single list.


### process_markdown
runs a list of promopts through GPT-R (a local multi agent deep researcher) and trough deep reseach model one shots. It repeats this process x number of times per model and for x number of models. LLM_doc_eval then compares each repsonse aginst everyother response x number of times to get ELO score.
