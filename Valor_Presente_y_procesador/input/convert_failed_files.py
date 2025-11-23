# convert_failed_files.py
import os
import win32com.client as win32

# Directorios
input_xls_directory = os.path.join("Valor_Presente_y_procesador", "input", "xls")
output_xlsx_directory = os.path.join("Valor_Presente_y_procesador", "input", "xlsx")

# Solo los archivos que fallaron
failed_files = [
    "135 - Seguimiento Insumos.xls",
    "170 - Seguimiento Insumos.xls"
]

def convert_file_using_excel(input_file_path: str, output_file_path: str) -> None:
    print(f"[DEBUG] Converting: {input_file_path}")
    
    excel_application = win32.Dispatch("Excel.Application")
    
    try:
        excel_application.Visible = False
        excel_application.DisplayAlerts = False
    except AttributeError as e:
        print(f"[DEBUG] Warning: Could not set Excel properties: {e}")
    
    try:
        workbook = excel_application.Workbooks.Open(os.path.abspath(input_file_path))
        try:
            workbook.SaveAs(os.path.abspath(output_file_path), FileFormat=51)
            print(f"[DEBUG] ✅ Saved: {output_file_path}")
        finally:
            workbook.Close()
    except Exception as e:
        print(f"[DEBUG] ❌ Error: {e}")
        raise
    finally:
        try:
            excel_application.Quit()
            print("[DEBUG] Excel instance closed")
        except:
            pass


print("=" * 80)
print("CONVERSIÓN DE ARCHIVOS FALLIDOS")
print("=" * 80)

for file_name in failed_files:
    input_file_path = os.path.join(input_xls_directory, file_name)
    base_name = os.path.splitext(file_name)[0]
    output_file_path = os.path.join(output_xlsx_directory, f"{base_name}.xlsx")
    
    try:
        convert_file_using_excel(input_file_path, output_file_path)
    except Exception as error:
        print(f"FALLO FINAL: {file_name}")
        print(f"Tipo: {type(error).__name__}")
        print(f"Mensaje: {error}")
    
    print("-" * 80)

print("\n✅ Proceso completado")
