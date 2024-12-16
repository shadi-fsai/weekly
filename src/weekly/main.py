from litellm import completion
import csv
import yaml
from termcolor import colored
from .declassifier import Declassifier

my_model = "groq/Llama-3.3-70b-Versatile" 
my_api_base = None 

#my_model ='ollama/llama3.3:70b-instruct-q2_K'
#my_api_base = "http://localhost:11434"

        
class WeeklyReporter:
    def __init__(self, org_context, highlight_examples, workstream_importance):
        self.org_context = org_context
        self.highlight_examples = highlight_examples
        self.workstream_importance = workstream_importance

    def write_highlight(self, outcome):
        response = completion(
            model=my_model, 
            messages=[
                {"role": "system", "content": "You are a senior leader in a large organization, you are writing a weekly progress report that will be distributed to your team, your manager, and your cross functional partners."},
                {"role": "system", "content": "Here is some context about your organization {" + self.org_context + "}"},
                {"role": "system", "content": "The following are examples of what highlights look like: {" + self.highlight_examples + "}"},
                {"role": "system", "content": "The following are the existing workstreams and their importance: {" + self.workstream_importance + "}"},            

                {"role": "user", "content": "Write a highlight for the following outcome, remain strictly compliant with the style used in examples: " + outcome}
            ],
            api_base=my_api_base  # Ollama's default address
        )
        return response['choices'][0]['message']['content']



def main():

    declassifier = Declassifier()

    with open('config.yaml', 'r') as file:
        declassified = declassifier.declassify(file.read())
        config = yaml.safe_load(declassified)

    reporter = WeeklyReporter(config['org_context'], 
                            config['highlight_examples'],
                            config['workstream_importance'])

    outcomes = []
    with open('this_weeks_outcomes.csv', 'r') as file:
        declassifiedoutcomes = declassifier.declassify(file.read())
        reader = csv.reader(declassifiedoutcomes.splitlines())
        for row in reader:
            outcomes.append(row[0])

    with open('highlights.txt', 'w') as file:
        for outcome in outcomes:
            highlight = reporter.write_highlight(outcome)
            reclassified_highlight = declassifier.reclassify(highlight)
            print(colored(reclassified_highlight, "green"))
            file.write(reclassified_highlight + '\n')