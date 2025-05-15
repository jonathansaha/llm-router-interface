# llm-router-interface
Trying to build a natural language interface for network devices.

This repository is treated as a personal note to myself for the project.

Most of the files are iteration of same things. Start working from last one, middleware10.py.

pdf_utils.py and clean.py were used to make and cleaning the text files from pdf, for giving context to LLMs.


Steps:

1. Have some router reachable via ssh from your local computer, virtual or physical. I used Containerlab and SRLinux.
2. Download and run Ollama + any LM you can run. I used Deepseek r1:7b. You can use docker. Check if LM load goes to the GPU.
3. If you have access to something cloud hosted, you can use that. I used Gemini 2 free tier. You can use either step 2 or 3, dont need both.
4. Update the middleware file. For simplicity, most credentials and api keys are hard coded. Dont do as I did.
5. 
