from formencode import *
from is2sap.model import *
from is2sap.model import DBSession, metadata, Usuario
from tw.forms.validators import *

_ = lambda s: s

class UniqueUsername(FancyValidator):


   def validate_python(self, value, state):
      usuarios = DBSession.query(Usuario)
      for usuario in usuarios:
         if value == usuario.nombre_usuario:
             raise Invalid(
                 'El nombre de usuario ya existe.',
                 value, state)

class NotEmpty_PlainText(Regex):

    """
    Test that the field contains only letters, numbers, underscore,
    and the hyphen.  Subclasses Regex.

    Examples::

        >>> PlainText.to_python('_this9_')
        '_this9_'
        >>> PlainText.from_python('  this  ')
        '  this  '
        >>> PlainText(accept_python=False).from_python('  this  ')
        Traceback (most recent call last):
          ...
        Invalid: Enter only letters, numbers, or _ (underscore)
        >>> PlainText(strip=True).to_python('  this  ')
        'this'
        >>> PlainText(strip=True).from_python('  this  ')
        'this'
    """

    regex = r"^[a-zA-Z_\-0-9]*$"

    messages = {
        'invalid': _('Enter only letters, numbers, or _ (underscore)'),
        'empty': _("Please enter a value"),
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

    """
    Test that the field contains only letters, numbers, underscore,
    and the hyphen.  Subclasses Regex.

    Examples::

        >>> PlainText.to_python('_this9_')
        '_this9_'
        >>> PlainText.from_python('  this  ')
        '  this  '
        >>> PlainText(accept_python=False).from_python('  this  ')
        Traceback (most recent call last):
          ...
        Invalid: Enter only letters, numbers, or _ (underscore)
        >>> PlainText(strip=True).to_python('  this  ')
        'this'
        >>> PlainText(strip=True).from_python('  this  ')
        'this'
    """

    regex = r"^[a-zA-Z_\s]*$"

    messages = {
        'invalid': _('Enter only letters'),
        'empty': _("Please enter a value"),
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



