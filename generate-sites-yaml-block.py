import pandas as pd

#
# Generates the sites block in .upptimerc.yml :
# https://github.com/HakaiInstitute/hakai-datasets-upptime/blob/master/.upptimerc.yml
#
url='https://catalogue.hakai.org/erddap/tabledap/allDatasets.csv?datasetID&datasetID!="allDatasets"&accessible="public"'

sites=pd.read_csv(url)['datasetID']

for dataset_id in sites:
    print (f"""  - name: {dataset_id}\n    url: https://catalogue.hakai.org/erddap/tabledap/{dataset_id}.htmlTable?time&time<=now-1week&distinct()
    expectedStatusCodes:
      - 200
      - 201
      - 404""")