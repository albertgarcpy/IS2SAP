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
        HiddenField('id_estado_fase', validator=NotEmpty, label_text='Estado',
            help_text='Identificador del estado de la fase.'),
        HiddenField('id_proyecto', validator=NotEmpty, label_text='Proyecto',
            help_text='Identificador del Proyecto al que pertenece la fase'),
        TextField('numero_fase', size=3, label_text='Numero de Fase',
            help_text='Numero de fase asignado por el sistema.'),
        Spacer(),
        TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca un nombre para la fase.'),        
        Spacer(),
        TextArea('descripcion', label_text='Descripcion',
            help_text='Introduzca una descripcion de la fase')]

    submit_text = 'Guardar Fase'

class EditFaseForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_fase', label_text='Id',
            help_text='Identificador de la Fase'),
        HiddenField('id_estado_fase', validator=NotEmpty, label_text='Estado',
            help_text='Identificador del estado de la fase.'),
        HiddenField('id_proyecto', validator=NotEmpty, label_text='Proyecto',
            help_text='Identificador del Proyecto al que pertenece la fase'),
        TextField('numero_fase', size=3, label_text='Numero de Fase',
            help_text='Numero de fase asignado por el sistema.'),
        Spacer(),
        TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca un nombre para la fase.'),        
        Spacer(),
        TextArea('descripcion', label_text='Descripcion',
            help_text='Introduzca una descripcion de la fase')]

    submit_text = 'Guardar Fase'
    
crear_fase_form = FaseForm("CrearFase", action='add')
editar_fase_form = EditFaseForm("EditarFase", action='update')
