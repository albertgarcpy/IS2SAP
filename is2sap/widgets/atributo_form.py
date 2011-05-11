"""Atributo Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField
from tw.forms.fields import Button, SubmitButton, HiddenField
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *


class AtributoForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id', label_text='Id',
            help_text='Id del atributo'),
        TextField('tipo_de_item', validator=NotEmpty, label_text='Tipo de Item',
            help_text='Introduzca el tipo de item asociado al atributo'),
        Spacer(),
        TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca el nombre del atributo'),
        Spacer(),
        TextField('descripcion', label_text='Descripción'),
        Spacer(),
        TextField('tipo', label_text='Tipo',
            help_text='Introduzca el tipo del atributo'),
        Spacer()]

    submit_text = 'Guardar Atributo'

class EditAtributoForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id', label_text='Id',
            help_text='Id del atributo'),
        TextField('tipo_de_item', validator=NotEmpty, label_text='Tipo de Item',
            help_text='Introduzca el tipo de item asociado al atributo'),
        Spacer(),
        TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca el nombre del atributo'),
        Spacer(),
        TextField('descripcion', label_text='Descripción'),
        Spacer(),
        TextField('tipo', validator=NotEmpty, label_text='Tipo',
            help_text='Introduzca el tipo del atributo'),
        Spacer()]

    submit_text = 'Guardar Atributo'
    
crear_atributo_form = AtributoForm("CrearAtributo",action='add')
editar_atributo_form = EditAtributoForm("EditarAtributo", action='update')
