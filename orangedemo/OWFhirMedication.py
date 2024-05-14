import Orange
from Orange.data import Domain, StringVariable, ContinuousVariable, Table
from Orange.widgets import widget, gui
import json
import re 
import requests
import pandas as pd
import numpy as np
from collections import OrderedDict
from Orange.widgets.utils import widgetpreview


class OWFhirMedication(widget.OWWidget):
    """
    Questo widget permette di creare una Orange Table a partire da un file JSON contenente la risorsa 
    medication, prà farlo partendo da un file in locale oppure andando a trattare un file 
    proveniente da server.
    """

    name = "OWFhir Medication"
    description = "Widget for extract the medications info"
    category = "Demo"


#CLASSI INPUTS E OUTPUTS WIDGET
    class Inputs:
        list_of_paths = widget.Input("Bundle Resource Paths", list)

    class Outputs:
        processed_table = widget.Output("Processed Resource Table", Table)


#GUI WIDGET E INIZIALIZZAZIONE VARIABILI
    def __init__(self):
        super().__init__()
        
        self.result_dict={} #dizionario per estrarre tutte le info annidate nella risorsa
        self.supporto={} #dizionario per recuperare le colonne
        self.data_values = [] #record da inserire nella tabella finale
        self.string_values=[]
        self.res=[] #lista delle risorse trovate
        self.norm=[]#lista dei dizionari normalizzati

        self.input_received = None
        box = gui.widgetBox(self.controlArea,"")
        box.setFixedHeight(100)
        
        ## campo per immettere stringa dell APi da cui fare richiesta
        self.test_input = "" #valore di default per l input
        self.input_line = gui.lineEdit(widget=box, master=self,value="test_input", 
                                       label="Input a fhir server endpoit to retrieve data for a patient"
                                       "(Example:'https://spark.incendi.no/fhir/Medication/med0318)",
                                       validator=None,callback=self.validate_api)
        
        gui.button(box, master = self, label = "send", callback=self.validate_api)
        gui.separator(self)
        box2  = gui.widgetBox(self.controlArea,"")
        self.display_message = gui.widgetLabel(box2," ")        


#ELABORAZIONE DATI DA SERVER
    def validate_api(self):
        #se l'input è una stringa valida che corrisponde alla forma di un endpoint, si passa alla funzione che fa la request
        api_pattern = r'^https?://(?:\w+\.)?\w+\.\w+(?:/\S*)?$'
        if re.match(api_pattern, self.test_input):
            self.make_request()
        else:
            self.display_message.setText("ERROR: Input a valid FHIR API")

    def make_request(self):
        try:
            response = requests.get(self.test_input) #esempio di response--> response= requests.get("https://spark.incendi.no/fhir/Medication/med0318")
        except:
            print("error while making request")
            self.display_message.setText("error while making request")
            return
        json_results = response.json()  #trasformiamo la response in un json e gli applichiamo la funzione flatten_dict
        json_results = self.flatten_dict(json_results)
        all_data=pd.json_normalize(json_results)
        self.dataFrameCleanning = all_data
        self.commit_table() #infine una volta appiattito il json andiamo ad applicarci commit_table per costruire il dominio e mandarlo come output

    def flatten_dict(self, d, key='', sep='_'):
        """
        Appiattisce un dizionario annidato, unendo le chiavi annidate con un separatore.
        :param d: Il dizionario da appiattire.
        :param key: La chiave corrente, utilizzata per costruire la chiave risultante.
        :param sep: Il separatore da utilizzare tra le chiavi annidate.
        :return: Un nuovo dizionario appiattito.
        """
        items = []  
    
        # Itera attraverso le coppie chiave-valore nel dizionario fornito
        for k, v in d.items():
            new_key = key + sep + k if key else k  # Costruisce la nuova chiave concatenando la chiave corrente al prefisso
        
            # Se il valore è un dizionario, chiamata ricorsiva per appiattirlo e aggiungi i suoi elementi alla lista
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            # Se il valore è una lista, itera attraverso i suoi elementi
            elif isinstance(v, list):
                for i, val in enumerate(v):
                    # Se l'elemento della lista è un dizionario, chiamata ricorsiva per appiattirlo
                    if isinstance(val, dict):
                        items.extend(self.flatten_dict(val, f"{new_key}_{i}", sep=sep).items())
                    # Altrimenti, aggiungi l'elemento alla lista con una nuova chiave basata sull'indice
                    else:
                        items.append((f"{new_key}_{i}", val))
            # Se il valore non è né un dizionario né una lista, aggiungi la coppia chiave-valore alla lista
            else:
                items.append((new_key, v))
    
        # Restituisci un nuovo dizionario appiattito
        return dict(items)

    def construct_domain(self, df):
        """
        Costruisce un dominio Orange basato sulle colonne del DataFrame fornito.
        param df: Il DataFrame contenente i dati da utilizzare per costruire il dominio.
        return: Un oggetto di dominio Orange.
        """
        columns = OrderedDict(df.dtypes)    # Ottieni i tipi di dati delle colonne nel DataFrame
        
        def create_variable(col):
            """
            Crea una variabile Orange (Continua o Discreta) in base al tipo di dati della colonna.
            param col: Una coppia chiave-valore rappresentante una colonna e il suo tipo di dati.
            return: Una variabile Orange.
            """
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
            # Se il tipo di dati della colonna non è riconosciuto come float, int, date o object,
            # la trattiamo come variabile discreta con valori unici della colonna
            return Orange.data.DiscreteVariable(col[0], values = df[col[0]].unique().tolist())
        
            # Mappa la funzione create_variable su ogni colonna e ottieni una lista di variabili
        res  = list(map(create_variable, columns.items()))

        # Restituisci un oggetto di dominio Orange basato sulle variabili create
        return Domain([],metas=res)
    
    def commit_table(self):
        domain = self.construct_domain(self.dataFrameCleanning) #costruisce il dominio in base al dataframe con cui lavora 
        #metodo from_list per creare una orange table da una lista
        orange_table = Orange.data.Table.from_list(domain = domain, rows = self.dataFrameCleanning.values.tolist())
        self.Outputs.processed_table.send(orange_table)


#ELABORAZIONE DATI DA LOCALE
    def process_item(self, x=dict(), prefix=""):
        for field in x.items():
            if prefix != "":
                key = prefix + field[0]
            else:
                key = field[0]
            value = field[1]

            # Se il valore è una lista con un solo elemento di tipo stringa, assegna il valore al risultato
            if isinstance(value, list):
                if len(value) == 1 and isinstance(value[0], str):
                    self.result_dict[key] = value[0]
                    continue
                # Se la lista ha più di un elemento o l'elemento non è una stringa, continua con il prossimo campo
                else:
                    continue

            # Se il valore è un dizionario, chiamata ricorsiva per processare il sotto-dizionario
            if isinstance(value, dict):
                self.process_item(value, prefix=f"{key}_")
                continue

            # Assegna il valore corrente al risultato
            self.result_dict[key] = value
    
    def normalizzo(self):
        """
        Normalizza le risorse processate.
        Itera attraverso la lista di risorse, chiama la funzione `process_item` per ciascuna risorsa,
        aggiunge il risultato normalizzato alla lista `self.norm`, e quindi determina la risorsa con il
        numero massimo di colonne in modo da impostare il supporto per l'output.
        """
        for i in self.res:
            self.process_item(i)
            self.norm.append(self.result_dict)
            self.result_dict = {}

        app = 0
        for i in self.norm:
            if len(i) > app:
                self.supporto = i
                app = len(i)

        print(self.supporto, len(self.supporto), app)
    
    def create_table(self):
        # Inizializziamo due liste per le variabili di tipo stringa e continue
        string_features = []
        cont_features = []
        unique_records = set() # Usiamo un set per memorizzare record unici

        # Iteriamo attraverso ogni campo (column) e valore (value) nel dizionario di supporto
        for field in self.supporto.items():
            column = field[0]
            value = field[1]
            # Verifichiamo il tipo di valore e aggiungiamo la variabile corrispondente alla lista appropriata
            if isinstance(value, str):
                string_features.append(StringVariable(column))
            elif isinstance(value, int):
                cont_features.append(ContinuousVariable(column))

        data = []  # Inizializziamo una lista per contenere i dati della tabella

        # Iteriamo attraverso ogni record nella lista normalizzata
        for i in self.norm:
            record_values = tuple(i.values())  # Convertiamo i valori del dizionario in una tupla
            # Controlliamo se il record è già stato aggiunto alla tabella per evitare ripetizioni
            if record_values not in unique_records:
                l = list(record_values)  # Convertiamo la tupla in una lista
                data.append(l)  # Aggiungiamo il record alla lista dei dati della tabella
                unique_records.add(record_values)  # Aggiungiamo il record unico al set

        # Costruiamo un dominio Orange basato sulle variabili di tipo stringa
        domain = Domain([], metas=string_features)
        # Creiamo una tabella Orange utilizzando il dominio e i dati
        output_table = Table.from_list(domain, data)
        # Inviamo la tabella Orange come output
        self.Outputs.processed_table.send(output_table)

    def extract_resource(self, path):
        """
        Estrae le risorse di tipo "Medication" da un file JSON specificato dal percorso.
        param path: Il percorso del file JSON contenente le risorse FHIR.
        """
        # Apre il file JSON specificato dal percorso
        with open(path, "r") as f:
            # Carica i dati del bundle FHIR dal file JSON
            bundle_data = json.load(f)
        
            # Itera attraverso le entry del bundle 
            for entry in bundle_data.get("entry", []):
                resource = entry.get("resource", {})
                # Verifica se la risorsa è di tipo "Medication" e la aggiunge alla lista
                if resource.get("resourceType") == "Medication":
                    self.res.append(resource)

            f.close()

        # Normalizza i dati e crea la tabella Orange
        self.normalizzo()
        self.create_table()

    @Inputs.list_of_paths
    def set_input(self, value): 
        """
        Imposta l'input del widget con la lista di percorsi dei file JSON delle risorse FHIR.
        param value: La lista di percorsi dei file JSON.
        """
        self.input_value = value
    
        # Verifica se l'input è valido e non è vuoto
        if self.input_value is not None and len(self.input_value) > 0:
            print("Received this output from the previous widget:", self.input_value)
            for path in self.input_value:   # Itera attraverso i percorsi dei file JSON e chiama la funzione extract_resource per ciascun percorso
                self.extract_resource(path)
