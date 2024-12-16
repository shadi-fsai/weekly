from litellm import completion
import json

my_local_model = 'ollama/llama3.2'  #using the 3B model for this
my_local_api_base = "http://localhost:11434"

#this 
class Declassifier:
    def __init__(self):
        self.original_to_fiction = {}
        self.fiction_to_original = {}

    def add_entity(self, original, fictional):
        print(f"Adding entity {original} with fictional name {fictional}")
        self.original_to_fiction[original] = fictional
        self.fiction_to_original[fictional] = original

    def extract_entity(self, text, entity, existing_entities=None):
        response = completion(
            model=my_local_model, 
            messages=[
                {"role": "system", "content": "You are an entity extraction tool."},
                {"role": "user", "content": "return only a json list and nothing else, return a json list of "+entity+" names in the following text:" + text + "\n Json list and nothing else:"}
            ],
            api_base=my_local_api_base  # Ollama's default address
        )
        answer = json.loads(response['choices'][0]['message']['content'])
        if existing_entities:
            answer = [item for item in answer if item not in existing_entities]
        return answer

    def create_fictional_name(self, entity, original):
        ''' this function takes in an entity and its original name and creates a fictional name for the entity'''
        response = completion(
            model=my_local_model, 
            messages=[
                {"role": "system", "content": "You are an entity name replacement tool."},
                {"role": "user", "content": "Come up with a fictional "+entity+" name to replace "+original+". Return the new name and NOTHING else."}
            ],
            api_base=my_local_api_base  # Ollama's default address
        )
        return response['choices'][0]['message']['content']
        

    def declassify(self, text) -> str:
        ''' this function takes in a text and replaces all the sensitive information (company names, workstream names, people names)
        It creates fictional names for these entities and returns the text with the fictional names'''
        company_names = self.extract_entity(text, "company")
        workstream_names = self.extract_entity(text, "workstream")
        people_names = self.extract_entity(text, "person")

        for company in company_names:
            if company in self.original_to_fiction:
                continue
            fictional_name = self.create_fictional_name("company", company)
            self.add_entity(company, fictional_name)
            text = text.replace(company, fictional_name)

        for workstream in workstream_names:
            if workstream in self.original_to_fiction:
                continue
            fictional_name = self.create_fictional_name("workstream", workstream)
            self.add_entity(workstream, fictional_name)
            text = text.replace(workstream, fictional_name)
        
        for person in people_names:
            if person in self.original_to_fiction:
                continue
            fictional_name = self.create_fictional_name("person", person)
            self.add_entity(person, fictional_name)
            text = text.replace(person, fictional_name)

        return text

    def reclassify(self, text) -> str:
        ''' this function takes in a text with fictional names created by declassify, and replaces the fictional names with the original names'''
        for fictional, original in self.fiction_to_original.items():
            text = text.replace(fictional, original)
        return text


def main():
    declassifier = Declassifier()
    text = "This week we had a great meeting with Apple and Facebook, we discussed the new project with the workstream called Project X. We also hired a new person named John Doe"
    print ("Declassifying original text:" +text+ "\n")
    declassified_text = declassifier.declassify(text)
    print(declassified_text)
    print ("\n\n Reclassifying: \n")
    reclassified_text = declassifier.reclassify(declassified_text)
    print(reclassified_text)
    