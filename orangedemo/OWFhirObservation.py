from Orange.data import Domain, StringVariable, DiscreteVariable, ContinuousVariable, Table
from Orange.widgets import widget, gui
import json
from Orange.widgets.utils import widgetpreview
import re 
import requests
import pandas as pd 

class OWFhirObservation(widget.OWWidget):
    name = "OWFhir Observation"
    description = "test input Observation"
    category = "Demo"
    
    class Inputs:
        list_of_paths = widget.Input("Bundle Resource Paths", list, auto_summary=False)

    class Outputs:
        processed_table = widget.Output("Processed Observation Table", Table)


    def __init__(self):
        super().__init__()
        
        #list of variables to extract from the json
        self.string_variables = ["resource_id", "resource_subject_reference","resource_encounter_reference", "resource_effectiveDateTime"]
        self.cat_variables = ["resource_category_0_coding_0_code", "resource_code_coding_0_code", "resource_code_text",
                              "resource_component_0_code_text", "resource_component_0_valueQuantity_code",
                              "resource_component_1_code_text", "resource_component_1_valueQuantity_code",
                              "resource_valueCodeableConcept_text", "resource_valueQuantity_unit"]
        self.numeric_variables = ["resource_valueQuantity_value", "resource_component_0_valueQuantity_value", "resource_component_1_valueQuantity_value"]
        
        self.all_res = [] # list of all the resources extracted from the request
        self.all_keys = [] # list of all the keys extracted from the resources
        self.addPrefix = False # flag to add prefix to the column names

        box = gui.widgetBox(self.controlArea,"") 
        box.setFixedHeight(100) 
        self.test_input = "" # inital default value for input
        self.input_line = gui.lineEdit(widget=box, master=self,value="test_input", # field to input the api
                                       label="Input a fhir server endpoit to retrieve data for a patient ",validator=None) 
        gui.button(box, master = self, label = "send", callback=self.validate_api) # button to send the request
        self.display_message = gui.widgetLabel(box," ") # label to display error messages


    # function to validate the input
    def validate_api(self):
        api_pattern = r'^https?://(?:\w+\.)?\w+\.\w+(?:/\S*)?$' # regex to validate the input
        if re.match(api_pattern, self.test_input): 
            self.make_request()
        else:
            print("input a valid fhir api")
            self.display_message.setText("ERROR: Input a valid FHIR API") 

    # function to make the request to the api 
    def make_request(self):
        try:
            response = requests.get(self.test_input) 
        except:
            print("error while making request")
            self.display_message.setText("error while making request")
            return
        #"https://hapi.fhir.org/baseR4/Observation/" 
        json_results = response.json()
        
        observation_requests = self.extract_ObservationRequest(res_from_request=json_results) # extract the observation requests from the json
        processed_resources = list(map(self.flatten_dict, observation_requests)) # flatten the jsons 
        [self.all_res.append(resource) for resource in processed_resources] # append the resources to the list of all resources 
        self.create_table() # create the table

    # function to flatten the jsons 
    def flatten_dict(self,d, key ='', sep='_'): # key is the key of the json, sep is the separator to use in the column names, d is the json to flatten 
        
        items = [] # list of items to append to the final dict
        for k, v in d.items():
            new_key = key + sep + k if key else k # create the new key to append to the dict
            if new_key not in self.all_keys:
                self.all_keys.append(new_key)
            if isinstance(v, dict): # if the value is a dict, call the function recursively
                items.extend(self.flatten_dict(v, new_key, sep=sep).items()) 
            elif isinstance(v, list): # if the value is a list, iterate over the list and call the function recursively
                for i, val in enumerate(v): # i is the index of the element in the list, val is the element, v is the list
                    if isinstance(val, dict):
                        items.extend(self.flatten_dict(val, f"{new_key}_{i}", sep=sep).items()) # call the function recursively
                    else:
                        items.append((f"{new_key}_{i}", val))
                
            else:
                items.append((new_key, v))
        
        return dict(items)

    # function to create the domain for categorical variables
    def make_cat_variables(self):
        processed_cat_variables = [] # list of categorical variables to append to the domain
        valid_columns = [col for col in self.cat_variables if col in self.df.columns] # list of valid columns to extract from the df

        for column in valid_columns:
            cat_values = list(pd.unique(self.df[column])) # list of unique values in the column
            processed_cat_variables.append(DiscreteVariable(name=str(column), values=list(map(str, cat_values)))) 

        return processed_cat_variables
    
    # function to create the domain for the table
    def make_domain(self):
        self.df = pd.DataFrame(self.all_res) # create the df from the list of resources
        if self.addPrefix: 
            self.df = self.df.add_prefix("resource_") # add the prefix to the column names if needed
            
        valid_num_columns = [col for col in self.numeric_variables if col in self.df.columns] # list of valid numeric columns to extract from the df
        valid_str_columns = [col for col in self.string_variables if col in self.df.columns] # list of valid string columns to extract from the df
        
        # dict of features to append to the domain
        features_for_table = { 
        "strings": [StringVariable(name=i) for i in valid_str_columns],
        "numeric": [ContinuousVariable(name=i) for i in valid_num_columns],
        "categorical": self.make_cat_variables(),
        }

        domain = Domain(features_for_table["numeric"] + features_for_table["categorical"], metas=features_for_table["strings"]) 
        return domain

    # function to extract the observation requests from the json
    # path is the path of the file to extract the json from, res_from_request is the json to extract the observation requests from
    def extract_ObservationRequest(self, path=None,res_from_request=None): 
        if path is not None:
            with open(path,"r") as f:
                bundle_data = json.load(f)
                f.close()   
        else:
            bundle_data = res_from_request 
        try:
            patient_resources  = bundle_data["entry"] 
            obs_req = map(lambda resource: resource["resource"]["resourceType"] == "Observation", patient_resources) # map to check if the resource is an observation request
            list_obs_request = [element for element, obs in zip(patient_resources, obs_req) if obs] 
            
            
        # if the json is not a bundle, add the prefix to the column names    
        except KeyError:
            self.addPrefix = True 
            list_obs_request = [element for element in [bundle_data]] 
 
        return list_obs_request
    
    # function to remove the prefix
    def remove_uuid_prefix(self, value):
        if "urn:uuid:" in str(value):
            return str(value).replace("urn:uuid:", "") # remove the prefix from the value if present 
        else:
            return str(value)

    # function to modify the table values
    def modify_table_values(self, table):
        for row in table:
            for column_name in ['resource_subject_reference', 'resource_encounter_reference']:
                if column_name in table.domain:
                    row[column_name] = self.remove_uuid_prefix(row[column_name]) # remove the prefix from the column name if present
        return table

    # function to create the table and send it to the output 
    def create_table(self):
        domain = self.make_domain() # create the domain for the table, using the function make_domain 
        ordered_domain = [attr.name for attr in domain.attributes] + [meta.name for meta in domain.metas] # list of ordered column names to extract from the df
        self.data_list = [list(map(str, row)) for row in self.df[ordered_domain].to_numpy()] # list of lists to append to the table
        
        
        if len(self.data_list) > 20: # if the number of rows is greater than 20 (length of API), remove the rows with the LOINC code 93025-5
            self.data_list = list(filter(lambda x: x[4] != "93025-5", self.data_list)) 
            
        orange_table = Table.from_list(domain, self.data_list) # create the table from the list of lists
        modified_table = self.modify_table_values(orange_table) # modify the table values, using the function modify_table_values
        
        modified_table = self.modify_column_names(modified_table) # modify the column names, using the function modify_column_names

        self.Outputs.processed_table.send(modified_table) # send the table to the output 
        
    # function to modify the column names
    def modify_column_names(self, table):
        column_name_mapping = {
            "resource_id": "Resource ID",
            "resource_subject_reference": "Patient ID",
            "resource_encounter_reference": "Encounter ID",
            "resource_effectiveDateTime": "Date",
            "resource_category_0_coding_0_code": "Category",
            "resource_code_coding_0_code": "LOINC Code",
            "resource_code_text": "LOINC Description",
            "resource_valueQuantity_value": "Value",
            "resource_valueQuantity_unit": "Unit of Measure",
            "resource_component_0_code_text": "Component 1 LOINC Description",
            "resource_component_0_valueQuantity_value": "Component 1 Value",
            "resource_component_0_valueQuantity_code": "Component 1 Unit of Measure",
            "resource_component_1_code_text": "Component 2 LOINC Description",
            "resource_component_1_valueQuantity_value": "Component 2 Value",
            "resource_component_1_valueQuantity_code": "Component 2 Unit of Measure",
            "resource_valueCodeableConcept_text": "Status Survey"
        }

        
        new_attributes = []
        for col in table.domain.attributes:
            if col.name in column_name_mapping:
                if isinstance(col, ContinuousVariable):
                    new_attributes.append(ContinuousVariable(name=column_name_mapping[col.name]))
                elif isinstance(col, DiscreteVariable):
                    new_attributes.append(DiscreteVariable(name=column_name_mapping[col.name], values=col.values)) 
                
            else:
                new_attributes.append(col)

        new_metas = []
        for col in table.domain.metas:
            if col.name in column_name_mapping:
                new_metas.append(StringVariable(name=column_name_mapping[col.name]))
            else:
                new_metas.append(col)

        new_domain = Domain(attributes=new_attributes, metas=new_metas)
        table.domain = new_domain

        return table


    @Inputs.list_of_paths # decorator to set the input
    def set_input(self, value): # value is the list of paths to extract the jsons from
        self.input_value = value 
        if self.input_value is not None :
            self.all_res = [] # Clear previous data to avoid overlapping
            for path in self.input_value: 
                observation_requests = self.extract_ObservationRequest(path) # extract the observation requests from the json
                processed_resources = list(map(self.flatten_dict, observation_requests)) # flatten the jsons
                [self.all_res.append(resource) for resource in processed_resources] # append the resources to the list of all resources
                
            self.create_table()

if __name__ == "__main__":
    widgetpreview.WidgetPreview(OWFhirObservation).run()


