# -*- coding: utf-8 -*-
"""Controlador de Atributo"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates
from tg import tmpl_context, validate
from webhelpers import paginate

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import Atributo
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController


from is2sap.widgets.atributo_form import crear_atributo_form, editar_atributo_form



__all__ = ['AtributoController']

class AtributoController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla de bienvenida"""
        redirect("/admin/atributo/listado")        


#    @expose('is2sap.templates.atributo.nuevo')
#    def nuevo(self, **kw):
#        """Despliega el formulario para añadir un nuevo atributo."""
#        tmpl_context.form = crear_atributo_form
#        return dict(nombre_modelo='Atributo', page='nuevo', value=kw)

    @expose('is2sap.templates.atributo.nuevoDesdeTipoItem')
    def nuevoDesdeTipoItem(self, id_tipo_item, **kw):
        """Despliega el formulario para añadir un nuevo atributo."""
        tmpl_context.form = crear_atributo_form
        kw['id_tipo_item']=id_tipo_item
        return dict(nombre_modelo='Atributo', idTipoItem=id_tipo_item, page='nuevo', value=kw)

    @validate(crear_atributo_form, error_handler=nuevoDesdeTipoItem)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        atributo = Atributo()
        atributo.id_tipo_item = kw['id_tipo_item']
        atributo.nombre = kw['nombre']
        atributo.descripcion = kw['descripcion']
        atributo.tipo = kw['tipo']
        DBSession.add(atributo)
        DBSession.flush()    
        redirect("/admin/atributo/listadoAtributosPorTipoItem", id_tipo_item=kw['id_tipo_item'])

#    @expose("is2sap.templates.atributo.listado")
#    def listado(self,page=1):
#        """Metodo para listar todos los atributos de la base de datos"""
#        atributos = DBSession.query(Atributo)#.order_by(Usuario.id)
#        currentPage = paginate.Page(atributos, page, items_per_page=5)
#        return dict(atributos=currentPage.items,
#           page='listado', currentPage=currentPage)

    @expose("is2sap.templates.atributo.listadoAtributosPorTipoItem")
    def listadoAtributosPorTipoItem(self, id_tipo_item, page=1):
        """Metodo para listar todos los atributos de la base de datos"""
        atributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item).order_by(Atributo.id_atributo)
        currentPage = paginate.Page(atributos, page, items_per_page=5)
        return dict(atributos=currentPage.items,
           page='listado', idTipoItem=id_tipo_item, currentPage=currentPage)


    @expose('is2sap.templates.atributo.editar')
    def editar(self, id_atributo, **kw):
        """Metodo que rellena el formulario para editar los datos de un usuario"""
        tmpl_context.form = editar_atributo_form
        traerAtributo=DBSession.query(Atributo).get(id_atributo)
        kw['id_atributo']=traerAtributo.id_atributo
        kw['id_tipo_item']=traerAtributo.id_tipo_item
        kw['nombre']=traerAtributo.nombre
        kw['descripcion']=traerAtributo.descripcion
        kw['tipo']=traerAtributo.tipo
        return dict(nombre_modelo='Atributo', page='editar', value=kw)


    @validate(editar_atributo_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        atributo = DBSession.query(Atributo).get(kw['id_atributo'])   
        atributo.id_tipo_item = kw['id_tipo_item']
        atributo.nombre=kw['nombre']
        atributo.descripcion = kw['descripcion']
        atributo.tipo = kw['tipo']
        DBSession.flush()
        redirect("/admin/atributo/listadoAtributosPorTipoItem", id_tipo_item=kw['id_tipo_item'])


    @expose('is2sap.templates.atributo.confirmar_eliminar')
    def confirmar_eliminar(self, id_atributo, **kw):
        """Despliega confirmacion de eliminacion"""
        atributo=DBSession.query(Atributo).get(id_atributo)
        return dict(nombre_modelo='Atributo', page='editar', value=atributo)


    @expose()
    def delete(self, id_atributo, id_tipo_item, **kw):
        """ Metodo que elimina el registro de un atributo
            Parametros: - id_atributo: Para identificar el atributo a eliminar
                        - id_tipo_item: Para redireccionar al listado de atributos correspondientes al tipo de item 
        """
        DBSession.delete(DBSession.query(Atributo).get(id_atributo))
        redirect("/admin/atributo/listadoAtributosPorTipoItem", id_tipo_item=id_tipo_item)
