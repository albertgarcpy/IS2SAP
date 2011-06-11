"""Linea Base Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField, TextArea
from tw.forms.fields import Button, SubmitButton, HiddenField
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *


class LineaBaseForm(TableForm):

    hover_help = True
    show_errors = True

    
    submit_text = 'Guardar Linea Base'

class EditLineaBaseForm(TableForm):

    hover_help = True
    show_errors = True

    submit_text = 'Guardar Linea Base'
    


