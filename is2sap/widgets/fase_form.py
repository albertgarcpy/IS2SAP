"""Fase Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField, CalendarDatePicker
from tw.forms.fields import Button, SubmitButton, HiddenField, CheckBox, TextArea
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *


class FaseForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_fase', label_text='Id',
            help_text='Identificador de la Fase'),
        TextField('id_estado_fase', validator=NotEmpty, label_text='Estado',
            help_text='Identificador del estado de la fase.'),
        Spacer(),
        TextField('id_proyecto', validator=NotEmpty, label_text='Proyecto',
            help_text='Identificador del Proyecto al que pertenece la fase'),
        Spacer(),
        TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca un nombre para la fase.'),        
        Spacer(),
        TextArea('descripcion', attrs=dict(rows=3, cols=25), label_text='Descripcion',
            help_text='Introduzca una descripcion de la fase'),        
        Spacer(),
        TextField('numero_fase', label_text='Numero de Fase',
            help_text='Numero de fase asignado por el sistema.')]

    submit_text = 'Guardar Fase'

class EditFaseForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_fase', validator=NotEmpty, label_text='Id',
            help_text='Identificador de la Fase'),
        TextField('id_estado_fase', validator=NotEmpty, label_text='Id Fase',
            help_text='Identificador del estado de la fase.'),
        Spacer(),
        TextField('id_proyecto', validator=NotEmpty, label_text='Proyecto',
            help_text='Identificador del Proyecto al que pertenece la fase'),
        Spacer(),
        TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca un nombre para la fase.'),        
        Spacer(),
        TextArea('descripcion', attrs=dict(rows=3, cols=25), label_text='Descripcion',
            help_text='Introduzca una descripcion de la fase'),        
        Spacer(),
        TextField('numero_fase', label_text='Numero de Fase',
            help_text='Numero de fase asignado por el sistema.')]

    submit_text = 'Guardar Fase'
    
crear_fase_form = FaseForm("CrearFase", action='add')
editar_fase_form = EditFaseForm("EditarFase", action='update')
