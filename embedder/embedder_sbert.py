import torch
from sentence_transformers import SentenceTransformer

from config import WEIGHTS_PATH


class Embedder:
    """
    This class is responsible for creating embeddings of
    input sentences using a pre-trained sentence transformer model.
    """

    def __init__(self):
        """
        Initializes the Embedder class by creating an
        instance of the SentenceTransformer model and setting the device.
        """
        self.model = SentenceTransformer(WEIGHTS_PATH)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(device=self.device)

    def answer(self, query):
        """
        Generates the embedding of the input
        query using the SentenceTransformer model.

        Args:
        - query: The input query for which the
        embedding needs to be generated.

        Returns:
        - result: A dictionary containing the query
        embedding as a list of floating-point numbers.
        """
        with torch.no_grad():
            emb = self.model.encode(query, convert_to_tensor=True)

        result = {
            "query_embedding": [float(el) for el in torch.squeeze(emb)],
        }

        return result


if __name__ == "__main__":
    emb = Embedder()

    r = emb.answer("Ищу специалиста по ML")
