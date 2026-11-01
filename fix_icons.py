import glob

replacements = {
    'page_icon="??"': 'page_icon=":gear:"',
}

files = glob.glob('app/pages/*.py') + ['app/app.py']
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if '01_Overview' in f:
        content = content.replace('page_icon="??"', 'page_icon=":bar_chart:"')
    elif '02_Data_Upload' in f:
        content = content.replace('page_icon="??"', 'page_icon=":inbox_tray:"')
    elif '03_Profiling' in f:
        content = content.replace('page_icon="??"', 'page_icon=":microscope:"')
    elif '04_ETL' in f:
        content = content.replace('page_icon="??"', 'page_icon=":gear:"')
    elif '05_Warehouse' in f:
        content = content.replace('page_icon="??"', 'page_icon=":package:"')
    elif '06_Data_Quality' in f:
        content = content.replace('page_icon="??"', 'page_icon=":memo:"')
    elif '07_MLOps' in f:
        content = content.replace('page_icon="??"', 'page_icon=":robot_face:"')
    elif '08_Monitoring' in f:
        content = content.replace('page_icon="??"', 'page_icon=":chart_with_upwards_trend:"')
    elif '09_Reports' in f:
        content = content.replace('page_icon="??"', 'page_icon=":page_facing_up:"')
    elif '10_BI_Dashboard' in f:
        content = content.replace('page_icon="??"', 'page_icon=":bar_chart:"')
    elif '11_Data_Explorer' in f:
        content = content.replace('page_icon="??"', 'page_icon=":mag:"')
    elif '12_Settings' in f:
        content = content.replace('page_icon="??"', 'page_icon=":gear:"')
    elif 'app.py' in f:
        content = content.replace('page_icon="??"', 'page_icon=":house:"')
    else:
        content = content.replace('page_icon="??"', 'page_icon=":gear:"')

    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print("Icons fixed.")
