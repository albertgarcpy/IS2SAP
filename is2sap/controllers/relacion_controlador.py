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


from is2sap.widgets.relacion_form import crear_relacion_form, editar_relacion_form



__all__ = ['RelacionController']

class RelacionController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla de bienvenida"""
        redirect("/desa/relacion/listado")        


    @expose('is2sap.templates.relacion.nuevo')
    def nuevo(self, **kw):
        """Despliega el formulario para añadir un nueva Relacion."""
        tmpl_context.form = crear_relacion_form
        return dict(nombre_modelo='Relacion', page='nuevo', value=kw)

    @validate(crear_relacion_form, error_handler=nuevo)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        relacion = Relacion()
        relacion.estado = kw['id_estado']
        relacion.id_item1 = kw['id_item1']
        relacion.id_item2 = kw['id_item2']
        relacion.tipo = kw['tipo']
	relacion.version = kw['version']
        
        DBSession.add(item)
        DBSession.flush()    
        redirect("/desa/relacion/listado")

    @expose("is2sap.templates.relacion.listado")
    def listado(self,page=1):
        """Metodo para listar todos los items de la base de datos"""
        relacions = DBSession.query(Relacion)#.order_by(Usuario.id)
        currentPage = paginate.Page(relacions, page, items_per_page=5)
        return dict(relacions=currentPage.relacions,
           page='listado', currentPage=currentPage)



    @expose('is2sap.templates.relacion.editar')
    def editar(self, id_item, **kw):
        """Metodo que rellena el formulario para editar los datos de un relacion"""
        tmpl_context.form = editar_relacion_form
        traerRelacion=DBSession.query(Relacion).get(id_relacion)
        kw['estado']=traerRelacion.estado
        kw['id_item1']=traerRelacion.id_item1
        kw['id_item2']=traerRelacion.id_item2
        kw['tipo']=traerRelacion.tipo
        kw['version']=traerRelacion.version
        
	return dict(nombre_modelo='Relacion', page='editar', value=kw)


    @validate(editar_relacion_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        relacion = DBSession.query(Relacion).get(kw['id_relacion'])   
        relacion.estado = kw['estado']
        relacion.id_item1 = kw['id_item1']
        relacion.id_item2 = kw['id_item2']
        relacion.tipo = kw['tipo']
        relacion.version = kw['version']
        
        DBSession.flush()
        redirect("/desa/relacion/listado")


    @expose('is2sap.templates.relacion.confirmar_eliminar')
    def confirmar_eliminar(self, id_item, **kw):
        """Despliega confirmacion de eliminacion"""
        relacion=DBSession.query(Relacion).get(id_relacion)
        return dict(nombre_modelo='Relacion', page='editar', value=relacion)


    @expose()
    def delete(self, id_relacion, **kw):
        """Metodo que elimina un registro de la base de datos"""
        DBSession.delete(DBSession.query(Relacion).get(id_relacion))
        redirect("/desa/relacion/listado")
