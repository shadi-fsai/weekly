from litellm import completion
import json
from termcolor import colored
from pydantic import BaseModel
from typing import List

my_local_model = 'ollama/hf.co/shadicopty/llama3.2-entity'
my_local_api_base = "http://localhost:11434"

#my_local_model = "groq/Llama-3.3-70b-Versatile" 
#my_local_api_base = None 

class HighlightSchema(BaseModel):
    projects: List[str]
    companies: List[str]
    people: List[str]

class Declassifier:
    def __init__(self):
        self.original_to_fiction = {}
        self.fiction_to_original = {}

    def add_entity(self, original, fictional):
        print(f"Adding entity {original} with fictional name {fictional}")
        self.original_to_fiction[original] = fictional
        self.fiction_to_original[fictional] = original

    def extract_entity(self, text):
        response = completion(
            model=my_local_model, 
            messages=[
                {"role": "system", "content": "You are an entity extraction tool. respond in json format only."},
                {"role": "user", "content": "Extract the company, project and people names from the text. Here is the text: \n" + text + "}\n Only respond with valid JSON of a LIST of items."}
            ],
            response_format=HighlightSchema,
            api_base=my_local_api_base  # Ollama's default address
        )
        print (response['choices'][0]['message']['content'])
        return json.loads(response['choices'][0]['message']['content'])
        

    def create_fictional_name(self, original, entity_type) -> str:
        ''' this function takes in an entity and its original name and creates a fictional name for the entity'''
        old_fictional_names = str(self.original_to_fiction.values())
        response = completion(
            model=my_local_model, 
            messages=[
                {"role": "system", "content": "You are an entity name replacement tool."},
                {"role": "user", "content": "Come up with an alternative "+entity_type+" name to replace "+original+"; It should be somewhat hard to guess the original from the alternate name you come up with, but it should have similar attributes. You CANNOT use any of the following names: {"+ old_fictional_names+"}\n Return the new name and NOTHING else."}
            ],
            api_base=my_local_api_base  # Ollama's default address
        )
        return response['choices'][0]['message']['content']
        

    def declassify(self, text) -> str:
        ''' this function takes in a text and replaces all the sensitive information (company names, workstream names, people names)
        It creates fictional names for these entities and returns the text with the fictional names'''
        entities = self.extract_entity(text)
        companies = entities['companies']
        people = entities['people']
        projects = entities['projects']

        # Remove any person names that also exist in the companies list
        people = [person for person in people if person not in companies]

        for company in companies:
            if company in self.original_to_fiction:
                continue
            fictional_name = self.create_fictional_name(company, "company")
            self.add_entity(company, fictional_name)
            text = text.replace(company, fictional_name)

        for person in people:
            if person in self.original_to_fiction:
                continue
            fictional_name = self.create_fictional_name(person, "person")
            self.add_entity(person, fictional_name)
            text = text.replace(person, fictional_name)

        for project in projects:
            if project in self.original_to_fiction:
                continue
            fictional_name = self.create_fictional_name(project, "project")
            self.add_entity(project, fictional_name)
            text = text.replace(project, fictional_name)

        return text

    def reclassify(self, text) -> str:
        ''' this function takes in a text with fictional names created by declassify, and replaces the fictional names with the original names'''
        for fictional, original in self.fiction_to_original.items():
            text = text.replace(fictional, original)
        return text


def main():
    declassifier = Declassifier()
    text = "This week we had a great meeting with Apple and Facebook, we discussed the new project GenXneG. Steve did a great job presenting the new features to the team."
    print(colored("Declassifying original text:" + text + "\n", "green"))
    declassified_text = declassifier.declassify(text)
    print(colored(declassified_text, "green"))
    print ("\n\n Reclassifying: \n")
    reclassified_text = declassifier.reclassify(declassified_text)
    print(colored(reclassified_text, "green"))
    