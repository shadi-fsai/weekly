# Weekly

This tool creates weekly progress report highlights for organizational distribution.
It can be used with ollama locally or groq using API, to use with groq you need to obtain a groq-key

## Ollama

Download Ollama from https://ollama.com/download
Prior to running run 'ollama pull llama3.3:70b-instruct-q2_K' in your command line.
This will require your machine to have at least 24GB of ram.

If you don't have that RAM, you can use llama3.2 for smaller footprint models.

## Groq

Get your API keys from Groq.com
Copy .env-example to .env and update with your keys.

## Running the weekly report


Use 'poetry lock' then 'poetry install' to get an environment installed 

Edit highlight-examples.txt to provide examples of what properly formatted highlights look like.
Edit orgcontext.txt to explain your organizational context, this improves the quality of the output highlights
Edit workstream-importance.txt to give context on specific workstreams your org is running, this allows the tool to produce better explanaitaions of impact.

Edit this_weeks_outcomes.csv, use an outcome per row

Run 'poetry run weekly' to get the output in file 'highlights.txt'