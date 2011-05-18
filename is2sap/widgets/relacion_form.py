"""Relacion Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField
from tw.forms.fields import Button, SubmitButton, HiddenField
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *


class RelacionForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_relacion', label_text='Id',
            help_text='Id de la relacion'),
        TextField('estado', validator=NotEmpty, label_text='Estado',
            help_text='Introduzca el estado'),
        Spacer(),
        TextField('id_item1', validator=NotEmpty, label_text='Item Origen',
            help_text='Introduzca el item origen'),
        Spacer(),
	TextField('id_item2', validator=NotEmpty, label_text='Item Destino',
            help_text='Introduzca el item destino'),
        Spacer(),
        TextField('tipo', validator=NotEmpty, label_text='Tipo',
            help_text='Introduzca el tipo'),
        Spacer(),
        TextField('version', validator=PlainText, label_text='Version',
            help_text='Introduzca una version'),
        Spacer()]

    submit_text = 'Guardar Relacion'

class EditRelacionForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_relacion', label_text='Id',
            help_text='Id de la relacion'),
        TextField('estado', validator=NotEmpty, label_text='Estado',
            help_text='Introduzca el estado'),
        Spacer(),
        TextField('id_item1', validator=NotEmpty, label_text='Item Origen',
            help_text='Introduzca el item origen'),
        Spacer(),
	TextField('id_item2', validator=NotEmpty, label_text='Item Destino',
            help_text='Introduzca el item destino'),
        Spacer(),
        TextField('tipo', validator=NotEmpty, label_text='Tipo',
            help_text='Introduzca el tipo'),
        Spacer(),
        TextField('version', validator=PlainText, label_text='Version',
            help_text='Introduzca una version'),
        Spacer()]

    submit_text = 'Guardar Relacion'
    
crear_relacion_form = RelacionForm("CrearRelacion",action='add')
editar_relacion_form = EditRelacionForm("EditarRelacion", action='update')
