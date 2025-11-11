from google.cloud import bigquery
c=bigquery.Client(project='cosmic-rarity-473820-m7')
j=c.load_table_from_file(open('Tabla_Final_ARPRO_Completa.csv','rb'), 'cosmic-rarity-473820-m7.analytics_dataset.tabla_final_arpro_completa', job_config=bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.CSV, skip_leading_rows=1, autodetect=True))
j.result(); print('[DEBUG] ✅ Uploaded Tabla_Final_ARPRO_Completa!')
