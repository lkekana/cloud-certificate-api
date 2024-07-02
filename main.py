from llm.openai import GPT4oStrategy

example_file_path = "samples\BenJoubert-BTech-IT-SoftwareDevelopment-2017-04-08_20240513_0001.pdf"
example_file = open(example_file_path, "rb")

def main():
    strategy = GPT4oStrategy()
    strategy.generate_response_from_file("Which institution issued this document?", example_file)
    
if __name__ == "__main__":
    main()