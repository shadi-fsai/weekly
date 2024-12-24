from opik import Opik
from opik.evaluation import evaluate
import csv
from opik.evaluation.metrics import (Hallucination, Moderation, IsJson)
from opik.evaluation.metrics import GEval

from pydantic import BaseModel
from typing import List
from litellm import completion

import dotenv
dotenv.load_dotenv()

opik_client = Opik()

metricGEval = GEval(
    task_introduction="You are an expert judge tasked with evaluating the faithfulness of an AI-generated answer to the given context.",
    evaluation_criteria="In the provided text, the OUTPUT must include all the named entities from INPUT in the right categories; it must be JSON formatted",
)

my_model = "ollama/hf.co/shadicopty/llama3.2-entity"

class HighlightSchema(BaseModel):
    projects: List[str]
    companies: List[str]
    people: List[str]

def extract_entities(highlight):
    prompt = f"Identify the project names, company names, and people names in the following highlight: '{highlight}'"
    
    response = completion(
        model=my_model,
        messages=[
            {"role": "system", "content": "You are a data extraction tool. Return answers in JSON only."},
            {"role": "user", "content": prompt}
        ],
        response_format=HighlightSchema,
        temperature=0
    )
    identified_entities = response['choices'][0]['message']['content']
    return identified_entities    


def setup(client):
    # Create a dataset
    dataset = client.get_or_create_dataset(name="My dataset2")
    # Load the CSV file
    with open('generated_highlight_samples-test.csv', mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            highlight = list(row.values())[0]
            highlight_data = list(row.values())[1:]
            print(f"Highlight: {highlight}, Highlight Data: {highlight_data}")
            # Create a dataset item
            dataset.insert([{"highlight": highlight, "highlight_data": highlight_data}])
    return dataset

def evaluation_task(dataset_item):
    # your LLM application is called here
    input = dataset_item["highlight"]
    precontext = "You are a data extraction tool. Return answers in JSON format only."
    with opik_client.start("generate_text"):
        answer = extract_entities(input)
    result = {
        "input": input,
        "output": answer,
        "context": [precontext],
        "reference": ""
    }
    return result

def main():
    dataset = setup(opik_client)

    metrics = [Hallucination(), metricGEval, IsJson()]
    global my_model
    for llm in ["ollama/hf.co/shadicopty/llama3.2-entity",
                "ollama/hf.co/shadicopty/llama3.2-entity-1b",
                "ollama/granite3.1-dense:8b",
                "ollama/granite3.1-moe:3b",
                "ollama/granite3.1-dense:2b",
                "ollama/phi3.5:latest",
                "ollama/qwen2.5:3b-instruct",
                "ollama/llama3.2:3b-instruct-fp16",
                "ollama/llama3.1:8b-instruct-q3_K_M",
                "ollama/llama3.2"]:
        my_model = llm
        eval_results = evaluate(
            experiment_name="my_evaluation:" + llm,
            dataset=dataset,
            task=evaluation_task,
            scoring_metrics=metrics
        )
        print(eval_results)

