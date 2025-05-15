# llm-router-interface
Trying to build a natural language interface for network devices.

This repository is treated as a personal note to myself for the project.

Most of the files are iteration of same things. Start working from last one, middleware10.py.

pdf_utils.py and clean.py were used to make and clean the text files from pdf, for giving context to LLMs.


Steps:

1. Have some router reachable via ssh from your local computer, virtual or physical. I used Containerlab and SRLinux.
2. Download and run Ollama + any LM you can run. I used Deepseek r1:7b. You can use docker. Check if LM load goes to the GPU.
3. If you have access to something cloud hosted, you can use that. I used Gemini 2 free tier. You can use either step 2 or 3, dont need both.
4. Update the middleware file. For simplicity, most credentials and api keys are hard coded. Dont do as I did.
5. Get your context ready. For exmaple, I downloaded/copied Nokia SRLinux commands, manual, guides etc. Then I used pdf_utils.py and clean.py to creat text file that can be given in prompt. You can also use Chatgpt, Copilot, etc, to help you generate this file. This file has various commands and their explanations and examples. Files I used are in documents directory.
6. Running middleware will start a server, you will request in below format.
   curl -X POST http://localhost:5000/query -H "Content-Type: application/json" -d '{
  "router": "node2",
  "question": "What are the bgp neighbours in node2 router?"
}'
8. That is it!
