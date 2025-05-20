import azure.functions as func
import logging
from src.services.Model_service import ModelService
from src.repository.di_repository import DocIntRepository
from src.repository.cosmos_repository import CosmosRepository
from src.repository.aoi_repository import AOIRepository
from src.repository.st_repository import STRepository
import os
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

diendpoint = os.environ["DOC_INT_ENDPOINT"]
oaiendpoint = os.environ["AOI_ENDPOINT"]
stconn = os.environ["ST_ACOUNNT_URL"]
oai_key = os.environ["AOI_KEY"]
base_url = os.environ["URL_BASE"]
cosmos_url = os.environ["COSMOS_URL"]
cosmos_key = os.environ["COSMOS_KEY"]
azure_cosmos = CosmosRepository(cosmos_url=cosmos_url,cosmos_key=cosmos_key)
azuredi = DocIntRepository(doc_int_endpoint=diendpoint)
azure_oi = AOIRepository(oaiendpoint,oai_key)
azure_st = STRepository(stconn)
modelService = ModelService(azure_di=azuredi,azure_oi=azure_oi,azure_st=azure_st,azure_cosmos=azure_cosmos,base_url=base_url)



@app.route(route="Process", methods=["POST"])
def Process(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        content_type = req.headers.get('Content-Type', '')
        if 'multipart/form-data' not in content_type:
            return func.HttpResponse(
                "Tipo de contenido no soportado. Se espera multipart/form-data",
                status_code=400
            )

        pdf_files = req.files
        if pdf_files is None:
            return func.HttpResponse(
                "No se encontró el campo 'files' en la petición",
                status_code=400
            )       

        result = modelService.process(pdf_files)

        return func.HttpResponse(result, status_code=200, mimetype="application/json")
     

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

@app.route(route="swagger", methods=["GET"])
def swagger_json(req: func.HttpRequest) -> func.HttpResponse:
    with open("swagger.json", "r") as f:
        swagger_content = f.read()

    return func.HttpResponse(
        swagger_content,
        mimetype="application/json"
    )
@app.route(route="docs", methods=["GET"])
def docs_html(req: func.HttpRequest) -> func.HttpResponse:
    with open("swagger.html", "r") as f:
        html = f.read()

    return func.HttpResponse(html, mimetype="text/html")
