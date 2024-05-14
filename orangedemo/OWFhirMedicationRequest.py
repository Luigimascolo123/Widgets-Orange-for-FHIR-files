import sys
import numpy
import tkinter as tk
from Orange.data import Domain, StringVariable, DiscreteVariable, ContinuousVariable, Table, Values, Tuple
from Orange.widgets import widget, gui, settings
from Orange.widgets.utils.signals import Input, Output

from tkinter import filedialog
import json
from Orange.widgets.utils import widgetpreview
import re 
import requests
import pandas as pd 

class OWFhirAnalyzieMedicationRequest(widget.OWWidget):
    name = "OWFhir MedicationRequest"
    description = "returns processed orange table for medication request FHIR resource"
    category = "Demo"
    
    class Inputs:
        list_of_paths = widget.Input("Bundle Resource Paths", list)

    class Outputs:
        processed_table = widget.Output("Processed MedicationRequest Table", Table)


    def __init__(self):
        super().__init__()


        # self.result_dict = {} ## dict for extracting all the nested info. in the resource
        # self.data_values = [] ## rows to append in the final table
        # self.string_values = []
        self.string_variables = ["resource_id", "resource_medicationCodeableConcept_text", "resource_subject_reference","resource_encounter_reference","resource_authoredOn",
                 "resource_requester_display","resource_reasonReference_0_reference"]
        self.numeric_variables = ["resource_dosageInstruction_0_timing_repeat_frequency", "resource_dosageInstruction_0_sequence", "resource_dosageInstruction_0_timing_repeat_period",
                     "resource_dosageInstruction_0_doseAndRate_0_doseQuantity_value"]
        self.cat_variables = ["resource_status", "resource_intent", "resource_medicationCodeableConcept_coding_0_code","resource_medicationCodeableConcept_coding_0_display",
                 "resource_dosageInstruction_0_timing_repeat_periodUnit","resource_dosageInstruction_0_asNeededBoolean",
                  "resource_dosageInstruction_0_doseAndRate_0_type_coding_0_code","resource_dosageInstruction_0_additionalInstruction_0_coding_0_display"]
        self.all_res = [] 
        self.all_keys = [] 
        self.addPrefix = False 


        box = gui.widgetBox(self.controlArea,"")
        box.setFixedHeight(100)
        # self.set_input(self.Inputs.list_of_paths)
        ## campo per immettere stringa dell APi da cui fare richiesta
        self.test_input = "" ## inital default value for input
        self.local_resource_path = ""
        self.input_line = gui.lineEdit(widget=box, master=self,value="test_input", label="Input a fhir server endpoit to retrieve data for a patient ",validator=None)
        gui.button(box, master = self, label = "send", callback=self.validate_api)

        gui.separator(self)
        box2  = gui.widgetBox(self.controlArea,"")
        box2.setFixedHeight(50)
        self.display_message = gui.widgetLabel(box2," ")        
        self.upload_button = gui.button(box2, self, label="Import one or more medication request resource", callback=self.selectMedicationRequests)
        
        # gui.button(box, master = self, label = "send", callback=self.extract_MedicationRequest)

        gui.separator(self)
        


    def selectMedicationRequests(self):
        self.local_resource_path = filedialog.askopenfilenames(title="Select JSON file(s)", filetypes=(("JSON files", "*.json"),))
        if self.local_resource_path:
            # self.addPrefix = True
            self.set_input(self.local_resource_path)



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
        # response = requests.get("https://hapi.fhir.org/baseR4/MedicationRequest/")
        json_results = response.json()
        
        medication_requests = self.extract_MedicationRequest(res_from_request=json_results)
        processed_resources = list(map(self.flatten_dict, medication_requests))
        [self.all_res.append(resource) for resource in processed_resources]
        self.create_table()
        

    def flatten_dict(self,d, key ='', sep='_'):
        
        items = []
        for k, v in d.items():
            new_key = key + sep + k if key else k
            if new_key not in self.all_keys:
                self.all_keys.append(new_key)
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
            


    def make_cat_variables(self):
        processed_cat_variables = []
        
        valid_columns = [col for col in self.cat_variables if col in self.df.columns]

        cat_x = self.df[valid_columns]
        # cat_x = cat_x.fillna("nan")
        
        for column in cat_x:
            cat_x.loc[:,column] = list(map(str,cat_x[column]))
            processed_cat_variables.append(DiscreteVariable(name = str(column), values = list(pd.unique(cat_x[column]))))
        return processed_cat_variables

    def make_domain(self):
        self.df = pd.DataFrame(self.all_res)
        if self.addPrefix:
            self.df = self.df.add_prefix("resource_")
        # print("self.df in cat variables = ", self.df.columns)
        self.df = self.df.fillna("nan")
        features_for_table = {
            "strings" : [],
            "categorical" : [],
            "timestamps" : [],
            "numeric"   :[]
        }
        # list(map(lambda x : features_for_table["strings"].append(StringVariable(name=x)),string_variables))
        # list(map(lambda x : features_for_table["categorical"].append(DiscreteVariable(name=x)),cat_variables))
        # list(map(lambda x : features_for_table["numeric"].append(ContinuousVariable(name=x)),numeric_variables))
        # list(map(lambda x : features_for_table["timestamps"].append(TimeVariable(name=x)),time_variables))
        
        valid_num_columns = [col for col in self.numeric_variables if col in self.df.columns]
        valid_str_columns = [col for col in self.string_variables if col in self.df.columns]

        for i in valid_str_columns:
            features_for_table["strings"].append(StringVariable(name = i ))
        for i in valid_num_columns:
            features_for_table["numeric"].append(ContinuousVariable(name = i))
        
        features_for_table["categorical"] = self.make_cat_variables()
        
        # for i in time_variables:
        #     features_for_table["timestamps"].append(TimeVariable(name = str(i)))
        print(len(features_for_table["numeric"] + features_for_table["categorical"]))      
        domain = Domain(features_for_table["numeric"]+ features_for_table["categorical"] , metas = features_for_table["strings"])
        return domain


    def extract_MedicationRequest(self, path=None,res_from_request=None):
        # if self.local_resource_path is not None:
        #     path = self.local_resource_path
        
        if path is not None:
            with open(path,"r") as f:
                bundle_data = json.load(f)
                f.close()   
        else:
            bundle_data = res_from_request
        try:
            patient_resources  = bundle_data["entry"]
            idx_med_req = map(lambda resource: resource["resource"]["resourceType"] == "MedicationRequest", patient_resources) 
            list_med_request = [element for element, ismedicationreq in zip(patient_resources, idx_med_req) if ismedicationreq]
            # print(f"processing a total of {len(list_med_request)} medication requests found in the file")
        except KeyError:
            ## in questo caso si sta usando solo una risorsa medication request e non un bundle
            # list_med_request = list([bundle_data])
            self.addPrefix = True
            list_med_request = [element for element in [bundle_data]]
        print("THIS :", list_med_request)

        return list_med_request
    
    
        
    def create_table(self):
        domain = self.make_domain()
        ordered_domain = []
        for i in range(len(domain.attributes)):
            ordered_domain.append(domain.attributes[i].name)
        for i in range(len(domain.metas)):
                
            ordered_domain.append(domain.metas[i].name)
        data_list = [list(map(str,row)) for row in self.df[ordered_domain].to_numpy()]
        self.Outputs.processed_table.send(Table(domain, data_list))

    @Inputs.list_of_paths
    def set_input(self, value): 
        print("recived this value in set input: ",value)
        self.input_value = value
        if self.input_value is not None :
            # print("recived this output from prev. widget : ", self.input_value)
            for path in self.input_value:
                # print("sending this path", path)
                medication_requests = self.extract_MedicationRequest(path)
                processed_resources = list(map(self.flatten_dict, medication_requests))
                [self.all_res.append(resource) for resource in processed_resources]
            self.create_table()

        
if __name__ == "__main__":
    widgetpreview.WidgetPreview(OWFhirAnalyzieMedicationRequest).run()


