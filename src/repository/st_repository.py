

from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

from src.interfaces.st_interface import STInterface
from openpyxl import Workbook, load_workbook
from openpyxl.workbook.workbook import Workbook as OpenpyxlWorkbook
import io


class STRepository(STInterface):
    def __init__(self,  storage_connection_string, container_name="documents"):
        # Cliente para Document Intelligence
        
        # Cliente para Azure Blob Storage
        self.blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
        self.container_name = container_name
        
        try:
            self.container_client = self.blob_service_client.create_container(container_name)
        except Exception:
            self.container_client = self.blob_service_client.get_container_client(container_name)

   

    def Save(self, document_name: str, content) -> str:
        """
        Guarda un documento o un workbook modificado en el contenedor de blobs.
        Acepta bytes o instancia de openpyxl.Workbook.
        """
        # Serializar content
        if isinstance(content, OpenpyxlWorkbook):
            stream = io.BytesIO()
            content.save(stream)
            data = stream.getvalue()
        elif isinstance(content, (bytes, bytearray)):
            data = content
        else:
            raise TypeError("Content must be bytes or openpyxl Workbook instance.")
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=document_name)
        blob_client.upload_blob(data, overwrite=True)
        return f"Blob '{document_name}' guardado correctamente."

    def Get(self, document_name: str) -> bytes:
        """
        Descarga un documento desde el contenedor de blobs.
        """
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=document_name)
        blob_data = blob_client.download_blob()
        return blob_data.readall()
