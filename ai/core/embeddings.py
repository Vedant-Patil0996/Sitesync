from sentence_transformers import SentenceTransformer

# Load the local embedding model
# 'all-MiniLM-L6-v2' outputs 384 dimensions and is very fast/lightweight
model = SentenceTransformer('all-MiniLM-L6-v2')

def embed(text: str) -> list[float]:
    """
    Generate an embedding for the given text using a local SentenceTransformers model.
    """
    # The encode function returns a numpy array, which we convert to a list of floats
    embedding = model.encode(text)
    return embedding.tolist()
