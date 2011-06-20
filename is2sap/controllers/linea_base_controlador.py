# -*- coding: utf-8 -*-
"""Controlador de Linea Base"""

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
from sqlalchemy.orm import contains_eager
import shutil
import os
from pkg_resources import resource_filename

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata

from is2sap.model.model import TipoItem, Item, Proyecto, Usuario, Fase, Atributo, ItemDetalle, ItemHistorial, ItemDetalleHistorial, LineaBase, LineaBase_Item, LineaBaseHistorial
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController


from is2sap.widgets.linea_base_form import LineaBaseForm, EditLineaBaseForm

from tw.forms import TableForm, Spacer, TextField, PasswordField, TextArea
from tw.forms.fields import Button, SubmitButton, HiddenField
from tw.forms.validators import *
from is2sap.widgets.mi_validador.mi_validador import *



__all__ = ['LineaBaseController']

class LineaBaseController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla de bienvenida"""
        redirect("/admin/linea_base/listado")        


    @expose('is2sap.templates.linea_base.nuevo')
    def nuevo(self, **kw):
        """Despliega el formulario para añadir una linea base a la fase"""
        tmpl_context.form = crear_linea_base_form
        return dict(nombre_modelo='LineaBase', page='nueva_linea_base', value=kw)


    @expose('is2sap.templates.linea_base.nuevo')
    def nuevoDesdeFase(self, id_proyecto, id_fase, **kw):
        """Despliega el formulario para añadir una linea base a la fase"""
	fields = [
        HiddenField('id_linea_base', label_text='Id',
            help_text='Id del usuario'),
	TextField('nombre', validator=NotEmpty, label_text='Nombre',
            help_text='Introduzca el nombre de la linea base'),
        Spacer(),
	TextArea('descripcion', label_text='Descripcion',
            help_text='Introduzca una descripcion de la linea base'),        
        Spacer(),
	HiddenField('id_estado', validator=NotEmpty, label_text='Estado',
            help_text='Identificador del estado de la linea base.'),
	HiddenField('id_fase', validator=NotEmpty, label_text='Fase',
            help_text='Identificador de la fase.'),
	HiddenField('version', validator=NotEmpty, label_text='Version',
            help_text='Version de la linea base')]
	crear_linea_base_form = LineaBaseForm("CrearLineaBase", action='add',fields=fields)
        tmpl_context.form = crear_linea_base_form
        kw['id_estado']= 'Desarrollo'
        kw['id_fase']= id_fase
	kw['version']= '1'
        return dict(nombre_modelo='LineaBase', id_proyecto=id_proyecto, id_fase=id_fase, page='nuevo', value=kw)


    #@validate(crear_linea_base_form, error_handler=nuevoDesdeFase)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
	
        linea_base = LineaBase()
	linea_base.nombre = kw['nombre']
        linea_base.descripcion = kw['descripcion']
        linea_base.estado = kw['id_estado']
        linea_base.id_fase = kw['id_fase']
        linea_base.version = kw['version']
        DBSession.add(linea_base)
        DBSession.flush()
	id_fase = kw['id_fase']
	flash("Linea Base Generada")
	id_proyecto=DBSession.query(Fase.id_proyecto).filter_by(id_fase=id_fase).first()    
        redirect("/admin/linea_base/listado_linea_bases",id_proyecto=id_proyecto, id_fase=id_fase)

    @expose("is2sap.templates.linea_base.listado")
    def listado(self,page=1):
        """Metodo para listar todos los linea_bases de la base de datos"""
        linea_bases = DBSession.query(LineaBase)#.order_by(Usuario.id)
        currentPage = paginate.Page(linea_bases, page, items_per_page=5)
        return dict(linea_bases=currentPage.items,
           page='listado', currentPage=currentPage)



    @expose('is2sap.templates.linea_base.editar')
    def editar(self, id_proyecto, id_fase, id_linea_base, **kw):
        """Metodo que rellena el formulario para editar los datos de un Línea Base"""
	traerLineaBase=DBSession.query(LineaBase).get(id_linea_base)
	deshabilitado=False
	if traerLineaBase.estado=='Aprobado':
		deshabilitado=True
	fields = [
       HiddenField('id_linea_base', label_text='Id',
            help_text='Id del usuario'),
	TextField('nombre', validator=NotEmpty, label_text='Nombre', disabled=deshabilitado,
            help_text='Introduzca el nombre de la linea base'),
        Spacer(),
	TextArea('descripcion', label_text='Descripcion', disabled=deshabilitado,
            help_text='Introduzca una descripcion de la linea base'),        
        Spacer(),
	HiddenField('estado', validator=NotEmpty, label_text='Estado',
            help_text='Identificador del estado de la linea base.'),
	HiddenField('id_fase', validator=NotEmpty, label_text='Fase',
            help_text='Identificador de la fase.'),
	HiddenField('version', validator=NotEmpty, label_text='Version',
            help_text='Version de la linea base')]
	
        
        kw['id_linea_base']=traerLineaBase.id_linea_base
	kw['nombre']=traerLineaBase.nombre
        kw['descripcion']=traerLineaBase.descripcion
	kw['estado']=traerLineaBase.estado
        kw['id_fase']=traerLineaBase.id_fase
        kw['version']=traerLineaBase.version
	editar_linea_base_form = EditLineaBaseForm("EditarLineaBase", action='update', fields=fields)
        tmpl_context.form = editar_linea_base_form
	
	return dict(nombre_modelo='LineaBase', id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base, page='editar', value=kw)


    #@validate(editar_linea_base_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        linea_base = DBSession.query(LineaBase).get(kw['id_linea_base'])
	linea_base.nombre = kw['nombre']   
        linea_base.descripcion = kw['descripcion']
	auxiliar = kw['estado']
	if auxiliar=='Revision':
		auxiliar='Desarrollo'
        linea_base.estado = auxiliar
        linea_base.id_fase = kw['id_fase']
        linea_base.version = kw['version']
	id_fase = kw['id_fase']
	DBSession.flush()
	id_proyecto=DBSession.query(Fase.id_proyecto).filter_by(id_fase=id_fase).first()  
	flash("Linea Base Editada")
	redirect("/admin/linea_base/listado_linea_bases", id_proyecto=id_proyecto, id_fase=id_fase)


    @expose('is2sap.templates.linea_base.confirmar_eliminar')
    def confirmar_eliminar(self, id_linea_base, **kw):
        """Despliega confirmacion de eliminacion"""
        linea_base=DBSession.query(LineaBase).get(id_linea_base)
        return dict(nombre_modelo='LineaBase', page='editar', value=linea_base)


    @expose("is2sap.templates.linea_base.aprobaciones")
    def aprobaciones(self, id_proyecto, id_fase, page=1):
        """Metodo para aprobar todos las linea_bases"""
        linea_bases = DBSession.query(LineaBase).order_by(LineaBase.id_linea_base)
        currentPage = paginate.Page(linea_bases, page, items_per_page=5)
        return dict(linea_bases=currentPage.items,
           page='aprobaciones', id_proyecto=id_proyecto, id_fase=id_fase, currentPage=currentPage)


    @expose()
    def aprobar(self, id_proyecto, id_fase, id_linea_base, **kw):     
        """Metodo que aprueba la linea base"""
	linea_base = DBSession.query(LineaBase).get(id_linea_base)
	items = linea_base.items
	if items == []:
		flash(_("No puede aprobar una Linea Base sin items"), 'warning')
                redirect("/admin/linea_base/aprobaciones",id_proyecto=id_proyecto, id_fase=id_fase)	
        linea_base.estado = 'Aprobado'
        DBSession.flush()
	flash("Linea Base Aprobada")
        redirect("/admin/linea_base/aprobaciones",id_proyecto=id_proyecto, id_fase=id_fase)

    
    @expose()
    def romper(self,  id_proyecto, id_fase, id_linea_base, **kw):     
        """Metodo que rompe la linea base"""
        linea_base = DBSession.query(LineaBase).get(id_linea_base)
	linea_base.estado = 'Desarrollo' 
	#Guarda en el historial la última linea base aprobada
	linea_baseHistorial = LineaBaseHistorial()
        linea_baseHistorial.id_linea_base = linea_base.id_linea_base
        linea_baseHistorial.nombre = linea_base.nombre
        linea_baseHistorial.descripcion = linea_base.descripcion
        linea_baseHistorial.estado = linea_base.estado
        linea_baseHistorial.id_fase = linea_base.id_fase
	linea_baseHistorial.version = linea_base.version
	items = linea_base.items
        #Aqui se van agregando registros a la tabla Linea_Base_Item_Historial
	#Para que el sistema guarde automáticamente el historial de los items que contiene la linea base
	for item in items:
        	item.linea_bases_historial.append(linea_baseHistorial)

        DBSession.add(linea_baseHistorial) 
	version_aux = int(linea_base.version)+1
  	linea_base.version = str(version_aux)
	DBSession.flush()
	flash("Linea Base Rota")
        redirect("/admin/linea_base/aprobaciones", id_proyecto=id_proyecto, id_fase=id_fase)


    @expose('is2sap.templates.linea_base.confirmar_romper')
    def confirmar_romper(self, id_proyecto, id_fase, id_linea_base, **kw):
        """Despliega confirmar romper linea base"""
        linea_base=DBSession.query(LineaBase).get(id_linea_base)
        return dict(nombre_modelo='LineaBase', id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base, page='editar', value=linea_base)


    @expose("is2sap.templates.linea_base.listado_proyectos")
    def proyectos(self,page=1):
        """Metodo para listar todos los Proyectos existentes de la base de datos"""
        usuario = DBSession.query(Usuario).filter_by(nombre_usuario=request.identity['repoze.who.userid']).first()
        todosProyectos = usuario.proyectos
	proyectos = []
        for proyecto in todosProyectos:
            if proyecto.iniciado == True:
               proyectos.append(proyecto)

        currentPage = paginate.Page(proyectos, page, items_per_page=5)
        return dict(proyectos=currentPage.items,
           page='listado_proyectos', currentPage=currentPage)
	

    @expose("is2sap.templates.linea_base.listado_fases")
    def fases(self,id_proyecto, page=1):
        """Metodo para listar las Fases de un proyecto """
        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        fasesProyecto = proyecto.fases
	fases = DBSession.query(Fase).all()
	for fase in fasesProyecto:
	   if fase.id_estado_fase == 1:
	        fases.remove(fase)
        currentPage = paginate.Page(fases, page, items_per_page=5)
        return dict(fases=currentPage.items, page='listado_fases', 
           nombre_proyecto=proyecto.nombre, id_proyecto=proyecto.id_proyecto, currentPage=currentPage)


    @expose("is2sap.templates.linea_base.listado_linea_bases")
    def listado_linea_bases(self, id_proyecto, id_fase, page=1):
        """Metodo para listar las lineas bases de una Fase """
        fase = DBSession.query(Fase).get(id_fase)
        linea_bases = fase.linea_bases
        currentPage = paginate.Page(linea_bases, page, items_per_page=5)
        return dict(linea_bases=currentPage.items,
           page='listado_linea_bases', nombre_fase=fase.nombre, id_proyecto=id_proyecto, id_fase=id_fase, currentPage=currentPage)


    @expose("is2sap.templates.linea_base.historial_linea_bases")
    def historial_linea_bases(self, id_proyecto, id_fase, id_linea_base, page=1):
        """Metodo para listar el historial de una linea base"""
        linea_base = DBSession.query(LineaBase).get(id_linea_base)
        linea_bases = linea_base.linea_base_historial
        currentPage = paginate.Page(linea_bases, page, items_per_page=5)
        return dict(linea_bases=currentPage.items,
           page='historial_linea_bases', nombre_linea_base=linea_base.nombre, id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base, currentPage=currentPage)


    @expose("is2sap.templates.linea_base.listadoItemsPorLineaBase")
    def listadoItemsPorLineaBase(self, id_proyecto, id_fase, id_linea_base, page=1):
        """Metodo para listar todos los items de la base de datos que pertenecen a la linea base"""
        linea_base=DBSession.query(LineaBase).get(id_linea_base)
	items = linea_base.items
        currentPage = paginate.Page(items, page)#, items_per_page=1)
        return dict(items=currentPage.items, page='listadoItemsPorLineaBase', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, currentPage=currentPage)

	
    @expose("is2sap.templates.linea_base.listadoItemsParaAsignaraLineaBase")
    def listadoItemsParaAsignaraLineaBase(self, id_proyecto, id_fase, id_linea_base, page=1):
        """Metodo para listar todos los items a asignar a la linea base"""
        #linea_base=DBSession.query(LineaBase).get(id_linea_base)
	linea_bases=DBSession.query(LineaBase).all()
	itemsenLineaBase = []
	for linea_base in linea_bases:
		itemsLineaBase = linea_base.items
		for itemLineaBase in itemsLineaBase:
			itemsenLineaBase.append(itemLineaBase)
	items = DBSession.query(Item).filter_by(vivo=True).filter_by(estado='Aprobado').all()
	for item in itemsenLineaBase:
           items.remove(item)
        currentPage = paginate.Page(items, page)#, items_per_page=1)
        return dict(items=currentPage.items, page='listadoItemsParaAsignaraLineaBase', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, currentPage=currentPage)

    
    @expose()
    def asignarItem(self, id_proyecto, id_fase, id_linea_base, id_item):
        """Metodo que realiza la asignacion de un item a la linea base selecccionada"""
	linea_base=DBSession.query(LineaBase).get(id_linea_base)
	if linea_base.estado=='Aprobado':
		flash(_("La Linea Base esta Aprobada y no puede modificarse"), 'warning')
                redirect("/admin/linea_base/listadoItemsParaAsignaraLineaBase",id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base)
        item = DBSession.query(Item).get(id_item)
        linea_base = DBSession.query(LineaBase).get(id_linea_base)
        item.linea_bases.append(linea_base)

        redirect("/admin/linea_base/listadoItemsParaAsignaraLineaBase",id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base)


    @expose()
    def desasignar_item_linea_base(self, id_proyecto, id_fase, id_linea_base, id_item, **kw):
        """Metodo que desasigna un item de la linea base seleccionada"""
	linea_base=DBSession.query(LineaBase).get(id_linea_base)
	if linea_base.estado=='Aprobado':
		flash(_("La Linea Base esta Aprobada y no puede modificarse"), 'warning')
                redirect("/admin/linea_base/listadoItemsPorLineaBase",id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base)
        item = DBSession.query(Item).get(id_item)
        linea_base = DBSession.query(LineaBase).get(id_linea_base)
        item.linea_bases.remove(linea_base)

        redirect("/admin/linea_base/listadoItemsPorLineaBase", id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base)


    @expose("is2sap.templates.linea_base.listado_detalles_items_linea_base")
    def listado_detalles_items_linea_base(self, id_proyecto, id_fase, id_linea_base, id_item, page=1):
        """Metodo para listar todos los detalles de los items que pertenecen a la linea base"""
        detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item).order_by(ItemDetalle.id_item_detalle)
        currentPage = paginate.Page(detalles, page)#, items_per_page=1)
        return dict(detalles=currentPage.items, page='listado_detalles_items_linea_base', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, id_item=id_item, currentPage=currentPage)


    @expose("is2sap.templates.linea_base.listadoItemsPorLineaBaseHistorial")
    def listadoItemsPorLineaBaseHistorial(self, id_proyecto, id_fase, id_linea_base, version, page=1):
        """Metodo para listar todos los items de la base de datos que pertenecen al historial de la linea base"""
	linea_base_historial=DBSession.query(LineaBaseHistorial).filter_by(id_linea_base=id_linea_base).filter_by(version=version).first()
	items = linea_base_historial.items_historial
        currentPage = paginate.Page(items, page)#, items_per_page=1)
        return dict(items=currentPage.items, page='listadoItemsPorLineaBaseHistorial', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, currentPage=currentPage)


    @expose("is2sap.templates.linea_base.listado_detalles_items_linea_base_historial")
    def listado_detalles_items_linea_base_historial(self, id_proyecto, id_fase, id_linea_base, id_item, version, page=1):
        """Metodo para listar todos los detalles de los items que pertenecen a la linea base"""
        detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item).filter_by(version=version).order_by(ItemDetalle.id_item_detalle)
	if detalles == []:
		detalles = DBSession.query(ItemDetalleHistorial).filter_by(id_item=id_item).filter_by(version=version).order_by(ItemDetalleHistorial.id_historial_item_detalle)
        currentPage = paginate.Page(detalles, page)#, items_per_page=1)
        return dict(detalles=currentPage.items, page='listado_detalles_items_linea_base_historial', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, id_item=id_item, currentPage=currentPage)

   
