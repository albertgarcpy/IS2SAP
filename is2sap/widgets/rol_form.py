"""Rol Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField, CalendarDatePicker, TextArea
from tw.forms.fields import Button, SubmitButton, HiddenField, CheckBox
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *


class RolForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_rol', label_text='Id',
            help_text='Id del Rol'),
        TextField('nombre_rol', validator=NotEmpty_PlainText, label_text='Nombre', size=30,
            help_text='Introduzca el nombre del Rol.'),
        Spacer(),
        TextArea('descripcion', label_text='Descripcion', attrs=dict(rows=3, cols=49),
            help_text='Introduzca una descripcion del Rol'),
        Spacer()]

    submit_text = 'Guardar Rol'

class EditRolForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_rol', label_text='Id',
            help_text='Id del Rol'),
        TextField('nombre_rol', validator=NotEmpty_PlainText, label_text='Nombre', size=30,
            help_text='Introduzca el nombre del Rol.'),
        Spacer(),
        TextArea('descripcion', label_text='Descripcion', attrs=dict(rows=3, cols=49),
            help_text='Introduzca una descripcion del Rol'),
        Spacer()]

    submit_text = 'Guardar Rol'
    
crear_rol_form = RolForm("CrearRol", action='add')
editar_rol_form = EditRolForm("EditarRol", action='update')
