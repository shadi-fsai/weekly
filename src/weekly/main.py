from litellm import completion

my_model = 'ollama/llama3.2'
my_api_base = "http://localhost:11434"

def init():
    with open('orgcontext.txt', 'r') as file:
        org_context = file.read()

    with open('highlight-examples.txt', 'r') as file:
        highlight_examples = file.read()

    with open('workstream-importance.txt', 'r') as file:
        workstream_importance = file.read()

    response = completion(
        model=my_model, 
        messages=[
            {"role": "system", "content": "You are a senior leader in a large organization, you are writing a weekly progress report that will be distributed to your team, your manager, and your cross functional partners."},
            {"role": "system", "content": "Here is some context about your organization {" + org_context + "}"},
            {"role": "system", "content": "The following are examples of what highlights look like: {" + highlight_examples + "}"},
            {"role": "system", "content": "The following are the existing workstreams and their importance: {" + workstream_importance + "}"},            
        ],
        api_base=my_api_base  # Ollama's default address
    )

def main():
    init()

    response = completion(
        model=my_model, 
        messages=[
            {"role": "user", "content": "Write a highlight for the following outcome: we hired a new head of operations to lead our new community launch. "}
        ],
        api_base=my_api_base  # Ollama's default address
    )

    print(response['choices'][0]['message']['content'])

