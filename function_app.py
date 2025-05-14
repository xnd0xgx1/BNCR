import azure.functions as func
import logging
from src.services.Model_service import ModelService
from src.repository.di_repository import DocIntRepository
from src.repository.aoi_repository import AOIRepository
from src.repository.st_repository import STRepository
import os
from io import BytesIO

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

diendpoint = os.environ["DOC_INT_ENDPOINT"]
oaiendpoint = os.environ["AOI_ENDPOINT"]
stconn = os.environ["ST_CONNECTIONSTRING"]
azuredi = DocIntRepository(doc_int_endpoint=diendpoint)
azure_oi = AOIRepository(oaiendpoint)
azure_st = STRepository(stconn)
modelService = ModelService(azure_di=azuredi,azure_oi=azure_oi,azure_st=azure_st)



@app.route(route="Process", methods=["POST"])
def Process(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        content_type = req.headers.get('Content-Type', '')
        if content_type == 'application/pdf':
            logging.info("[ProcessDocument] - recibiendo PDF como cuerpo binario")
            file_bytes = req.get_body()  # obtener el contenido binario del PDF
            file_stream = BytesIO(file_bytes)

            # Procesar el archivo
            result = modelService.processfase2(file_stream)

            return func.HttpResponse(result, status_code=200, mimetype="application/json")
        else:
            return func.HttpResponse("Tipo de contenido no soportado", status_code=400)

    except Exception as e:
        logging.error(f"Error procesando el documento: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)


@app.route(route="excel", methods=["GET"])
def GetExcel(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Procesando solicitud GET para recuperar Excel desde Blob Storage")

    try:
        # Obtener el nombre del documento desde los parámetros de la URL
        document_name = req.params.get("nombre")
        if not document_name:
            return func.HttpResponse("El parámetro 'nombre' es requerido.", status_code=400)

        # Obtener el archivo desde el repositorio (Blob Storage)
        file_bytes = modelService.getdocument(document_name)

        # Retornar el archivo como respuesta binaria
        return func.HttpResponse(
            body=file_bytes,
            status_code=200,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={document_name}"
            }
        )

    except Exception as e:
        logging.error(f"Error al recuperar el documento: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
