from formencode import *
from is2sap.model import *
from is2sap.model import DBSession, metadata, Usuario
from tw.forms.validators import *


class UniqueUsername(FancyValidator):


   def validate_python(self, value, state):
      usuarios = DBSession.query(Usuario)
      for usuario in usuarios:
         if value == usuario.nombre_usuario:
             raise Invalid(
                 'El nombre de usuario ya existe.',
                 value, state)
