# convert_all_xls_to_xlsx.py
import os
from collections import Counter
from typing import List, Dict, Any
import win32com.client as win32

# Directorios
input_xls_directory = os.path.join("Valor_Presente_y_procesador", "input", "xls")
output_xlsx_directory = os.path.join("Valor_Presente_y_procesador", "input", "xlsx")


def convert_file_using_excel(
    input_file_path: str,
    output_file_path: str,
    messages_mode: str = "debug",
    retry_on_error: bool = True,
) -> None:
    if messages_mode == "debug":
        print(f"[DEBUG] Converting: {input_file_path}")

    # Excel POR ARCHIVO (más seguro si alguno se cuelga)
    excel_application = win32.Dispatch("Excel.Application")
    
    try:
        excel_application.Visible = False
        excel_application.DisplayAlerts = False
    except AttributeError as e:
        if messages_mode == "debug":
            print(f"[DEBUG] Warning: Could not set Excel properties: {e}")
        # Continuar sin configurar propiedades
    
    try:
        workbook = excel_application.Workbooks.Open(os.path.abspath(input_file_path))
        try:
            workbook.SaveAs(os.path.abspath(output_file_path), FileFormat=51)  # 51 = xlsx
            if messages_mode == "debug":
                print(f"[DEBUG] Saved: {output_file_path}")
        finally:
            workbook.Close()
    except AttributeError as e:
        # Si falla, intentar con otra instancia limpia de Excel
        if retry_on_error:
            if messages_mode == "debug":
                print(f"[DEBUG] Retrying with clean Excel instance...")
            try:
                excel_application.Quit()
            except:
                pass
            # Reintentar sin retry para evitar bucle infinito
            convert_file_using_excel(input_file_path, output_file_path, messages_mode, retry_on_error=False)
        else:
            raise
    finally:
        try:
            excel_application.Quit()
            if messages_mode == "debug":
                print("[DEBUG] Excel instance closed")
        except:
            pass


def convert_all_xls_files_in_folder(messages_mode: str = "debug") -> Dict[str, Any]:
    """
    Convierte todos los .xls de input_xls_directory a .xlsx en output_xlsx_directory.

    messages_mode:
        - "debug"   -> imprime detalle por archivo y errores individuales
        - "resumen" -> imprime solo estadísticas agregadas al final
    """
    print("\n" + "=" * 80)
    print("CONVERTIDOR .XLS → .XLSX USANDO EXCEL")
    print("=" * 80)

    if not os.path.exists(input_xls_directory):
        print(f"[DEBUG] Carpeta de entrada no existe: {input_xls_directory}")
        return {}

    if not os.path.exists(output_xlsx_directory):
        os.makedirs(output_xlsx_directory, exist_ok=True)
        if messages_mode == "debug":
            print(f"[DEBUG] Carpeta de salida creada: {output_xlsx_directory}")

    list_of_xls_files: List[str] = [
        name for name in os.listdir(input_xls_directory)
        if name.lower().endswith(".xls")
    ]

    if not list_of_xls_files:
        print("[DEBUG] No .xls files found in input folder")
        return {}

    if messages_mode == "debug":
        print(f"[DEBUG] Found {len(list_of_xls_files)} .xls files")
        for index, file_name in enumerate(list_of_xls_files, start=1):
            print(f"  {index}. {file_name}")
    else:
        print(f"Archivos .xls encontrados: {len(list_of_xls_files)}")

    # Detectar ya convertidos
    existing_xlsx_base_names = {
        os.path.splitext(name)[0].lower()
        for name in os.listdir(output_xlsx_directory)
        if name.lower().endswith(".xlsx")
    }

    files_already_converted = 0
    files_converted_now = 0
    files_failed = 0
    error_records: List[Dict[str, Any]] = []

    for input_file_name in list_of_xls_files:
        base_name, _ = os.path.splitext(input_file_name)
        base_name_lower = base_name.lower()

        input_file_path = os.path.join(input_xls_directory, input_file_name)
        output_file_name = base_name + ".xlsx"
        output_file_path = os.path.join(output_xlsx_directory, output_file_name)

        # Ya existe .xlsx para este .xls
        if base_name_lower in existing_xlsx_base_names:
            files_already_converted += 1
            if messages_mode == "debug":
                print(f"[DEBUG] Skipping (already converted): {input_file_path}")
            continue

        try:
            convert_file_using_excel(
                input_file_path=input_file_path,
                output_file_path=output_file_path,
                messages_mode=messages_mode,
            )
            files_converted_now += 1

        except Exception as error:
            files_failed += 1
            error_records.append(
                {
                    "file_name": input_file_name,
                    "error_type": type(error),
                    "error_message": str(error),
                }
            )
            if messages_mode == "debug":
                print(f"\n[DEBUG] ERROR converting: {input_file_name}")
                print(f"[DEBUG] Type: {type(error).__name__}")
                print(f"[DEBUG] Message: {error}")

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN CONVERSIÓN .XLS → .XLSX")
    print("=" * 80)
    print(f"Total .xls encontrados:          {len(list_of_xls_files)}")
    print(f"Ya convertidos previamente:      {files_already_converted}")
    print(f"Convertidos en esta ejecución:   {files_converted_now}")
    print(f"Fallidos en esta ejecución:      {files_failed}")
    print("=" * 80)

    if messages_mode == "resumen" and error_records:
        print("\n📊 ESTADÍSTICAS DE ERRORES (MODO RESUMEN)")
        error_counter = Counter(record["error_type"] for record in error_records)
        for error_type, count in error_counter.items():
            print(f"  - {error_type.__name__}: {count} archivo(s)")

        print("\nEjemplo de error por tipo:")
        example_by_type: Dict[type, Dict[str, Any]] = {}
        for record in error_records:
            error_type = record["error_type"]
            if error_type not in example_by_type:
                example_by_type[error_type] = record

        for error_type, example in example_by_type.items():
            print(f"\n  {error_type.__name__}:")
            print(f"    Archivo: {example['file_name']}")
            print(f"    Mensaje: {example['error_message']}")

    return {
        "total_xls_files": len(list_of_xls_files),
        "already_converted": files_already_converted,
        "converted_now": files_converted_now,
        "failed": files_failed,
        "errors": error_records,
    }


if __name__ == "__main__":
    # Cambia a "resumen" si quieres menos ruido:
    convert_all_xls_files_in_folder(messages_mode="debug")
    # convert_all_xls_files_in_folder(messages_mode="resumen")
