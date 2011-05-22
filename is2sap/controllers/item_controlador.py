# -*- coding: utf-8 -*-
"""Controlador de Item"""
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
from tw.forms import TableForm, Spacer, TextField, PasswordField, CalendarDatePicker
from tw.forms.fields import Button, SubmitButton, HiddenField, CheckBox
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *


from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import TipoItem, Item, Proyecto, Usuario, Fase, Atributo
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController
from is2sap.widgets.item_form import ItemForm, editar_item_form


__all__ = ['ItemController']


crear_item_form = None

class ItemController(RestController):

    allow_only = has_permission('edicion',
                                msg=l_('Solo para usuarios con permiso "edicion"'))


    @expose()
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='Item', page='index_item')


    @expose('is2sap.templates.item.nuevo')
    def nuevo(self, id_proyecto, id_fase, id_tipo_item, **kw):
        """Despliega el formulario para anhadir un nuevo Item."""

        fields = [
                HiddenField('id_item', label_text='Id',
                      help_text='Id del item'),
                HiddenField('id_tipo_item', validator=NotEmpty, label_text='Tipo de Item',
                      help_text='Introduzca el tipo de item'),
                Spacer(),
                TextField('id_linea_base', label_text='Linea Base',
                      help_text='Introduzca la linea Base'),
                Spacer(),
                TextField('numero', validator=NotEmpty, label_text='Numero',
                      help_text='Introduzca un numero para el item'),
                Spacer(),
                TextField('descripcion', validator=PlainText, label_text='Descripcion',
                      help_text='Introduzca una descripcion'),
                Spacer(),
                TextField('complejidad', validator=PlainText, label_text='Complejidad',
                      help_text='Introduzca su direccion de domicilio.'),
                Spacer(),
                TextField('prioridad', validator=PlainText, label_text='Prioridad',
                      help_text='Introduzca la prioridad'),
                Spacer(),
                TextField('estado', validator=PlainText, label_text='Estado',
                      help_text='Introduzca un estado valido'),
                Spacer(),
	        TextField('archivo_externo', validator=PlainText, label_text='Archivo Externo',
                      help_text='Introduzca un archivo externo'),
                Spacer(),
	        TextField('version', validator=PlainText, label_text='Version',
                      help_text='Introduzca una version'),
                Spacer(),
	        TextField('observacion', validator=PlainText, label_text='Observacion',
                      help_text='Introduzca una observacion'),
                Spacer(),
	        CalendarDatePicker('fecha_modificacion', label_text='Fecha de Modificacion',
                      help_text='Introduzca una fecha de modificacion'),
                Spacer(),
                CheckBox('vivo', label_text='Vivo', default='True',
                     help_text='Indica si esta vivo'),
                Spacer()]

        atributos_nuevos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item)

        for atributo_nuevo in atributos_nuevos:

              nombre = atributo_nuevo.nombre
              tipo = atributo_nuevo.tipo              
        
              if tipo=='Texto':
                 nuevo_atributo = TextField(nombre, validator=PlainText, label_text=nombre,
                              help_text='Introduzca')
              elif tipo=='Numerico':
                 nuevo_atributo = TextField(nombre, validator=Int, label_text=nombre,
                              help_text='Introduzca')
              else:
                 nuevo_atributo = CalendarDatePicker('fecha', label_text=nombre,
                              help_text='Seleccione la fecha de Creacion del Proyecto')
              fields.append(nuevo_atributo)

        global crear_item_form
        crear_item_form = ItemForm("CrearItem", action='add',fields=fields)
        kw['id_tipo_item']= int(id_tipo_item)      
        tmpl_context.form = crear_item_form

        return dict(nombre_modelo='Item', id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, page='nuevo_item', value=kw)

    #@validate(crear_item_form, error_handler=nuevo)
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
        item.vivo = kw['vivo']
        DBSession.add(item)
        DBSession.flush()    
        redirect("/item/index")

    @expose("is2sap.templates.item.listado")
    def listado(self, id_proyecto, id_fase, id_tipo_item, page=1):
        """Metodo para listar todos los items de la base de datos"""
        items = DBSession.query(Item).filter_by(id_tipo_item=id_tipo_item)
        currentPage = paginate.Page(items, page, items_per_page=5)
        return dict(items=currentPage.items,
           page='listado_item', id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, currentPage=currentPage)

    @expose("is2sap.templates.item.listado_proyectos")
    def proyectos(self,page=1):
        """Metodo para listar todos los Proyectos existentes de la base de datos"""
        usuario = DBSession.query(Usuario).filter_by(nombre_usuario=request.identity['repoze.who.userid']).first()
        proyectos = usuario.proyectos
        currentPage = paginate.Page(proyectos, page, items_per_page=5)
        return dict(proyectos=currentPage.items,
           page='listado_proyectos', currentPage=currentPage)

    @expose("is2sap.templates.item.listado_fases")
    def fases(self,id_proyecto, page=1):
        """Metodo para listar las Fases de un proyecto """
        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        fases = proyecto.fases
        currentPage = paginate.Page(fases, page, items_per_page=5)
        return dict(fases=currentPage.items, page='listado_fases', 
           nombre_proyecto=proyecto.nombre, id_proyecto=proyecto.id_proyecto, currentPage=currentPage)

    @expose("is2sap.templates.item.listado_tipo_items")
    def tipoItems(self, id_proyecto, id_fase, page=1):
        """Metodo para listar los Tipos de Items de una Fase """
        fase = DBSession.query(Fase).get(id_fase)
        tipoItems = fase.tipoitems
        currentPage = paginate.Page(tipoItems, page, items_per_page=5)
        return dict(tipoItems=currentPage.items,
           page='listado_tipo_items', nombre_fase=fase.nombre, id_proyecto=id_proyecto, id_fase=id_fase, currentPage=currentPage)

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
        tipo_item=DBSession.query(TipoItem).get(item.id_tipo_item)
        return dict(nombre_modelo='Item', page='editar', nombre_tipo_item=tipo_item.nombre,item=item)


    @expose()
    def delete(self, id_item, **kw):
        """Metodo que elimina un registro de la base de datos"""
        DBSession.delete(DBSession.query(Item).get(id_item))
        redirect("/admin/item/listado")


"""

        
        print 'Imprimiento d'
        d={}
        crear_item_form.update_params(d)
        print d['children']
        #diccio={'fields':newItems}
        #crear_item_form.update_params(diccio)
"""
