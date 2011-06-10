# -*- coding: utf-8 -*-
"""Controlador de Relacion"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates
from tg import tmpl_context, validate
from webhelpers import paginate

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import Relacion
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController



__all__ = ['RelacionController']


class RelacionController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='Relacion', page='index_relacion')        


    @expose('is2sap.templates.usuario.nuevo')
    def nuevo(self, **kw):
        """Despliega el formulario para añadir un nuevo Usuario."""
        tmpl_context.form = crear_usuario_form
        return dict(nombre_modelo='Usuario', page='nuevo_usuario', value=kw)


    @validate(crear_usuario_form, error_handler=nuevo)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """       
        

    @expose("is2sap.templates.usuario.listado")
    def listado(self,page=1):
        """Metodo para listar todos los usuarios de la base de datos"""

        currentPage = paginate.Page(usuarios, page, items_per_page=5)
        return dict(usuarios=currentPage.items,
           page='listado_usuario', currentPage=currentPage)

    @expose('is2sap.templates.usuario.editar')
    def editar(self, id_usuario, **kw):
        """Metodo que rellena el formulario para editar los datos de un usuario"""
        return dict(nombre_modelo='Usuario', page='editar_usuario', value=kw)

    @validate(editar_usuario_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""


    @expose('is2sap.templates.usuario.confirmar_eliminar')
    def confirmar_eliminar(self, id_usuario, **kw):
        """Despliega confirmacion de eliminacion"""

        return dict(nombre_modelo='Usuario', page='eliminar_usuario', value=usuario)

    @expose()
    def delete(self, id_usuario, **kw):
        """Metodo que elimina un registro de la base de datos"""

        redirect("/admin/usuario/listado")
