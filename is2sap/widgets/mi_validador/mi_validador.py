from formencode import *
from is2sap.model import *
from is2sap.model import DBSession, metadata, Usuario
from tw.forms.validators import *

_ = lambda s: s

class UniqueUsername(FancyValidator):

   not_empty = True

   def validate_python(self, value, state):
      usuarios = DBSession.query(Usuario)
      for usuario in usuarios:
         if value == usuario.nombre_usuario:
             raise Invalid(
                 'El nombre de usuario ya existe.',
                 value, state)

class NotEmpty_PlainText(Regex):

    regex = r"^[a-zA-Z_\-0-9\s]*$"

    messages = {
        'invalid': _('Introduzca solo "letras", o "numeros", o "_", o "-")'),
        'empty': _("Rellene el campo"),
        }

    not_empty = True

    def validate_python(self, value, state):
        self.assert_string(value, state)
        if self.strip and isinstance(value, basestring):
            value = value.strip()
        if not self.regex.search(value):
            raise Invalid(self.message('invalid', state),
                          value, state)
        if value == 0:
            # This isn't "empty" for this definition.
            return value
        if not value:
            raise Invalid(self.message('empty', state),
                          value, state)


class NotEmpty_Text(Regex):

    regex = r"^[a-zA-Z\s]*$"

    messages = {
        'invalid': _('Introducir solo letras'),
        'empty': _("Rellene el campo"),
        }

    not_empty = True

    def validate_python(self, value, state):
        self.assert_string(value, state)
        if self.strip and isinstance(value, basestring):
            value = value.strip()
        if not self.regex.search(value):
            raise Invalid(self.message('invalid', state),
                          value, state)
        if value == 0:
            # This isn't "empty" for this definition.
            return value
        if not value:
            raise Invalid(self.message('empty', state),
                          value, state)


class MiPlainText(Regex):

    regex = r"^[a-zA-Z_/\-0-9\s]*$"

    messages = {
        'invalid': _('Introduzca solo "letras", o "numeros", o "_", o "/", o "-")'),
        }


    def validate_python(self, value, state):
        self.assert_string(value, state)
        if self.strip and isinstance(value, basestring):
            value = value.strip()
        if not self.regex.search(value):
            raise Invalid(self.message('invalid', state),
                          value, state)


class NumerosTelefono(Regex):

    regex = r"^[-\0-9]*$"

    messages = {
        'invalid': _('Introduzca solo "numeros", o "-")'),
        }


    def validate_python(self, value, state):
        self.assert_string(value, state)
        if self.strip and isinstance(value, basestring):
            value = value.strip()
        if not self.regex.search(value):
            raise Invalid(self.message('invalid', state),
                          value, state)



