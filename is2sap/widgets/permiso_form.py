"""Permiso Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField, CalendarDatePicker, TextArea
from tw.forms.fields import Button, SubmitButton, HiddenField, CheckBox
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *


class PermisoForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_permiso', label_text='Id',
            help_text='Id del Permiso'),
        TextField('nombre_permiso', validator=NotEmpty_PlainText, label_text='Nombre', size=38,
            help_text='Introduzca el nombre del Permiso.'),
        Spacer(),
        TextArea('descripcion', label_text='Descripcion', attrs=dict(rows=10, cols=50),
            help_text='Introduzca una descripcion del Permiso'),
        Spacer()]

    submit_text = 'Guardar Permiso'

class EditPermisoForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_permiso', label_text='Id',
            help_text='Id del Permiso'),
        TextField('nombre_permiso', validator=NotEmpty_PlainText, label_text='Nombre', size=38,
            help_text='Introduzca el nombre del Permiso.'),
        Spacer(),
        TextArea('descripcion', label_text='Descripcion', attrs=dict(rows=10, cols=50),
            help_text='Introduzca una descripcion del Permiso'),
        Spacer()]

    submit_text = 'Guardar Permiso'
    
crear_permiso_form = PermisoForm("CrearPermiso", action='add')
editar_permiso_form = EditPermisoForm("EditarPermiso", action='update')
