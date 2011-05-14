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
from is2sap.model.model import Item
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController


from is2sap.widgets.item_form import crear_item_form, editar_item_form



__all__ = ['ItemController']

class ItemController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla de bienvenida"""
        redirect("/admin/item/listado")        


    @expose('is2sap.templates.item.nuevo')
    def nuevo(self, **kw):
        """Despliega el formulario para añadir un nuevo Item."""
        tmpl_context.form = crear_item_form
        return dict(nombre_modelo='Item', page='nuevo', value=kw)

    @validate(crear_item_form, error_handler=nuevo)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        item = Item()
        item.id_tipo_item = kw['id_tipo_item']
        item.id_linea_base = kw['id_linea_base']
        item.numero = kw['numero']
        item.descripcion = kw['descripcion']
        item.complejidad = kw['complejidad']
        item.prioridad = kw['prioridad']
        item.estado = kw['estado']
	item.archivo_externo = kw['archivo_externo']
	item.version = kw['version']
	item.observacion = kw['observacion']
	item.fecha_modificacion = kw['fecha_modificacion']
        DBSession.add(item)
        DBSession.flush()    
        redirect("/admin/item/listado")

    @expose("is2sap.templates.item.listado")
    def listado(self,page=1):
        """Metodo para listar todos los items de la base de datos"""
        items = DBSession.query(Item)#.order_by(Usuario.id)
        currentPage = paginate.Page(items, page, items_per_page=5)
        return dict(items=currentPage.items,
           page='listado', currentPage=currentPage)



    @expose('is2sap.templates.item.editar')
    def editar(self, id_item, **kw):
        """Metodo que rellena el formulario para editar los datos de un item"""
        tmpl_context.form = editar_item_form
        traerItem=DBSession.query(Item).get(id_item)
        kw['id_item']=traerItem.id_item
        kw['id_tipo_item']=traerItem.id_tipo_item
        kw['id_linea_base']=traerItem.id_linea_base
        kw['numero']=traerItem.numero
        kw['descripcion']=traerItem.descripcion
        kw['complejidad']=traerItem.complejidad
        kw['prioridad']=traerItem.prioridad
        kw['estado']=traerItem.estado
	kw['archivo_externo']=traerItem.archivo_externo
	kw['version']=traerItem.version
	kw['observacion']=traerItem.observacion
	kw['fecha_modificacion']=traerItem.fecha_modificacion
	return dict(nombre_modelo='Item', page='editar', value=kw)


    @validate(editar_item_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        item = DBSession.query(Item).get(kw['id_item'])   
        item.id_tipo_item = kw['id_tipo_item']
        item.id_linea_base = kw['id_linea_base']
        item.numero = kw['numero']
        item.descripcion = kw['descripcion']
        item.complejidad = kw['complejidad']
        item.prioridad = kw['prioridad']
        item.estado = kw['estado']
	item.archivo_externo = kw['archivo_externo']
	item.version = kw['version']
	item.observacion = kw['observacion']
	item.fecha_modificacion = kw['fecha_modificacion']
        DBSession.flush()
        redirect("/admin/item/listado")


    @expose('is2sap.templates.item.confirmar_eliminar')
    def confirmar_eliminar(self, id_item, **kw):
        """Despliega confirmacion de eliminacion"""
        item=DBSession.query(Item).get(id_item)
        return dict(nombre_modelo='Item', page='editar', value=item)


    @expose()
    def delete(self, id_item, **kw):
        """Metodo que elimina un registro de la base de datos"""
        DBSession.delete(DBSession.query(Item).get(id_item))
        redirect("/admin/item/listado")
