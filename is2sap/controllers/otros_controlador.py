# -*- coding: utf-8 -*-
"""Controlador de Otras Opciones para SAP"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates
from tg import tmpl_context, validate
from webhelpers import paginate
from tg.controllers import RestController, redirect
from repoze.what.predicates import has_permission
import formencode
from tw import forms
from tw.forms import TableForm, Spacer, TextField, PasswordField, CalendarDatePicker, TextArea, SingleSelectField
from tw.forms.fields import Button, SubmitButton, HiddenField, CheckBox, FileField
from tw.forms.validators import *
from sqlalchemy.orm import contains_eager

import os
try:
    from hashlib import sha1
except ImportError:
    sys.exit('ImportError: No module named hashlib\n'
             'If you are on python2.4 this library is not part of python. '
             'Please install it. Example: easy_install hashlib')


from is2sap.widgets.mi_validador.mi_validador import *
from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import Proyecto, Usuario
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController
from is2sap.widgets.cambio_contrasenha_form import editar_contrasenha_form

from paste.request import construct_url, parse_formvars

__all__ = ['OtrosController']

class OtrosController(BaseController):

    #allow_only = has_permission('edicion',
    #                            msg=l_('Solo para usuarios con permiso "edicion"'))
    
    @expose('is2sap.templates.otros.index')
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre='Opciones', page='index_otros')

    @expose('is2sap.templates.otros.cambiar_contrasenha')
    def cambiar_contrasenha(self, **kw):
        """Metodo que rellena el formulario para editar los datos de un item"""
        tmpl_context.form = editar_contrasenha_form
	return dict(nombre_opcion='Cambio de Password', page='cambiar_contrasenha', value=kw)

    @validate(editar_contrasenha_form, error_handler=cambiar_contrasenha)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        nombre_usuario = request.identity['repoze.who.userid']
        usuario = DBSession.query(Usuario).filter_by(nombre_usuario=nombre_usuario).first()
        password_anterior = usuario.password
        password_anterior_form = kw['password_anterior_form']
        password_nuevo = kw['password_nuevo']
        password_nuevo_repeticion = kw['password_nuevo_repeticion']

        #identity = request.environ.get('repoze.who.identity')
        #print identity

        hash = sha1()
        if isinstance(password_anterior_form, unicode):
            password_anterior_form = password_anterior_form.encode('utf-8')
        hash.update(password_anterior_form + str(password_anterior[:40]))
        result = password_anterior[40:] == hash.hexdigest()

        if result == True and password_nuevo == password_nuevo_repeticion:
           usuario.password = password_nuevo
        else:
           flash(_('Datos incorrectos'), 'warning')
           redirect("/otros/cambiar_contrasenha")
         
        flash("Su password se cambio con exito!")
        redirect("/otras_op")
