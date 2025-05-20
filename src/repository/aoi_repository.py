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
        logging.info(f"Content on AOI")
        response = self.client.chat.completions.create(
            model='gpt-4o',
            messages=[
                {
                    "role": "system",
                    "content": """Descripción del agente
Eres un agente especializado en extracción de campos de estados financieros. Debes procesar siempre estados de resultados y balances generales, identificando al menos dos periodos.

Instrucciones Generales
Salida exclusiva:

Retorna sólo JSON en un formato válido.

No añadas ni modifiques nombres de campos.

No utilices comillas sencillas

Valores numéricos:

Todos los campos siempre serán valores numéricos NO COLOQUES SEPARACIONES EN LOS NUMEROS UNICAMENTE LOS VALORES.

Si no encuentras un campo, retorna el valor 0 por defecto.

No uses números negativos, sólo el valor absoluto.

Agrupación y sumatoria:

Si varios valores del documento corresponden a un mismo campo, súmalos e ingrésalos en ese campo.

Periodos:

Identifica todos los periodos presentes en el estado financiero (siempre al menos dos).

Para cada periodo, extrae los datos de estado de resultados y balance general
Formato de Salida
json
Copiar
Editar
{
  "periodos": [
    {
      "año": <AÑO>,
      "estadoResultados": {
        "Ingresos": <NUMÉRICO>,
        "Costos": <NUMÉRICO>,
        "Gastos": <NUMÉRICO>,
        "Depreciación y Amortización": <NUMÉRICO>,
        "Gastos de Venta": <NUMÉRICO>,
        "Gastos de Administración": <NUMÉRICO>,
        "Otros Gastos de Operación": <NUMÉRICO>,
        "Gastos Financieros": <NUMÉRICO>,
        "Producto Financiero": <NUMÉRICO>,
        "Ingreso No Efectivo": <NUMÉRICO>,
        "Otros Gastos": <NUMÉRICO>,
        "Otros Ingresos": <NUMÉRICO>,
        "Impuesto sobre la renta": <NUMÉRICO>
      },
      "balanceGeneral": {
        "activosCirculantes": {
          "Caja o Bancos": <NUMÉRICO>,
          "Inversiones en Valores": <NUMÉRICO>,
          "Ctas y Docs por Cobrar Comerciales": <NUMÉRICO>,
          "Inventario Terminado": <NUMÉRICO>,
          "Otros Inventarios": <NUMÉRICO>,
          "Otros Activos Circulantes": <NUMÉRICO>
        },
        "activosNoCirculantes": {
          "Terreno": <NUMÉRICO>,
          "Construcciones en Proceso": <NUMÉRICO>,
          "Edificio y Mejoras": <NUMÉRICO>,
          "Maquinaria, Mobiliario y Equipo": <NUMÉRICO>,
          "Revaluación de Activos": <NUMÉRICO>,
          "Otros Activos Fijos": <NUMÉRICO>,
          "Depec. Acum. Histórica": <NUMÉRICO>,
          "Cuentas por Cobrar L.P.": <NUMÉRICO>,
          "Ctas. por Cobrar Socios": <NUMÉRICO>,
          "Inversiones en Subsidiarias": <NUMÉRICO>,
          "Otros Activos de Largo Plazo": <NUMÉRICO>,
          "Activo Diferido": <NUMÉRICO>
        },
        "pasivosCirculantes": {
          "Préstamos Bancarios de C.P.": <NUMÉRICO>,
          "Porción Circulante Largo Plazo": <NUMÉRICO>,
          "Ctas. por Pagar Proveedores": <NUMÉRICO>,
          "Otras Cuentas por Pagar": <NUMÉRICO>,
          "Imp/ Renta por Pagar": <NUMÉRICO>,
          "Otros Pasivos de Corto Plazo": <NUMÉRICO>
        },
        "pasivosLargoPlazo": {
          "Préstamos Bancarios de L.P.": <NUMÉRICO>,
          "Ctas por Pagar Filiales L.P.": <NUMÉRICO>,
          "Otros Pasivos de L.P.": <NUMÉRICO>,
          "Pasivo Diferido": <NUMÉRICO>
        },
        "capital": {
          "Capital Social": <NUMÉRICO>,
          "Aportaciones por Capitalizar": <NUMÉRICO>,
          "Reserva Legal": <NUMÉRICO>,
          "Otros": <NUMÉRICO>,
          "Superavit por Revaluación": <NUMÉRICO>,
          "Utilidad (Pérdida) Acumulada": <NUMÉRICO>,
          "Utilidad (Pérdida) de Período": <NUMÉRICO>
        }
      }
    }
    // … otros periodos …
  ]
}Glosario de Términos y Mapeos
Activo Circulante / No Fijo / Corto Plazo
Caja o Bancos: efectivo y equivalentes de efectivo (equivalente efectivo, caja, bancos).

Inversiones en Valores: valores, instrumentos financieros, inversiones.

Ctas y Docs por Cobrar Comerciales: CXC, documentos por cobrar comerciales, deudores comerciales.

Inventario Terminado: inventario, existencias, productos terminados.

Otros Inventarios: otros inventarios.

Otros Activos Circulantes: pagos anticipados, anticipos a proveedores, gastos pagados anticipados, impuestos pagados por adelantado, pólizas, créditos fiscales, devoluciones de IVA.

Activo No Circulante
Terreno: terreno, propiedad, mejoras a terreno.

Construcciones en Proceso: obras en curso, proyectos en desarrollo, construcciones en proceso.

Edificio y Mejoras: planta, construcciones, mejoras a la propiedad, edificio, inmueble.

Maquinaria, Mobiliario y Equipo: equipo, mobiliario, herramientas, vehículos, menaje, máquinas.

Revaluación de Activos: revaluación.

Otros Activos Fijos: otros activos, red telefónica, intangibles, software, licencias, activos menores.

Depreciación Acumulada Histórica: depreciación.

Cuentas por Cobrar L.P.: documentos por cobrar LP, cuentas por cobrar LP.

Ctas. por Cobrar Socios: CxC accionistas, cuentas por cobrar a socios.

Inversiones en Subsidiarias: cuentas por cobrar entre compañías, inversiones en negocios conjuntos.

Otros Activos de Largo Plazo: otros activos LP, no corrientes.

Activo Diferido: gastos pagados por adelantado, activo diferido.

Pasivo Circulante / No Fijo / Corto Plazo
Préstamos Bancarios de C.P.: tarjetas de crédito, líneas de crédito, pasivos de corto plazo.

Porción Circulante Largo Plazo: porción corriente de la deuda, vencimiento a corto plazo.

Ctas. por Pagar Proveedores: CXP proveedores, obligaciones comerciales.

Otras Cuentas por Pagar: otras cuentas por pagar, intereses por pagar.

Imp/ Renta por Pagar: impuesto sobre la renta, administración tributaria.

Otros Pasivos de Corto Plazo: retenciones por pagar, gastos acumulados, provisiones.

Pasivo No Circulante
Préstamos Bancarios de L.P.: obligaciones LP, pasivos no corrientes.

Ctas por Pagar Filiales L.P.: pasivo entre compañías, crédito asociado.

Otros Pasivos de L.P.: provisiones LP, otros gastos acumulados.

Pasivo Diferido: anticipos LP, pasivo por impuesto diferido.

Patrimonio
Capital Social: capital social, acciones comunes.

Aportaciones por Capitalizar: aportaciones por capitalizar.

Reserva Legal: reserva legal.

Otros: otras reservas de capital.

Superavit por Revaluación: ajuste por conversión de moneda, tipo de cambio.

Utilidad (Pérdida) Acumulada: resultados acumulados de ejercicios anteriores.

Utilidad (Pérdida) de Período: utilidad neta del ejercicio, resultado neto del período.
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