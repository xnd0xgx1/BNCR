import logging
from src.interfaces.aoi_interface import AOIInterface
from openai import AzureOpenAI
import json
# from azure.core.credentials import AzureKeyCredential
import re

class AOIRepository(AOIInterface):

   

    def __init__(self, endpoint,key):
        self.client = AzureOpenAI(
            api_key=key,  
            api_version="2024-12-01-preview",
            azure_endpoint = endpoint
            )
    
    def clean_json_string(self,s: str) -> str:
        """
        Extrae el fragmento entre el primer '{' y el último '}', o entre el primer '['
        y el último ']' si no hay objetos, y devuelve esa subcadena.
        """
        # Primero, elimina posibles prefijos como "json\n" o ```json
        for prefix in ("json\n", "```json", "```"):
            if s.startswith(prefix):
                s = s[len(prefix):]
        s = s.strip()

        # Decide si es un objeto o un array
        if s.startswith("{") and "}" in s:
            start = s.find("{")
            end = s.rfind("}") + 1
        elif s.startswith("[") and "]" in s:
            start = s.find("[")
            end = s.rfind("]") + 1
        else:
            # Busquemos igual un objeto dentro de la cadena
            start = s.find("{")
            end = s.rfind("}") + 1
            if start == -1 or end == 0:
                # No parece contener JSON; devolvemos entero y dejaremos que json.loads falle
                return s

        candidate = s[start:end]

        # Eliminamos posibles marcas de bloque de código restantes
        return candidate.strip().strip("```").strip()

        
    def Call(self,content):
        logging.info(f"Content on AOI {content}")
        response = self.client.chat.completions.create(
            model='gpt-4o',
            messages=[
                {
                    "role": "system",
                    "content": """Eres un agente especializado en extracción de campos de estados financieros, debes extraer siempre los siguientes campos en un json, RETORNA SOLO JSON siempre en un formato válido sin añadir o modificar los nombres de los campos SIEMPRE SERAN VALORES NUMERICOS EN CASO DE NO ENCONTRAR UNO RETORNA EL DEFAULT 0 EN EL CAMPO, IDENTIFICA TODOS LOS PERIODOS EN EL ESTADO FINANCIERO SIEMPRE SON AL MENOS 2, No coloques numeros negativos solo el valor: 
                      {
                        "periodos": [
                            {
                            "año": 2023,
                            "estadoResultados": {
                                "Ingresos": 1200000,
                                "Costos": 700000,
                                "Gastos": 100000,
                                "Depreciación y Amortización": 50000,
                                "Gastos de Venta": 30000,
                                "Gastos de Administración": 20000,
                                "Otros Gastos de Operación": 10000,
                                "Gastos Financieros": 15000,
                                "Producto Financiero": 5000,
                                "Ingreso No Efectivo": 20000,
                                "Otros Gastos": 8000,
                                "Otros Ingresos": 12000,
                                "Impuesto sobre la renta": 30000
                            },
                            "balanceGeneral": {
                                "activosCirculantes": {
                                "Caja o Bancos": 150000,
                                "Inversiones en Valores": 50000,
                                "Ctas y Docs por Cobrar Comerciales": 80000,
                                "Inventario Terminado": 60000,
                                "Otros Inventarios": 30000,
                                "Otros Activos Circulantes": 20000
                                },
                                "activosNoCirculantes": {
                                "Terreno": 100000,
                                "Construcciones en Proceso": 50000,
                                "Edificio y Mejoras": 250000,
                                "Maquinaria, Mobiliario y Equipo": 200000,
                                "Revaluación de Activos": 30000,
                                "Otros Activos Fijos": 10000,
                                "Depec. Acum. Histórica": 80000,
                                "Cuentas por Cobrar L.P.": 40000,
                                "Ctas. por Cobrar Socios": 20000,
                                "Inversiones en Subsidiarias": 60000,
                                "Otros Activos de Largo Plazo": 15000,
                                "Activo Diferido": 10000
                                },
                                "pasivosCirculantes": {
                                "Préstamos Bancarios de C.P.": 70000,
                                "Porción Circulante Largo Plazo": 20000,
                                "Ctas. por Pagar Proveedores": 60000,
                                "Otras Cuentas por Pagar": 15000,
                                "Imp/ Renta por Pagar": 10000,
                                "Otros Pasivos de Corto Plazo": 8000
                                },
                                "pasivosLargoPlazo": {
                                "Préstamos Bancarios de L.P.": 100000,
                                "Ctas por Pagar Filiales L.P.": 20000,
                                "Otros Pasivos de L.P.": 25000,
                                "Pasivo Diferido": 12000
                                },
                                "capital": {
                                "Capital Social": 300000,
                                "Aportaciones por Capitalizar": 20000,
                                "Reserva Legal": 10000,
                                "Otros": 5000,
                                "Superavit por Revaluación": 30000,
                                "Utilidad (Pérdida) Acumulada": 50000,
                                "Utilidad (Pérdida) de Período": 70000
                                }
                            }
                            }
                           
                        ]
                        }





                    """,
                },
                {
                    "role": "user",
                    "content": "Extrae los campos de este contenido fuente: " + content,
                }
            ]
        )
        responseoai = response.choices[0].message.content.replace("json\n","")
        logging.warning(f"Respuesta del openai: {responseoai}")
        cleaned = self.clean_json_string(responseoai)
        logging.info(f"Cleaned: {cleaned}")
        try:
            
            parsed = json.loads(cleaned)
            return parsed
        except json.JSONDecodeError as e:
            logging.warning(f"Error parsing json: {e}")
            return json.loads("{}")