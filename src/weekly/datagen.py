from datetime import time
from time import sleep
from litellm import completion
from litellm import RateLimitError
import csv
from termcolor import colored
import json
import random
from pydantic import BaseModel
from typing import List
import boto3

my_model = "groq/Llama-3.3-70b-Versatile"
my_api_base = None 

company_names = [
    "Apple", "Microsoft", "Amazon", "Google", "Facebook",
    "Tesla", "Berkshire Hathaway", "Johnson & Johnson", "JPMorgan Chase",
    "Visa", "Procter & Gamble", "NVIDIA", "Walmart", "Mastercard",
    "UnitedHealth Group", "Home Depot", "Samsung",
    "Nestlé", "Roche", "Toyota", "Pfizer", "Coca-Cola",
    "PepsiCo", "Intel", "Cisco", "Verizon",
    "AT&T", "Chevron", "ExxonMobil", "Disney",
    "Comcast", "Nike", "McDonald's", "Abbott",
    "Merck", "Adobe", "Salesforce", "Netflix", "PayPal",
    "Qualcomm", "Broadcom", "Oracle", "IBM",
    "Honeywell", "Medtronic", "Bristol-Myers Squibb", "Amgen",
    "Eli Lilly", "General Electric", "Lockheed Martin",
    "Raytheon", "Goldman Sachs", "Morgan Stanley",
    "Citigroup", "Bank of America", "Wells Fargo", "American Express",
    "Boeing", "3M", "General Motors", "Ford",
    "Uber", "Lyft", "Airbnb", "Spotify",
    "Zoom", "Square", "Twitter", "Snap",
    "Pinterest", "Shopify", "eBay", "Alibaba",
    "Baidu", "Tencent", "JD.com", "Xiaomi",
    "Huawei", "Sony", "Panasonic",
    "LG", "Philips", "Siemens", "SAP", "Deutsche Bank",
    "HSBC", "Barclays", "Royal Bank of Canada", "TD Bank",
    "UBS", "Credit Suisse", "ING", "BNP Paribas",
    "Société Générale", "Allianz", "AXA", "Zurich Insurance",
    "Munich Re", "Prudential", "MetLife", "Aflac"
]

people_names = [
    "John", "Jane Doe", "Michael", "Emily Davis", "David",
    "Sarah Lee", "James", "Jessica Wilson", "Daniel", "Laura Hernandez",
    "Robert", "Linda Lewis", "Thomas", "Karen Hall", "Christopher",
    "Nancy Young", "Matthew", "Betty Wright", "Anthony", "Lisa Green",
    "Joshua", "Patricia Baker", "Andrew", "Barbara Nelson", "Joseph",
    "Margaret Mitchell", "Charles", "Susan Roberts", "Paul", "Dorothy Phillips",
    "Mark", "Sandra Parker", "Steven", "Ashley Edwards", "Kevin",
    "Kimberly Stewart", "Brian", "Michelle Morris", "George", "Deborah Reed",
    "Edward", "Amanda Morgan", "Ronald", "Stephanie Murphy", "Kenneth",
    "Rebecca Rivera", "Jason", "Sharon Richardson", "Jeffrey", "Cynthia Howard",
    "Ryan", "Kathleen Torres", "Jacob", "Amy Gray", "Gary",
    "Angela James", "Nicholas", "Melissa Brooks", "Eric", "Brenda Sanders",
    "Jonathan", "Rachel Bennett", "Stephen", "Katherine Barnes", "Larry",
    "Emma Henderson", "Scott", "Megan Jenkins", "Frank", "Hannah Powell",
    "Raymond", "Olivia Patterson", "Gregory", "Chloe Flores", "Benjamin",
    "Victoria Simmons", "Patrick", "Samantha Bryant", "Alexander", "Isabella Griffin",
    "Jack", "Sophia Hayes", "Dennis", "Mia Jenkins", "Jerry",
    "Ava Simmons", "Tyler", "Grace Russell", "Aaron", "Zoe Hayes",
    "Henry", "Lily Jenkins", "Ethan", "Ella Simmons", "Mason Bryant"
]

project_names = [
    "Apollo", "Mercury", "Gemini", "Artemis", "Orion",
    "Voyager", "Pioneer", "Galileo", "Cassini", "Juno",
    "Kepler", "Hubble", "Chandra", "Spitzer", "Webb",
    "Curiosity", "Perseverance", "Opportunity", "Spirit", "Pathfinder",
    "Insight", "Phoenix", "Viking", "Mariner", "Surveyor",
    "Lunar Orbiter", "Ranger", "New Horizons", "Dawn", "Stardust"
]

memory = {}

def generate_random_highlight(company_names, people_names, project_names):
    project = random.choice(project_names)
    companies = random.sample(company_names, random.randint(1, 2))
    people = random.sample(people_names, random.randint(1, 3))
    word_count = random.randint(80, 120)
    global memory
    prompt = f"Generate a '{word_count}'-word highlight for the project named \"'{project}'\" involving companies {', '.join(companies)} and employees {', '.join(people)}. Make sure to include all of these named entities. You might want to include impactful statistics to make the highlight engaging. return only one of the highlights generated, with NOTHING else before or after that.\n"+\
        "Use sentence structure and styles that are different than:{" + "".join(memory.values()) + "}"
        
    print(colored(prompt, 'red'))

    response = completion(
        model=my_model,
        messages=[
            {"role": "system", "content": "You are a senior leader in a large organization"},
            {"role": "user", "content": prompt}
        ],
        temperature=1,
        top_p=0.5
    )
    highlight = response['choices'][0]['message']['content']

    highlight_data = {
        "projects": project,
        "companies": companies,
        "people": people
    }

    with open('generated_highlight_samples.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        highlight_data_json = json.dumps(highlight_data)
        writer.writerow([highlight, highlight_data_json])
        memory[str(highlight_data_json)] = highlight
    print(colored(highlight, 'green'))
    return [highlight, highlight_data_json]

class HighlightSchema(BaseModel):
    projects: List[str]
    companies: List[str]
    people: List[str]

def extract_entities(highlight):
    prompt = f"Identify the project names, company names, and people names in the following highlight: '{highlight}'"

    response = completion(
        model=my_model,
        messages=[
            {"role": "system", "content": "You are a data extraction tool."},
            {"role": "user", "content": prompt}
        ],
        response_format=HighlightSchema,
        temperature=0
    )
    identified_entities = response['choices'][0]['message']['content']
    return identified_entities    

class ComparisonSchema(BaseModel):
    different_entities: int

def main():

    for _ in range(100):
        try:
            [highlight, highlight_data_json] = generate_random_highlight(company_names, people_names, project_names)
            print(colored(highlight_data_json, 'magenta'))
            
            identified_entities_json = extract_entities(highlight)
            print(colored(identified_entities_json, 'blue'))
            
            comparison_prompt = f"Compare the following two JSON objects and determine if they have the same entity names:\n\nJSON 1: {highlight_data_json}\n\nJSON 2: {json.dumps(identified_entities_json)}, ignore structural differences, only focus on the names that show up in each. return the number of different entities"

            comparison_response = completion(
            model=my_model,
            messages=[
            {"role": "system", "content": "You are a JSON comparison tool."},
            {"role": "user", "content": comparison_prompt}
            ],
            response_format=ComparisonSchema,
            temperature=0
            )
            comparison_result = ComparisonSchema.parse_raw(comparison_response['choices'][0]['message']['content'])
            if comparison_result.different_entities == 0:
                print(colored("No differences found", 'yellow'))
            else:
                print(colored(f"Number of different entities: {comparison_result.different_entities}", 'yellow'))
        except RateLimitError:
            print(colored("Rate limit exceeded. Waiting for 60 seconds before retrying...", 'red'))
            sleep(60)
            continue


def create_conversation(sample):
  return {
    "messages": [
      {"role": "system", "content": "You are a data extraction tool. Return answers in JSON format only."},
      {"role": "user", "content": "Identify the project names, company names, and people names in the following highlight: '" + sample["highlight"] + "'"},
      {"role": "assistant", "content": sample["highlight_data"]}
    ]
  }

def transform_to_trainable_json():
    with open('generated_highlight_samples.csv', mode='r') as file:
        reader = csv.reader(file)
        conversations = []
        for row in reader:
            highlight, highlight_data = row
            sample = {
            "highlight": highlight,
            "highlight_data": highlight_data
            }
            conversation = create_conversation(sample)
            conversations.append(conversation)
        
        with open('trainable_data.json', 'w') as json_file:
            json.dump(conversations, json_file, indent=4)