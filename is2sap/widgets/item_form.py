"""Item Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField, CalendarDatePicker, TextArea, SingleSelectField
from tw.forms.fields import Button, SubmitButton, HiddenField, CheckBox, FileField
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *


class ItemForm(TableForm):
   
    hover_help = True
    show_errors = True
    submit_text = 'Guardar Item'

class EditItemForm(TableForm):

    hover_help = True
    show_errors = True
    submit_text = 'Guardar Item'


