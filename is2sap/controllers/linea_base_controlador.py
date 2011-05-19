# -*- coding: utf-8 -*-
"""Controlador de Linea Base"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates
from tg import tmpl_context, validate
from webhelpers import paginate

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import LineaBase
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController


from is2sap.widgets.linea_base_form import crear_linea_base_form, editar_linea_base_form



__all__ = ['LineaBaseController']

class LineaBaseController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla de bienvenida"""
        redirect("/admin/linea_base/listado")        


    @expose('is2sap.templates.linea_base.nuevo')
    def nuevo(self, **kw):
        """Despliega el formulario para añadir un nuevo Línea Base."""
        tmpl_context.form = crear_linea_base_form
        return dict(nombre_modelo='LineaBase', page='nuevo', value=kw)

    @validate(crear_linea_base_form, error_handler=nuevo)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        linea_base = LineaBase()
        linea_base.descripcion = kw['descripcion']
        linea_base.estado = kw['estado']
        linea_base.id_fase = kw['id_fase']
        linea_base.version = kw['version']
        DBSession.add(linea_base)
        DBSession.flush()    
        redirect("/admin/linea_base/listado")

    @expose("is2sap.templates.linea_base.listado")
    def listado(self,page=1):
        """Metodo para listar todos los linea_bases de la base de datos"""
        linea_bases = DBSession.query(LineaBase)#.order_by(Usuario.id)
        currentPage = paginate.Page(linea_bases, page, items_per_page=5)
        return dict(linea_bases=currentPage.items,
           page='listado', currentPage=currentPage)



    @expose('is2sap.templates.linea_base.editar')
    def editar(self, id_linea_base, **kw):
        """Metodo que rellena el formulario para editar los datos de un Línea Base"""
        tmpl_context.form = editar_linea_base_form
        traerLineaBase=DBSession.query(LineaBase).get(id_linea_base)
        kw['id_linea_base']=traerLineaBase.id_linea_base
        kw['descripcion']=traerLineaBase.descripcion
        kw['estado']=traerLineaBase.estado
        kw['id_fase']=traerLineaBase.id_fase
        kw['version']=traerLineaBase.version
        return dict(nombre_modelo='LineaBase', page='editar', value=kw)


    @validate(editar_linea_base_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        linea_base = DBSession.query(LineaBase).get(kw['id_linea_base'])   
        linea_base.descripcion = kw['descripcion']
        linea_base.estado = kw['estado']
        linea_base.id_fase = kw['id_fase']
        linea_base.version = kw['version']
        DBSession.flush()
        redirect("/admin/linea_base/listado")


    @expose('is2sap.templates.linea_base.confirmar_eliminar')
    def confirmar_eliminar(self, id_linea_base, **kw):
        """Despliega confirmacion de eliminacion"""
        linea_base=DBSession.query(LineaBase).get(id_linea_base)
        return dict(nombre_modelo='LineaBase', page='editar', value=linea_base)


    @expose()
    def delete(self, id_linea_base, **kw):
        """Metodo que elimina un registro de la base de datos"""
        DBSession.delete(DBSession.query(LineaBase).get(id_linea_base))
        redirect("/admin/linea_base/listado")
   

    @expose("is2sap.templates.linea_base.aprobaciones")
    def aprobaciones(self,page=1):
        """Metodo para aprobar todos las linea_bases"""
        linea_bases = DBSession.query(LineaBase)#.order_by(Usuario.id)
        currentPage = paginate.Page(linea_bases, page, items_per_page=5)
        return dict(linea_bases=currentPage.items,
           page='aprobaciones', currentPage=currentPage)


    @expose()
    def aprobar(self, id_linea_base, **kw):     
        """Metodo que aprueba la linea base"""
        linea_base = DBSession.query(LineaBase).get(id_linea_base)   
        linea_base.estado = 'APROBADO'
        DBSession.flush()
        redirect("/admin/linea_base/aprobaciones")

    
    @expose()
    def romper(self, id_linea_base, **kw):     
        """Metodo que rompe la linea base"""
        linea_base = DBSession.query(LineaBase).get(id_linea_base)   
        linea_base.estado = 'REVISION'
        DBSession.flush()
        redirect("/admin/linea_base/aprobaciones")


    @expose('is2sap.templates.linea_base.confirmar_romper')
    def confirmar_romper(self, id_linea_base, **kw):
        """Despliega confirmar romper linea base"""
        linea_base=DBSession.query(LineaBase).get(id_linea_base)
        return dict(nombre_modelo='LineaBase', page='editar', value=linea_base)


    @expose('is2sap.templates.linea_base.confirmar_aprobar')
    def confirmar_aprobar(self, id_linea_base, **kw):
        """Despliega confirmar aprobar linea base"""
        linea_base=DBSession.query(LineaBase).get(id_linea_base)
        return dict(nombre_modelo='LineaBase', page='editar', value=linea_base)
