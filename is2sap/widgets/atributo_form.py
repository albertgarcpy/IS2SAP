"""Atributo Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField, TextArea, SingleSelectField
from tw.forms.fields import Button, SubmitButton, HiddenField
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *


class AtributoForm(TableForm):

    hover_help = True
    show_errors = True
    genre_options = ['Texto', 'Numerico', 'Fecha']

    fields = [
        HiddenField('id_atributo', label_text='Id',
            help_text='Id del atributo'),
        TextField('id_tipo_item', validator=NotEmpty, label_text='Identificador del Tipo de Item',
            help_text='Introduzca el tipo de item asociado al atributo'),
        Spacer(),
        TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca el nombre del atributo'),
        Spacer(),
        TextArea('descripcion', label_text='Descripcion'),
        Spacer(),
        SingleSelectField('tipo', options=genre_options, label_text='Tipo',
            help_text = 'Seleccione el tipo del atributo.')]

    submit_text = 'Guardar Atributo'

class EditAtributoForm(TableForm):

    hover_help = True
    show_errors = True
    genre_options = ['Texto', 'Numerico', 'Fecha']

    fields = [
        HiddenField('id_atributo', label_text='Id',
            help_text='Id del atributo'),
        TextField('id_tipo_item', validator=NotEmpty, label_text='Identificador del Tipo de Item',
            help_text='Introduzca el tipo de item asociado al atributo'),
        Spacer(),
        TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca el nombre del atributo'),
        Spacer(),
        TextArea('descripcion', label_text='Descripcion'),
        Spacer(),
        SingleSelectField('tipo', options=genre_options, label_text='Tipo',
            help_text = 'Seleccione el tipo del atributo.')]

    submit_text = 'Guardar Atributo'
    
crear_atributo_form = AtributoForm("CrearAtributo", action='add')
editar_atributo_form = EditAtributoForm("EditarAtributo", action='update')
