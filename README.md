# llm-router-interface
Trying to build a natural language interface for network devices.

This repository is treated as a personal note to myself for the project.

Most of the files are iteration of same things. Start working from last one, middleware_current.py. Older iterations have been moved to old_tryout directory.

pdf_utils2.py and clean.py were used to make and clean the text files from pdf, for giving context to LLMs.


Steps:

1. Have some router reachable via ssh from your local computer, virtual or physical. I used Containerlab and SRLinux.
2. Download and run Ollama + any LM you can run. I used Deepseek r1:7b. You can use docker. Check if LM load goes to the GPU.
3. If you have access to something cloud hosted, you can use that. I used Gemini 2 free tier. You can use either step 2 or 3, dont need both.
4. Update devices.list and api.key files as per your environment.
5. Get your context ready. For exmaple, I downloaded/copied Nokia SRLinux commands, manual, guides etc. Then I used pdf_utils.py and clean.py to creat text file that can be given in prompt. You can also use Chatgpt, Copilot, etc, to help you generate this file. This file has various commands and their explanations and examples. Files I used are in documents directory.
6. Running middleware will start a server, you will request in this format. >> 

   curl -X POST http://localhost:5000/query -H "Content-Type: application/json" -d '{
  "router": "node2",
  "question": "What are the bgp neighbours in node2 router?"
}'

7. Asking questions and reading through responses in CLI can get messy if the output gets large. To make it look better, there is index.html. Open it while the middleware is running. It pulls the devices list from the file devices.list and puts it in the dropdown menu. 
8. That is it!


Workflow:

1. User asks a question.
2. The Middleware sends it to an LLM.
3. LLM returns an appropriate command to
middleware.
4. Middleware sends that command to
router.
5. Router gives feedback.
6. User gets the feedback.

![Untitled-2025-05-15-0619](https://github.com/user-attachments/assets/6246b040-740c-46fd-bc2b-ec83a38f1179)

Screenshots:

![image](https://github.com/user-attachments/assets/1f939079-a069-4733-b5e4-3061d24dba74)
Output using index.html.

![image](https://github.com/user-attachments/assets/c622e288-ef94-483e-a02a-edbc945823d9)
Output from middleware during a request.

![image](https://github.com/user-attachments/assets/01e4c051-ae32-4bc2-8e65-fbf8c2a7ccd6)
Output in CLI.


