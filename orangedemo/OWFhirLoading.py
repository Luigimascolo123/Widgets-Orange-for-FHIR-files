import tkinter as tk
from tkinter import filedialog
from Orange.widgets import widget, gui

class OWFhirLoading(widget.OWWidget):
    """
    Questo Widget Orange permette di selezionare uno o più file JSON, che contengono risorse FHIR, e di trasformarli 
    in una lista di percorsi che sarà inviata come output del widget
    """

    name = "OWFhir Loading"
    description = "Upload FHIR resources and transform them in a Python List."
    category = "Demo"

    class Outputs:
        final_files_paths = widget.Output("Processed Data", list)

    def __init__(self):
        super().__init__()

        #Casella di controllo del widget
        box = gui.widgetBox(self.controlArea, "File Selection", orientation='horizontal')
        gui.label(box, self, "")
        
        #Pulsante del widget per selezionare i file JSON
        self.button = gui.button(box, self, "Import one or more JSON files",callback=self.upload_action, width=200, height=50)
        gui.label(box, self, "")
        self.info_label = gui.widgetLabel(box, ".")

        #Inizializzazione della lista dei percorsi dei file
        self.file_paths = []

    def upload_action(self):
        """
        Callback chiamato quando l'utente preme il pulsante per selezionare i file.
        Apre una finestra di dialogo per la selezione dei file JSON FHIR e memorizza i percorsi selezionati.
        """

        root = tk.Tk()
        root.withdraw()
        
        #Apertura della finestra di dialogo per la selezione dei file
        file_paths = filedialog.askopenfilenames(title="Select JSON FHIR resources",
                                                 filetypes=(("JSON Files", "*.json"),))

        #una volta selezionati i file chiama la funzione di commit sulla lista 
        if file_paths:
            print("File paths list: ", file_paths)
            self.file_paths = list(file_paths)
            self.commit()
        else:
            print("Selected 0 files")

    def commit(self):
        """
        Invia l'output contenente la lista dei percorsi dei file selezionati.
        """
        self.Outputs.final_files_paths.send(self.file_paths)