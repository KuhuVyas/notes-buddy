import os
import torch  # Import torch to check CUDA availability
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import BM25Retriever, FARMReader
from haystack.pipelines import SearchSummarizationPipeline
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Initialize InMemory document store (no Elasticsearch required)
document_store = InMemoryDocumentStore(use_bm25=True)


# Load documents from a folder (`notes`) and index them into the in-memory document store
def load_and_index_documents(folder_path):
    documents = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), "r", encoding = 'utf-8') as file:
                content = file.read()
                documents.append({
                    "content": content,
                    "meta": {"source": filename}
                })
    # Index the documents into InMemoryDocumentStore
    document_store.write_documents(documents)

# Initialize the retriever (BM25Retriever in this case)
retriever = BM25Retriever(document_store=document_store)

# Load model directly
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-large")

# Move model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)  # Move model to GPU (if available)

# Initialize FARMReader with the model name
reader = FARMReader(model_name_or_path=model) 

# Define the pipeline for extractive question answering
pipeline = SearchSummarizationPipeline(reader, retriever)

# Function to run the RAG pipeline and return the answer as a string
def run_rag_pipeline(query):
    # Tokenize the query and move inputs to GPU if available
    inputs = tokenizer(query, return_tensors="pt").to(device)
    
    # Retrieve documents based on the query
    result = pipeline.run(query=query)
    
    # Extract the best answer from the retrieved documents
    if result["answers"]:
        answer = f'{result["answers"][0].answer} {(result["answers"][1].answer)}'
    else:
        answer = "No answer found."
    
    # Return the answer as a string
    return answer


# create a vector store to store the conversation between users and chatbot.
class Conversation:
    def __init__(self):
        self.conversation_history = []

    def add_exchange_q(self, user1_input):
        # Format the conversation as "User1: input" and "User2: output"
        exchange = f'\nQuery: "{user1_input}"'
        # Append the exchange to the conversation history
        self.conversation_history.append(exchange)
    
    def add_exchange_o(self, user2_input):
        # Format the conversation as "User1: input" and "User2: output"
        exchange = f'\nOutput: "{user2_input}"'
        # Append the exchange to the conversation history
        self.conversation_history.append(exchange)

    def show_conversation(self):
        # Display the full conversation history
        return "\n\n".join(self.conversation_history)
