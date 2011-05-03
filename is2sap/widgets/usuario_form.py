"""Usuario Form"""

from tw.forms import TableForm, Spacer, TextField
from tw.forms.validators import NotEmpty


class UsuarioForm(TableForm):

    hover_help = True
    show_errors = True

    fields = [
        TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca su nombre completo.'),
        Spacer(),
        TextField('apellido', validator=NotEmpty, label_text='Apellido',
            help_text='Introduzca su apellido completo.'),
        Spacer(),
        TextField('nombre_usuario', validator=NotEmpty, label_text='Nombre de usuario',
            help_text='Introduzca un nombre de usuario para el login.'),
        Spacer(),
        TextField('password', validator=NotEmpty, label_text='Password',
            help_text='Introduzca su password.'),
        Spacer(),
        TextField('direccion', label_text='Direccion',
            help_text='Introduzca su direccion de domicilio.'),
        Spacer(),
        TextField('telefono', label_text='Telefono',
            help_text='Introduzca un numero de telefono.'),
        Spacer(),
        TextField('email', label_text='E-mail',
            help_text='Introduzca un nombre de e-mail.'),
        Spacer()]

    submit_text = 'Guardar Usuario'
    
crear_usuario_form = UsuarioForm("Instancia_de_UsuarioForm",action='crear_usuario')
