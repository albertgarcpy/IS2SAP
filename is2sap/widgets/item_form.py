"""Item Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField, CalendarDatePicker
from tw.forms.fields import Button, SubmitButton, HiddenField, CheckBox
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *

from is2sap.model import DBSession, metadata
from is2sap.model.model import Atributo


class ItemForm(TableForm):
   
    hover_help = True
    show_errors = True
    submit_text = 'Guardar Item'
        

class EditItemForm(TableForm):

    hover_help = True
    show_errors = True
    nuevoatributo = DBSession.query(Atributo).filter_by(id_tipo_item='1')

    fields = [
        HiddenField('id_item', label_text='Id',
            help_text='Id del item'),
        TextField('id_tipo_item', validator=NotEmpty, label_text='Tipo de Item',
            help_text='Introduzca el tipo de item'),
        Spacer(),
        TextField('id_linea_base', validator=NotEmpty, label_text='Linea Base',
            help_text='Introduzca la linea Base'),
        Spacer(),
        TextField('numero', validator=NotEmpty, label_text='Numero',
            help_text='Introduzca un numero para el item'),
        Spacer(),
        TextField('descripcion', validator=PlainText, label_text='Descripcion',
            help_text='Introduzca una descripcion'),
        Spacer(),
        TextField('complejidad', validator=PlainText, label_text='Complejidad',
            help_text='Introduzca su direccion de domicilio.'),
        Spacer(),
        TextField('prioridad', validator=PlainText, label_text='Prioridad',
            help_text='Introduzca la prioridad'),
        Spacer(),
        TextField('estado', validator=PlainText, label_text='Estado',
            help_text='Introduzca un estado valido'),
        Spacer(),
	TextField('archivo_externo', validator=PlainText, label_text='Archivo Externo',
            help_text='Introduzca un archivo externo'),
        Spacer(),
	TextField('version', validator=PlainText, label_text='Version',
            help_text='Introduzca una version'),
        Spacer(),
	TextField('observacion', validator=PlainText, label_text='Observacion',
            help_text='Introduzca una observacion'),
        Spacer(),
	CalendarDatePicker('fecha_modificacion',label_text='Fecha de Modificacion',
            help_text='Introduzca una fecha de modificacion'),
        Spacer(),
        CheckBox('vivo', disabled='False', label_text='Vivo', default='True',
            help_text='Indica si esta vivo'),
        Spacer()]

    submit_text = 'Guardar Item'
    

editar_item_form = EditItemForm("EditarItem", action='update')
