from datetime import datetime
import uuid
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from src.interfaces.cosmos_interface import CosmosInterface

class CosmosRepository(CosmosInterface):
    def __init__(
        self,
        cosmos_url: str,
        cosmos_key: str,
        database_name: str = "TrenCreditoIA",
        container_name: str = "Registros",
        partition_key_path: str = "/id"
    ):
        # Conexión al cliente de Cosmos
        self.client = CosmosClient(url=cosmos_url, credential=cosmos_key)
        # Base de datos (se crea si no existe)
        self.database = self.client.create_database_if_not_exists(id=database_name)
        # Contenedor (se crea si no existe)
        self.container = self.database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path=partition_key_path),
            offer_throughput=400
        )

    def save_record(self, record: dict) -> dict:
        """
        Inserta un registro en Cosmos DB. 
        Si el record no trae 'id', se genera uno nuevo. 
        Siempre añade un campo 'timestamp' con la hora UTC actual.
        Devuelve el item que creó Cosmos.
        """
        # Aseguramos que haya un id
        if "id" not in record:
            record["id"] = str(uuid.uuid4())
        # Añadimos timestamp para ordenarlo después
        record["timestamp"] = datetime.utcnow().isoformat()
        # Insertamos el item
        created_item = self.container.create_item(body=record)
        return created_item

    def get_latest_by_field(self, field_name: str, field_value) -> dict:
        """
        Busca en el contenedor los registros donde field_name == field_value,
        los ordena por timestamp descendente y devuelve sólo el más reciente.
        Si no hay resultados, devuelve None.
        """
        query = f"""
            SELECT TOP 1 * 
            FROM c 
            WHERE c.{field_name} = @value 
            ORDER BY c.timestamp DESC
        """
        parameters = [{"name": "@value", "value": field_value}]
        try:
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items[0] if items else None
        except exceptions.CosmosHttpResponseError as e:
            # Manejo básico de errores
            print(f"Error al ejecutar la consulta: {e.message}")
            return None
