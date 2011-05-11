# -*- coding: utf-8 -*-
"""Controlador de Usuario"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates
from tg import tmpl_context, validate
from webhelpers import paginate

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import Rol
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController

from is2sap.widgets.rol_form import crear_rol_form, editar_rol_form


__all__ = ['RolController']

class RolController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla de bienvenida"""
        redirect("/admin/proyecto/listado")        

    @expose('is2sap.templates.rol.nuevo')
    def nuevo(self, **kw):
        """Despliega el formulario para añadir un nuevo Proyecto."""
        tmpl_context.form = crear_rol_form
        return dict(nombre_modelo='Rol', page='nuevo_rol', value=kw)

    @validate(crear_rol_form, error_handler=nuevo)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        rol = Rol()
        rol.nombre_rol = kw['nombre_rol']
        rol.descripcion = kw['descripcion']
        DBSession.add(rol)
        DBSession.flush()    
        redirect("/admin/rol/listado")

    @expose("is2sap.templates.rol.listado")
    def listado(self,page=1):
        """Metodo para listar todos los Proyectos existentes de la base de datos"""
        roles = DBSession.query(Rol).order_by(Rol.id_rol)
        currentPage = paginate.Page(roles, page, items_per_page=5)
        return dict(roles=currentPage.items,
           page='listado_rol', currentPage=currentPage)

    @expose('is2sap.templates.rol.editar')
    def editar(self, id_rol, **kw):
        """Metodo que rellena el formulario para editar los datos de un Proyecto"""
        tmpl_context.form = editar_rol_form
        traerRol=DBSession.query(Rol).get(id_rol)
        kw['id_rol']=traerRol.id_rol
        kw['nombre_rol']=traerRol.nombre_rol
        kw['descripcion']=traerRol.descripcion
        return dict(nombre_modelo='Rol', page='editar_rol', value=kw)


    @validate(editar_rol_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        rol = DBSession.query(Rol).get(kw['id_rol'])   
        rol.nombre_rol=kw['nombre_rol']
        rol.descripcion = kw['descripcion']
        DBSession.flush()
        redirect("/admin/rol/listado")


    @expose('is2sap.templates.rol.confirmar_eliminar')
    def confirmar_eliminar(self, id_rol, **kw):
        """Despliega confirmacion de eliminacion"""
        rol=DBSession.query(Rol).get(id_rol)
        return dict(nombre_modelo='Rol', page='eliminar_rol', value=rol)


    @expose()
    def delete(self, id_rol, **kw):
        """Metodo que elimina un registro de la base de datos"""
        DBSession.delete(DBSession.query(Rol).get(id_rol))
        redirect("/admin/rol/listado")