import logging
from azure.identity import DefaultAzureCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from src.interfaces.di_interface import DocIntInterface
from azure.core.credentials import AzureKeyCredential


class DocIntRepository(DocIntInterface):

   

    def __init__(self, doc_int_endpoint):
        # credential = DefaultAzureCredential()
        credential = AzureKeyCredential("8V9ZK1hQ2Egh08RL2sYI3aFKxWuybgLFHrbkST258s3uRKBkxzx7JQQJ99BEACYeBjFXJ3w3AAALACOG5R66")
        self.client = DocumentIntelligenceClient(doc_int_endpoint, credential)
        


    def Process(self, filestream):
    
        try:
            logging.info(f"[DocIntRepository - process] - initialize")

            poller = self.client.begin_analyze_document(model_id="prebuilt-read",body=filestream,pages="1-10")
            result: AnalyzeResult = poller.result()
                # 1) Contenido puro
            content = result.content
                # 2) Recopilar confidencias de líneas
            line_confidences = []
            for page in result.pages:
                for word in page.words:  # cada línea es DocumentLine
                    line_confidences.append(word.confidence)

            # 4) Cálculo de promedios
            avg_line_confidence = (
                sum(line_confidences) / len(line_confidences)
                if line_confidences else None
            )
            
            logging.warning("Finalizando Respuestas de DI")
            # logging.error(f"resultado {result.content}")
            return {
                "content": content,
                "average_page_confidence": avg_line_confidence,
            }

        except Exception as e:
            logging.error(f"Error al ejecutar openai: {str(e)}")
            raise ValueError(f"[DocIntRepository - process] - Error: {str(e)}")



