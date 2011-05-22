"""Linea Base Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField
from tw.forms.fields import Button, SubmitButton, HiddenField
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *


class LineaBaseForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_linea_base', label_text='Id',
            help_text='Id del usuario'),
        TextField('descripcion', validator=NotEmpty, label_text='Descripcion',
            help_text='Introduzca su descripcion'),
        Spacer(),
        TextField('estado', default='DESARROLLO', label_text='Estado', disabled=True,
            help_text='Introduzca su estado'),
        Spacer(),
        TextField('id_fase', validator=UniqueUsername, label_text='Fase',
            help_text='Introduzca una fase'),
        Spacer(),
        TextField('version', default='1.0', disabled=True, label_text='Version',
            help_text='Introduzca la version'),
        Spacer()]
    submit_text = 'Guardar Linea Base'

class EditLineaBaseForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_linea_base', label_text='Id',
            help_text='Id del usuario'),
        TextField('descripcion', validator=NotEmpty, label_text='Descripcion',
            help_text='Introduzca su descripcion'),
        Spacer(),
        TextField('estado', validator=NotEmpty, label_text='Estado',
            help_text='Introduzca su estado'),
        Spacer(),
        TextField('id_fase', validator=UniqueUsername, label_text='Fase',
            help_text='Introduzca una fase'),
        Spacer(),
        TextField('version', validator=PlainText, label_text='Version',
            help_text='Introduzca la version'),
        Spacer()]

    submit_text = 'Guardar Linea Base'
    
crear_linea_base_form = LineaBaseForm("CrearLineaBase",action='add')
editar_linea_base_form = EditLineaBaseForm("EditarLineaBase", action='update')
