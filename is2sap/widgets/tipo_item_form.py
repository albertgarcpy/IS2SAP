"""TipoItem Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField, TextArea
from tw.forms.fields import Button, SubmitButton, HiddenField
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *


class TipoItemForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_tipo_item', label_text='Id',
            help_text='Id del tipo_item'),
        TextField('id_fase', label_text='Fase',
            help_text='Introduzca un id de fase'),
        Spacer(),
        TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca el nombre del tipo de Item correcto'),
        Spacer(),
        TextArea('descripcion', attrs=dict(rows=3, cols=25), label_text='Descripcion'),        
        Spacer()]

    submit_text = 'Guardar'

class EditTipoItemForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_tipo_item', label_text='Id',
            help_text='Id del tipo_item'),
        TextField('id_fase', label_text='Fase',
            help_text='Introduzca un id de fase'),
        Spacer(),
        TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca el nombre del tipo de Item correcto'),
        Spacer(),
        TextArea('descripcion', attrs=dict(rows=3, cols=25), label_text='Descripcion'),        
        Spacer()]

    submit_text = 'Guardar'
    
crear_tipo_item_form = TipoItemForm("Crear_tipo_item",action='add')
editar_tipo_item_form = EditTipoItemForm("Editar_tipo_item", action='update')
