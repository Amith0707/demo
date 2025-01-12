import os
from flask import Flask, request, jsonify, render_template
from groclake.vectorlake import VectorLake
from groclake.datalake import DataLake
from groclake.modellake import ModelLake

# Flask App
app = Flask(__name__)
#api key is not being fetched error type shit 
# Set API key and account ID
GROCLAKE_API_KEY = '3ef815416f775098fe977004015c6193'
GROCLAKE_ACCOUNT_ID = '1748fdaba3d5f04bb0082c086621ebc9'

# Set environment variables
os.environ['GROCLAKE_API_KEY'] = GROCLAKE_API_KEY
os.environ['GROCLAKE_ACCOUNT_ID'] = GROCLAKE_ACCOUNT_ID

# Initialize components
vectorlake = VectorLake()
datalake = DataLake()
modellake = ModelLake()

# Global variables to store IDs
datalake_id = None
vectorlake_id = None

# Initialize DataLake and VectorLake on startup
def initialize_lakes():
    global datalake_id, vectorlake_id
    
    # Create DataLake if not exists
    if not datalake_id:
        datalake_create = datalake.create()
        if "datalake_id" in datalake_create:
            datalake_id = datalake_create["datalake_id"]
            print(f"DataLake created with ID: {datalake_id}")
        else:
            raise Exception("Failed to create DataLake")
    
    # Create VectorLake if not exists
    if not vectorlake_id:
        vector_create = vectorlake.create()
        if "vectorlake_id" in vector_create:
            vectorlake_id = vector_create["vectorlake_id"]
            print(f"VectorLake created with ID: {vectorlake_id}")
        else:
            raise Exception("Failed to create VectorLake")

    # Upload initial document
    document_url = "https://drive.google.com/uc?export=download&id=1h3LH5T8K52O8WAipeV6Uzp6xk13It3MR"
    upload_initial_document(document_url)

def upload_initial_document(document_url):
    # Push the document to DataLake
    payload_push = {
        "datalake_id": datalake_id,
        "document_type": "url",
        "document_data": document_url
    }
    data_push = datalake.push(payload_push)
    document_id = data_push.get("document_id")
    if not document_id:
        raise Exception("Failed to push document")

    print(f"Document pushed successfully with ID: {document_id}")

    # Fetch and process the document
    payload_fetch = {
        "document_id": document_id,
        "datalake_id": datalake_id,
        "fetch_format": "chunk",
        "chunk_size": "500"
    }
    data_fetch = datalake.fetch(payload_fetch)
    document_chunks = data_fetch.get("document_data", [])
    print(f"Document fetched successfully. Total chunks: {len(document_chunks)}")

    # Push chunks to VectorLake
    for chunk in document_chunks:
        vector_doc = vectorlake.generate(chunk)
        vector_chunk = vector_doc.get("vector")
        vectorlake_push_request = {
            "vector": vector_chunk,
            "vectorlake_id": vectorlake_id,
            "document_text": chunk,
            "vector_type": "text",
            "metadata": {}
        }
        vectorlake.push(vectorlake_push_request)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint for processing user queries."""
    try:
        # Get user query from request
        query = request.json.get("query")
        if not query:
            return jsonify({"error": "Query is required."}), 400

        # Generate vector for the user query
        vector_search_data = vectorlake.generate(query)
        search_vector = vector_search_data.get("vector")

        # Search VectorLake
        search_payload = {
            "vector": search_vector,
            "vectorlake_id": vectorlake_id,
            "vector_type": "text",
        }
        search_response = vectorlake.search(search_payload)
        search_results = search_response.get("results", [])
        
        # Construct enriched context
        enriched_context = " ".join([result.get("vector_document", "") for result in search_results])

        # Query ModelLake with enriched context
        payload = {
            "messages": [
                {"role": "system", "content": "You are an AI assistant providing accurate finance-related guidance."},
                {
                    "role": "user",
                    "content": f"Using the following context: {enriched_context}, "
                               f"answer the question: {query}."
                               """
                                # how to answer questions ?
                                - make sure that the answer you are providing is simple and not very complex.
                                - give the basic details about any scheme if asked [basic details include : who can apply, what it offers, and who it benifits]
                                - do not answer any general questions about general knowledge, just reply with "please ask a question related to finance, thank you".
                               """
                }
            ]
        }
        chat_response = modellake.chat_complete(payload)
        answer = chat_response.get("answer", "No answer received.")
        return jsonify({"answer": answer}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    initialize_lakes()  # Initialize lakes before starting the app
    app.run(host='0.0.0.0', port=5000, debug=True)