"""Linea Base Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField, TextArea
from tw.forms.fields import Button, SubmitButton, HiddenField
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *


class LineaBaseForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_linea_base', label_text='Id',
            help_text='Id del usuario'),
	TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca el nombre de la linea base'),
        Spacer(),
	TextArea('descripcion', label_text='Descripcion',
            help_text='Introduzca una descripcion de la linea base'),        
        Spacer(),
	HiddenField('id_estado', validator=NotEmpty, label_text='Estado',
            help_text='Identificador del estado de la linea base.'),
	HiddenField('id_fase', validator=NotEmpty, label_text='Fase',
            help_text='Identificador de la fase.'),
	HiddenField('version', validator=NotEmpty, label_text='Version',
            help_text='Version de la linea base')]
    submit_text = 'Guardar Linea Base'

class EditLineaBaseForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
       HiddenField('id_linea_base', label_text='Id',
            help_text='Id del usuario'),
	TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca el nombre de la linea base'),
        Spacer(),
	TextArea('descripcion', label_text='Descripcion',
            help_text='Introduzca una descripcion de la linea base'),        
        Spacer(),
	HiddenField('id_estado', validator=NotEmpty, label_text='Estado',
            help_text='Identificador del estado de la linea base.'),
	HiddenField('id_fase', validator=NotEmpty, label_text='Fase',
            help_text='Identificador de la fase.'),
	HiddenField('version', validator=NotEmpty, label_text='Version',
            help_text='Version de la linea base')]

    submit_text = 'Guardar Linea Base'
    
crear_linea_base_form = LineaBaseForm("CrearLineaBase",action='add')
editar_linea_base_form = EditLineaBaseForm("EditarLineaBase", action='update')
