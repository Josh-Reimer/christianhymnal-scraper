import ollama

def load_prompt_from_file(filepath):
    """Load prompt content from a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def ask_ollama(prompt, model="phi3:mini"):
    """Send a prompt to Ollama and get the response."""
    try:
        response = ollama.generate(model=model, prompt=prompt)
        return response['response']
    except Exception as e:
        return f"Error: {e}"

def main():
    # Load prompt from file
    prompt_file = "prompts/text-extract-prompt.md"
    
    try:
        prompt = load_prompt_from_file(prompt_file)
        print(f"Loaded prompt from {prompt_file}")
        print(f"Prompt: {prompt[:100]}...\n")  # Show first 100 chars
        
        # Ask Ollama
        print("Asking Ollama...")
        response = ask_ollama(prompt, model="phi3:mini")
        
        print("\n" + "="*50)
        print("Response:")
        print("="*50)
        print(response)
        
    except FileNotFoundError:
        print(f"Error: Could not find {prompt_file}")
        print("Please create a prompt.txt file with your question.")

if __name__ == "__main__":
    main()