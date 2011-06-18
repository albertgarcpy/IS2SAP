# -*- coding: utf-8 -*-
"""Controlador de Permiso"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates
from tg import tmpl_context, validate
from webhelpers import paginate

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import Permiso
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController
from is2sap.widgets.permiso_form import crear_permiso_form, editar_permiso_form

__all__ = ['PermisoController']

class PermisoController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='Permiso', page='index_permiso')      

    @expose('is2sap.templates.permiso.nuevo')
    def nuevo(self, **kw):
        """Despliega el formulario para añadir un nuevo Permiso."""
        tmpl_context.form = crear_permiso_form
        return dict(nombre_modelo='Permiso', page='nuevo_permiso', value=kw)

    @validate(crear_permiso_form, error_handler=nuevo)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        permiso = Permiso()
        permiso.nombre_permiso = kw['nombre_permiso']
        permiso.descripcion = kw['descripcion']
        DBSession.add(permiso)
        DBSession.flush()    
        redirect("/admin/permiso/listado")

    @expose("is2sap.templates.permiso.listado")
    def listado(self,page=1):
        """Metodo para listar todos los Permisos existentes de la base de datos"""
        permisos = DBSession.query(Permiso).order_by(Permiso.id_permiso)
        currentPage = paginate.Page(permisos, page, items_per_page=5)
        return dict(permisos=currentPage.items,
           page='listado_permiso', currentPage=currentPage)

    @expose('is2sap.templates.permiso.editar')
    def editar(self, id_permiso, **kw):
        """Metodo que rellena el formulario para editar los datos de un Permiso"""
        tmpl_context.form = editar_permiso_form
        traerPermiso=DBSession.query(Permiso).get(id_permiso)
        kw['id_permiso']=traerPermiso.id_permiso
        kw['nombre_permiso']=traerPermiso.nombre_permiso
        kw['descripcion']=traerPermiso.descripcion
        return dict(nombre_modelo='Permiso', page='editar_permiso', value=kw)

    @validate(editar_permiso_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualizar la base de datos"""
        permiso = DBSession.query(Permiso).get(kw['id_permiso'])   
        permiso.nombre_permiso=kw['nombre_permiso']
        permiso.descripcion = kw['descripcion']
        DBSession.flush()
        redirect("/admin/permiso/listado")

    @expose('is2sap.templates.permiso.confirmar_eliminar')
    def confirmar_eliminar(self, id_permiso, **kw):
        """Despliega confirmacion de eliminacion"""
        permiso=DBSession.query(Permiso).get(id_permiso)
        return dict(nombre_modelo='Permiso', page='eliminar_permiso', value=permiso)

    @expose()
    def delete(self, id_permiso, **kw):
        """Metodo que elimina un registro de la base de datos"""
        DBSession.delete(DBSession.query(Permiso).get(id_permiso))
        redirect("/admin/permiso/listado")
