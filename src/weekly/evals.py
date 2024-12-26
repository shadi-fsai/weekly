import json
import pydantic
from opik import Opik
from opik.evaluation import evaluate
import csv
from opik.evaluation.metrics import (LevenshteinRatio, IsJson)
from opik.evaluation.metrics import base_metric, score_result

from typing import Any

from pydantic import BaseModel
from typing import List
from litellm import completion

import dotenv

my_eval_model = "groq/Llama-3.3-70b-Versatile"


class LLMJudgeScoreFormat(pydantic.BaseModel):
    score: int
    reason: str

class LLMJudgeMetric(base_metric.BaseMetric):
    def __init__(self, name: str = "Accurate Response"):
        self.name = name
        self.prompt_template = """
        TASK:
        You are an expert judge tasked with evaluating the precision of a given AI response.
        In the provided text, the OUTPUT must include all the named entities from REFERENCE in the right categories. OUTPUT should no include names that are not from REFERENCE. 
        It must be JSON formatted and consistenly formatted. Penalize significantly for missing entities, wrong entities, wrong categories, and wrong formatting. For the formatting it should precisely comply  with 'projects': [], 'companies': [], 'people': []. even if the list is empty or has a single value, it should be present. 
        If all of the above are correct, give a score of 1. If there are minor issues, give a score of 0.75. 
        If the answer is not JSON, give a score of 0.
        If the answer is JSON but does not have the right format, give a score of 0.25.
        If the answer is JSON, in the right format, but is missing some entities give it 0.5
    
        Your answer should include a score and a reason for the score.

        OUTPUT: {output}
        REFERENCE: {reference}
        """

    def score(self, output: str, reference:str, **ignored_kwargs: Any):
        print (f"SCORING Output: {output}, Reference: {reference}")
        """
        Score the output a of an LLM.

        Args:
            output: The output of an LLM to score.
            reference: Text that the output should be compared against.
            **ignored_kwargs: Any additional keyword arguments. This is important so that the metric can be used in the `evaluate` function.
        """
        # Construct the prompt based on the output of the LLM
        prompt = self.prompt_template.format(output=output, reference=reference)

        # Generate and parse the response from the LLM
        response = completion(
            model=my_eval_model, 
            messages=[{"role": "user", "content": prompt}],
            response_format=LLMJudgeScoreFormat,
        )

        final_score = float(json.loads(response.choices[0].message.content)["score"])
        reason = json.loads(response.choices[0].message.content)["reason"]
            # Return the score and the reason
        return score_result.ScoreResult(
            name=self.name, value=final_score, reason=reason
        )
 
dotenv.load_dotenv()

opik_client = Opik()
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
    answer = extract_entities(input)
    result = {
        "input": input,
        "output": answer,
        "context": [precontext],
        "reference": str(dataset_item["highlight_data"][0])
    }
    return result

def main():
    dataset = setup(opik_client)

    metrics = [LLMJudgeMetric(), IsJson(), LevenshteinRatio()]
    global my_model
    for llm in [
                "ollama/hf.co/shadicopty/llama3.2-entity",
                "ollama/hf.co/shadicopty/llama3.2-entity-1b",
                "ollama/granite3.1-moe:3b",
                "ollama/granite3.1-dense:2b",
                "ollama/qwen2.5:3b-instruct",
                "ollama/llama3.2:3b-instruct-fp16",
                "ollama/llama3.2"]:
        my_model = llm
        eval_results = evaluate(
            experiment_name="my_evaluation:" + llm,
            dataset=dataset,
            task=evaluation_task,
            scoring_metrics=metrics
        )
        print(eval_results)

