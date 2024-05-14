import sys
import numpy as np
import pandas as pd
import tkinter as tk
from Orange.data.pandas_compat import table_from_frame
from Orange.data import Domain, StringVariable, DiscreteVariable, ContinuousVariable, Table, Values, Tuple
from Orange.widgets import widget, gui, settings
from Orange.widgets.utils.signals import Input, Output
import tkinter as tk
from tkinter import filedialog
import json
from Orange.widgets.utils import widgetpreview
import re 
import requests


class OWFhirTestInput(widget.OWWidget):
    name = "OWFhir Encounter"
    description = "returns processed orange table for medication request FHIR resource"
    category = "Demo"
    
    class Inputs:
        list_of_paths = widget.Input("Bundle Resource Paths", list)

    class Outputs:
        processed_table = widget.Output("Processed Resource Table", Table)


    def __init__(self):
        super().__init__()
        
       
        self.supporto={} #dizionario per recuperare le colonne
        self.string_values=[]
        self.res=[] #lista delle risorse trovate
        self.norm=[]#lista dei dizionari normalizzati
        self.data=[]
        self.del_colonne=["meta_profile","identifier_system","class_system","type_coding_system","participant_type_coding_system","participant_individual_reference","reasonCode_coding_system","location_location_reference","serviceProvider_reference",
                          "meta_profile_0","identifier_0_system","class_0_system","type_0_coding_0_system","participant_0_type_0_coding_0_system","participant_0_individual_0_reference","reasonCode_0_coding_0_system","location_0_location_reference","serviceProvider_0_reference"]
        
        self.addPrefix = False 
        box = gui.widgetBox(self.controlArea,"")
        box.setFixedHeight(100)
        # self.set_input(self.Inputs.list_of_paths)
        self.test_input = "" ## inital default value for input
        self.local_resource_path = ""
        self.input_line = gui.lineEdit(widget=box, master=self,value="test_input", label="Input a fhir server endpoit to retrieve data for a patient ",validator=None)
        gui.button(box, master = self, label = "send", callback=self.validate_api)

        gui.separator(self)
        box2  = gui.widgetBox(self.controlArea,"")
        box2.setFixedHeight(50)
        self.display_message = gui.widgetLabel(box2," ")        
        self.upload_button = gui.button(box2, self, label="Import one or more medication request resource", callback=self.selectEncounter)
        
        # gui.button(box, master = self, label = "send", callback=self.extract_MedicationRequest)

        gui.separator(self)      


    def selectEncounter(self):
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
        #response = requests.get("https://spark.incendi.no/fhir/Encounter/")
        json_results = response.json()
        for i in range(0,len(json_results["entry"])): #len(bundle_data["entry"])
                y=json_results["entry"][i]["resource"]
                [self.res.append(y) for x in y.values() if x=="Encounter"]
                #for x in y.values():
                #    if x=="Encounter":
                #        self.res.append(y)
        self.normalizzo()
        self.create_table()



    def process_item(self, x ,key='',sep='_'):
        
        items = []
        for k, v in x.items():
            new_key = key + sep + k if key else k

            if isinstance(v, dict):
                items.extend(self.process_item(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, val in enumerate(v):
                    if isinstance(val, dict):
                        items.extend(self.process_item(val, f"{new_key}_{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}_{i}", val))
                
            else:
                items.append((new_key, v))
                
        return dict(items)
    
    
    
    
    def normalizzo(self):
        
        self.norm=list(map(self.process_item,self.res))
        
        app=0
        #cancello colonne inutili e trovo il dizionario di riferimento per costruire la tabella
        for j in self.norm:
            #keys=list(j.keys())
            keys=set(j.keys())  #vista da slide lez02
            for y in keys:
                if y in self.del_colonne:
                    del j[y]
        
            if len(j)>app:
                self.supporto=j
                app=len(j)
        #print(self.supporto)
            



    def create_table(self):
        
        string_features = []
        cont_features   = []

        for field in self.supporto.items():
            column = field[0]
            value = field[1]
            if isinstance(value,str):
                string_features.append(StringVariable(column)) 
            else:
                if isinstance(value,int):
                    cont_features.append(ContinuousVariable(column))
                else:
                    continue


        #data=[]
        for j in self.norm:
            l=list(j.values())
            self.data.append(l)
        
        #print(data)
        
        domain = Domain([],metas = string_features)
        output_table = Table.from_list(domain,self.data)
        # output_table = Table(domain, self.data_values)
        self.Outputs.processed_table.send(output_table)
        
    def extract_resource(self, path):
        with open(path,"r") as f:
            bundle_data = json.load(f)
            for i in range(0,len(bundle_data["entry"])): #len(bundle_data["entry"])
                y=bundle_data["entry"][i]["resource"]
                [self.res.append(y) for x in y.values() if x=="Encounter"]
                #for x in y.values():
                #    if x=="Encounter":
                #        self.res.append(y)
                        #print(self.res)
            f.close()
        self.normalizzo()
        self.create_table()
        
    
    @Inputs.list_of_paths
    def set_input(self, value):
         
        self.input_value = value
        if self.input_value is not None :
            print("recived this output from prev. widget : ", self.input_value)
            for path in self.input_value:
                self.extract_resource(path)
                

        
#if __name__ == "__main__":
#   widgetpreview.WidgetPreview(OWFhirTestInput).run()
    
    


