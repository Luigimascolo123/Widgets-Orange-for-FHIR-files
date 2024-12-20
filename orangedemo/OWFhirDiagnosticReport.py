from Orange.data import Domain, Table
from Orange.widgets import widget, gui
import json
import re 
import requests
import pandas as pd
import Orange
from collections import OrderedDict
import numpy as np
import math
from functools import partial

class OWFhirTestInput(widget.OWWidget):
    name = "OWFhir DiagnosticReport"
    description = "test input"
    category = "Demo"
    
    class Inputs:
        list_of_paths = widget.Input("Bundle Resource Paths", list)

    class Outputs:
        processed_table = widget.Output("Processed DiagnosticReport Table", Table)


    def __init__(self):
        super().__init__()

        self.dataFrame = pd.DataFrame()
        self.dataFrameCleanning = pd.DataFrame()
        box = gui.widgetBox(self.controlArea,"")
        box.setFixedHeight(100)
        # self.set_input(self.Inputs.list_of_paths)
        ## campo per immettere stringa dell APi da cui fare richiesta
        self.test_input = "" ## inital default value for input
        self.input_line = gui.lineEdit(widget=box, master=self,value="test_input", 
                                       label="Input a fhir server endpoit to retrieve data for a patient ",validator=None,callback=self.validate_api)
        gui.button(box, master = self, label = "send", callback=self.validate_api)

        gui.separator(self)
        box2  = gui.widgetBox(self.controlArea,"")
        self.display_message = gui.widgetLabel(box2," ")        



    def validate_api(self):
        ## se input è una stringa valida che corrisponde alla forma di un endpoint, si passa alla funzione che fa la request
        api_pattern = r'^https?://(?:\w+\.)?\w+\.\w+(?:/\S*)?$'
        if re.match(api_pattern, self.test_input):
            self.make_request()
        else:
            print("input a valid fhir api")
            self.display_message.setText("ERROR: Input a valid FHIR API")

    def make_request(self):
        try:
            response = requests.get(self.test_input)
        except:
            print("error while making request")
            self.display_message.setText("error while making request")
            return
        # response = requests.get("https://spark.incendi.no/fhir/Patient/3")
        json_results = response.json()
        json_results = self.flatten_dict(json_results)
        all_data=pd.json_normalize(json_results)
        self.dataFrameCleanning = all_data
        self.commit_table()
        print("API Results: ", json_results)

    def flatten_dict(self, d, key ='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = key + sep + k if key else k

            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, val in enumerate(v):
                    if isinstance(val, dict):
                        items.extend(self.flatten_dict(val, f"{new_key}_{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}_{i}", val))
                
            else:
                items.append((new_key, v))
        
        return dict(items)

    def construct_domain(self, df):
        columns = OrderedDict(df.dtypes)
        
        def create_variable(col):
            if col[1].__str__().startswith('float'):
                return Orange.data.ContinuousVariable(col[0])
            elif col[1].__str__().startswith('int'):
                return Orange.data.ContinuousVariable(col[0])
            elif col[1].__str__().startswith('date'):
                df[col[0]] = df[col[0]].values.astype(np.str)
            elif col[1].__str__() == 'object':
                df[col[0]] = df[col[0]].astype(type(""))
            else:
                return Orange.data.StringVariable(col[0])

            return Orange.data.DiscreteVariable(col[0], values = df[col[0]].unique().tolist())
        res  = list(map(create_variable, columns.items()))
        return Domain([],metas=res)
    
    def commit_table(self):
        domain = self.construct_domain(self.dataFrameCleanning)
        orange_table = Orange.data.Table.from_list(domain = domain, rows = self.dataFrameCleanning.values.tolist())
        self.Outputs.processed_table.send(orange_table)
        
    def Nan_check(self, resource, itemPosition, item):
        resultText = []
        try:
            if math.isnan(resource):
                resultText.append(np.nan)
        except:
            try:
                resultText.append(resource[itemPosition][f'{item}'])
            except:
                resultText.append(np.nan)
        return resultText
        
    def data_cleanning(self):
        '''
        ResourceID = resource.id
        LOINC Code = resource.category.coding.code
        LOINC Diagnostic = resource.category.coding.display
        DiagnosticDate = resource.effectiveDateTime
        Doctor = resource.performer.display
        Test = resource.code.text
        Result = resource.result.display
        '''
        columnsName=["ResourceID",  "LOINC Code A", "LOINC Diagnostic A",  "LOINC Code B", "LOINC Diagnostic B", "DiagnosticDate", "Doctor", "Test", "Result"]
        self.dataFrameCleanning = pd.DataFrame(columns=columnsName)
        
        self.dataFrameCleanning["ResourceID"] =  self.dataFrame["resource.id"]
        
        resoruceCat = [x[0]["coding"] for x in list(self.dataFrame["resource.category"])]
        
        resoruceCatACode = list(map(partial(self.Nan_check, itemPosition=0, item="code"), resoruceCat))
        resoruceCatADisplay = list(map(partial(self.Nan_check, itemPosition=0, item="display"), resoruceCat))
        
        self.dataFrameCleanning["LOINC Code A"] = np.resize(resoruceCatACode,len(self.dataFrameCleanning))
        self.dataFrameCleanning["LOINC Diagnostic A"] = np.resize(resoruceCatADisplay,len(self.dataFrameCleanning))

        resoruceCatBCode = list(map(partial(self.Nan_check, itemPosition=1, item="code"), resoruceCat)) 
        resoruceCatBDisplay = list(map(partial(self.Nan_check, itemPosition=1, item="display"), resoruceCat))

        self.dataFrameCleanning["LOINC Code B"] = np.resize(resoruceCatBCode,len(self.dataFrameCleanning))
        self.dataFrameCleanning["LOINC Diagnostic B"] = np.resize(resoruceCatBDisplay,len(self.dataFrameCleanning))
        
        self.dataFrameCleanning["DiagnosticDate"] = self.dataFrame["resource.effectiveDateTime"]
        
        doctorText = list(map(partial(self.Nan_check, itemPosition=0, item="display"), self.dataFrame["resource.performer"]))
        self.dataFrameCleanning["Doctor"] =np.resize(doctorText,len(self.dataFrameCleanning))
        
        self.dataFrameCleanning["Test"] = self.dataFrame["resource.code.text"]
        
        resultText = list(map(partial(self.Nan_check, itemPosition=0, item="display"), self.dataFrame["resource.result"]))
        self.dataFrameCleanning["Result"] = np.resize(resultText,len(self.dataFrameCleanning))
        
        # self.dataFrameCleanning = self.dataFrameCleanning.astype(dtype= {
        #                                 'ResourceID': 'S4', 
        #                                 'LOINC Code A': 'object', 
        #                                 'LOINC Diagnostic A': 'object', 
        #                                 'LOINC Code B': 'object', 
        #                                 'LOINC Diagnostic B': 'object', 
        #                                 'DiagnosticDate': 'S4', 
        #                                 'Doctor': 'object', 
        #                                 'Test': 'object', 
        #                                 'Result': 'object'})
                     
    def checkResourceType(self, resource):
        if resource["resource"]["resourceType"] == "DiagnosticReport":
            return resource
    
    def create_dataset(self, path):
        df=pd.DataFrame()
        for index, nome in enumerate(path):
            if "json" in nome : 
                with open(nome, encoding="utf8") as f:
                    dat=json.load(f)

                    #Clean json for only resourceType = DiagnosticReport.
                    filterDiagnosticreport = filter(self.checkResourceType, dat["entry"])
                    dataNormalize=[pd.json_normalize(r) for r in filterDiagnosticreport]

                    f.close()
                df_Temporaly=pd.concat(dataNormalize)
                df=pd.concat([df,df_Temporaly])
                print(df.shape)
        return df
    
    @Inputs.list_of_paths
    def set_input(self, value):

        self.input_value = value
        if self.input_value is not None :
            print("recived this output from prev. widget : ", self.input_value)
            self.dataFrame = self.create_dataset(self.input_value)
        self.data_cleanning()
        self.commit_table()
        

        
#if __name__ == "__main__":
    #widgetpreview.WidgetPreview(OWFhirTestInput).run()


