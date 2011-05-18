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
from is2sap.model.model import Proyecto, Usuario
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController


from is2sap.widgets.proyecto_form import crear_proyecto_form, editar_proyecto_form



__all__ = ['ProyectoController']

class ProyectoController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla de bienvenida"""
        redirect("/admin/proyecto/listado")        


    @expose('is2sap.templates.proyecto.nuevo')
    def nuevo(self, **kw):
        """Despliega el formulario para añadir un nuevo Proyecto."""
        tmpl_context.form = crear_proyecto_form
        usuario_id= DBSession.query(Usuario.id_usuario).filter_by(nombre_usuario=request.identity['repoze.who.userid']).first()
        kw['id_usuario']=usuario_id
        return dict(nombre_modelo='Proyecto', page='nuevo', value=kw)

    @validate(crear_proyecto_form, error_handler=nuevo)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        proyecto = Proyecto()
        proyecto.id_usuario=kw['id_usuario']
        proyecto.nombre = kw['nombre']
        proyecto.descripcion = kw['descripcion']
        proyecto.fecha = kw['fecha']
        proyecto.iniciado = kw['iniciado']
        DBSession.add(proyecto)
        DBSession.flush()    
        redirect("/admin/proyecto/listado")

    @expose("is2sap.templates.proyecto.listado")
    def listado(self,page=1):
        """Metodo para listar todos los Proyectos existentes de la base de datos"""
        proyectos = DBSession.query(Proyecto).order_by(Proyecto.id_proyecto)
        currentPage = paginate.Page(proyectos, page, items_per_page=5)
        return dict(proyectos=currentPage.items,
           page='listado', currentPage=currentPage)



    @expose('is2sap.templates.proyecto.editar')
    def editar(self, id_proyecto, **kw):
        """Metodo que rellena el formulario para editar los datos de un Proyecto"""
        traerProyecto=DBSession.query(Proyecto).get(id_proyecto)
        tmpl_context.form = editar_proyecto_form            
        kw['id_proyecto']=traerProyecto.id_proyecto
        kw['id_usuario']=traerProyecto.id_usuario
        kw['nombre']=traerProyecto.nombre
        kw['descripcion']=traerProyecto.descripcion
        kw['fecha']=traerProyecto.fecha
        kw['iniciado']=traerProyecto.iniciado
        if traerProyecto.iniciado:
            flash("El proyecto no puede modificarse porque ya se encuentra iniciado.")
        return dict(nombre_modelo='Proyecto', page='editar_proyecto', value=kw)


    @validate(editar_proyecto_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        proyecto = DBSession.query(Proyecto).get(kw['id_proyecto'])   
        proyecto.id_usuario = kw['id_usuario']
        proyecto.nombre=kw['nombre']
        proyecto.descripcion = kw['descripcion']
        proyecto.fecha = kw['fecha']
        proyecto.inciado =kw['iniciado']
        DBSession.flush()
        redirect("/admin/proyecto/listado")


    @expose('is2sap.templates.proyecto.confirmar_eliminar')
    def confirmar_eliminar(self, id_proyecto, **kw):
        """Despliega confirmacion de eliminacion"""
        proyecto=DBSession.query(Proyecto).get(id_proyecto)
        return dict(nombre_modelo='Proyecto', page='eliminar_proyecto', value=proyecto)


    @expose()
    def delete(self, id_proyecto, **kw):
        """Metodo que elimina un registro de la base de datos"""
        DBSession.delete(DBSession.query(Proyecto).get(id_proyecto))
        redirect("/admin/proyecto/listado")
