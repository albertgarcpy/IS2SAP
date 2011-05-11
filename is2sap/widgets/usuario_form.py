"""Usuario Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField
from tw.forms.fields import Button, SubmitButton, HiddenField
#from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *
#from formencode import *


class UsuarioForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_usuario', label_text='Id',
            help_text='Id del usuario'),
        TextField('nombre', validator=NotEmpty_Text, label_text='Nombre',
            help_text='Introduzca su nombre completo.'),
        Spacer(),
        TextField('apellido', validator=NotEmpty_Text, label_text='Apellido',
            help_text='Introduzca su apellido completo.'),
        Spacer(),
        TextField('nombre_usuario', validator=UniqueUsername, label_text='Nombre de usuario',
            help_text='Introduzca un nombre de usuario para el login.'),
        Spacer(),
        PasswordField('password', validator=NotEmpty, label_text='Password',
            help_text='Introduzca su password.'),
        Spacer(),
        TextField('direccion', validator=MiPlainText, label_text='Direccion',
            help_text='Introduzca su direccion de domicilio.'),
        Spacer(),
        TextField('telefono', validator=NumerosTelefono, label_text='Telefono',
            help_text='Introduzca un numero de telefono.'),
        Spacer(),
        TextField('email', validator=Email, label_text='E-mail',
            help_text='Introduzca un nombre de e-mail.'),
        Spacer()]

    submit_text = 'Guardar Usuario'

class EditUsuarioForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        HiddenField('id_usuario', label_text='Id',
            help_text='Id del usuario'),
        TextField('nombre', validator=NotEmpty_Text, label_text='Nombre',
            help_text='Introduzca su nombre completo.'),
        Spacer(),
        TextField('apellido', validator=NotEmpty_Text, label_text='Apellido',
            help_text='Introduzca su apellido completo.'),
        Spacer(),
        TextField('nombre_usuario', validator=NotEmpty_PlainText, label_text='Nombre de usuario',
            help_text='Introduzca un nombre de usuario para el login.'),
        Spacer(),
        #PasswordField('password', validator=NotEmpty_PlainText, label_text='Password',
        #    help_text='Introduzca su password.'),
        TextField('direccion', validator=MiPlainText, label_text='Direccion',
            help_text='Introduzca su direccion de domicilio.'),
        Spacer(),
        TextField('telefono', validator=NumerosTelefono, label_text='Telefono',
            help_text='Introduzca un numero de telefono.'),
        Spacer(),
        TextField('email', validator=Email, label_text='E-mail',
            help_text='Introduzca un nombre de e-mail.'),
        Spacer()]

    submit_text = 'Guardar Usuario'
    
crear_usuario_form = UsuarioForm("CrearUsuario",action='add')
editar_usuario_form = EditUsuarioForm("EditarUsuario", action='update')
