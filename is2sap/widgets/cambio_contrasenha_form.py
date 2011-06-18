"""Usuario Form"""

from tw.forms import TableForm, Spacer, TextField, PasswordField
from tw.forms.fields import Button, SubmitButton, HiddenField
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *

class EditContrasenhaForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        Spacer(),
        PasswordField('password_anterior_form', validator=NotEmpty, label_text='Password Anterior',
            help_text='Introduzca su password.'),
        Spacer(),
        PasswordField('password_nuevo', validator=NotEmpty, label_text='Password Nuevo',
            help_text='Introduzca su password.'),
        Spacer(),
        PasswordField('password_nuevo_repeticion', validator=NotEmpty, label_text='Repetir Password Nuevo',
            help_text='Introduzca su password.'),
        Spacer()]

    submit_text = 'Guardar Password'
    
editar_contrasenha_form = EditContrasenhaForm("EditarContrasenha", action='update')
