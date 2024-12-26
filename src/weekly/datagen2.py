# Copyright 2023-present, Argilla, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from enum import Enum
from pathlib import Path

from distilabel.llms import LiteLLM
from distilabel.pipeline import Pipeline
from distilabel.steps import LoadDataFromDicts
from distilabel.steps.tasks import TextGeneration
from pydantic import BaseModel, StringConstraints, conint
from typing_extensions import Annotated
from distilabel.pipeline import Pipeline
from distilabel.steps import LoadDataFromHub
from distilabel.steps.tasks import TextGeneration


llm = LiteLLM(model="groq/Llama-3.3-70b-Versatile")

llm = LiteLLM(model="gpt-4o-mini")

def main():
    with Pipeline(  # 
        name="simple-text-generation-pipeline",
        description="A simple text generation pipeline",
        ) as pipeline:  # 
            load_dataset = LoadDataFromHub(  # 
                name="load_dataset",
                output_mappings={"prompt": "instruction"},
            )

            text_generation = TextGeneration(  # 
                name="text_generation",
                llm=llm,  # 
            )

            load_dataset >> text_generation  # 

    distiset = pipeline.run(  # 
        parameters={
            load_dataset.name: {
                "repo_id": "distilabel-internal-testing/instruction-dataset-mini",
                "split": "test",
            },
            text_generation.name: {
                "llm": {
                    "generation_kwargs": {
                        "temperature": 0.7,
                        "max_new_tokens": 512,
                    }
                }
            },
        },
    )
    distiset.push_to_hub(repo_id="distilabel-example")
 