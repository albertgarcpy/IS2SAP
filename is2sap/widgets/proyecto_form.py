"""Usuario Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField, CalendarDatePicker
from tw.forms.fields import Button, SubmitButton, HiddenField, CheckBox
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *


class ProyectoForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_proyecto', label_text='Id',
            help_text='Id del Proyecto'),
        TextField('id_usuario', label_text='id_usuario',
            help_text='Id del Usuario.'),
        Spacer(),
        TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca su Nombre completo.'),
        Spacer(),
        TextField('descripcion', label_text='Descripcion',
            help_text='Introduzca una descripcion del Proyecto'),        
        Spacer(),
        CalendarDatePicker('fecha', date_format='%y-%m-%d',
            help_text='Seleccione la fecha de Creacion del Proyecto'),
        Spacer(),
        CheckBox('iniciado', label_text='Iniciado',
            help_text='Indica si el proyecto se ha iniciado')]

    submit_text = 'Guardar Proyecto'

class EditProyectoForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_proyecto', label_text='Id',
            help_text='Id del Proyecto'),
        TextField('id_usuario', label_text='id_usuario',
            help_text='Id del Usuario.'),
        Spacer(),
        TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca su Nombre completo.'),
        Spacer(),
        TextField('descripcion', label_text='Descripcion',
            help_text='Introduzca una descripcion del Proyecto'),        
        Spacer(),
        CalendarDatePicker('fecha', date_format='%y-%m-%d',
            help_text='Seleccione la fecha de Creacion del Proyecto'),
        Spacer(),
        CheckBox('iniciado', label_text='Iniciado',
            help_text='Indica si el proyecto se ha iniciado')]

    submit_text = 'Guardar Proyecto'
    
crear_proyecto_form = ProyectoForm("CrearProyecto", action='add')
editar_proyecto_form = EditProyectoForm("EditarProyecto", action='update')
