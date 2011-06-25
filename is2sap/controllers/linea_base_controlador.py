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
from sqlalchemy import func
from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata

from is2sap.model.model import TipoItem, Item, Proyecto, Usuario, Fase, Atributo, ItemDetalle, ItemHistorial, ItemDetalleHistorial, LineaBase, LineaBase_Item, LineaBaseHistorial, LineaBaseItemHistorial
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
    def nuevo(self, id_fase, **kw):
        """Despliega el formulario para añadir una linea base a la fase"""
	fase=DBSession.query(Fase).get(id_fase)
	#Comprobación de si el estado de la fase se encuentra en Con Lineas Bases
	if fase.relacion_estado_fase.nombre_estado=='Con Lineas Bases':
		flash(_("Todos los items de esta fase ya se encuentran en una Linea Base Aprobada"), 'warning')
                redirect("/admin/linea_base/listado_linea_bases",id_proyecto=fase.id_proyecto, id_fase=id_fase)	    
	tipo_items=DBSession.query(TipoItem).filter_by(id_fase=id_fase)
	itemsDeFaseActual = []
	for tipo_item in tipo_items:
		itemsTipoItem = DBSession.query(Item).filter_by(id_tipo_item=tipo_item.id_tipo_item).filter_by(vivo=True)
		for itemTipoItem in itemsTipoItem:
			itemsDeFaseActual.append(itemTipoItem)
	contador_items_en_fase_actual = 0
	for item in itemsDeFaseActual:
		contador_items_en_fase_actual = contador_items_en_fase_actual + 1
	#Comprobación de si existen items cargados para la fase actual
	if contador_items_en_fase_actual == 0:
		flash(_("Aun no existen items cargados para esta fase"), 'warning')
                redirect("/admin/linea_base/listado_linea_bases",id_proyecto=fase.id_proyecto, id_fase=id_fase)		
        kw['id_estado']= 'Desarrollo'
        kw['id_fase']= id_fase
	kw['version']= '1'
	tmpl_context.form = crear_linea_base_form
        return dict(nombre_modelo='LineaBase', id_proyecto=fase.id_proyecto, id_fase=id_fase, page='nuevo', value=kw)


    
    
    @validate(crear_linea_base_form, error_handler=nuevo)
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
        linea_bases = DBSession.query(LineaBase)
        currentPage = paginate.Page(linea_bases, page, items_per_page=5)
        return dict(linea_bases=currentPage.items,
           page='listado', currentPage=currentPage)



    @expose('is2sap.templates.linea_base.editar')
    def editar(self, id_fase, id_linea_base, **kw):
        """Metodo que rellena el formulario para editar los datos de un Línea Base"""
	traerLineaBase=DBSession.query(LineaBase).get(id_linea_base)
	if traerLineaBase.estado=='Aprobado':
		flash(_("No puede editar una Linea Base Aprobada"), 'warning')
                redirect("/admin/linea_base/listado_linea_bases",id_proyecto=id_proyecto, id_fase=id_fase)
	
        
        kw['id_linea_base']=traerLineaBase.id_linea_base
	kw['nombre']=traerLineaBase.nombre
        kw['descripcion']=traerLineaBase.descripcion
	kw['estado']=traerLineaBase.estado
        kw['id_fase']=traerLineaBase.id_fase
        kw['version']=traerLineaBase.version
	
        tmpl_context.form = editar_linea_base_form
	fase=DBSession.query(Fase).get(id_fase)
	return dict(nombre_modelo='LineaBase', id_proyecto=fase.id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base, page='editar', value=kw)


    @validate(editar_linea_base_form, error_handler=editar)
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


    @expose("is2sap.templates.linea_base.aprobaciones")
    def aprobaciones(self, id_proyecto, id_fase, page=1):
        """Metodo para aprobar todos las linea_bases"""
        linea_bases = DBSession.query(LineaBase).filter_by(id_fase=id_fase).order_by(LineaBase.id_linea_base)
        currentPage = paginate.Page(linea_bases, page, items_per_page=5)
        return dict(linea_bases=currentPage.items,
           page='aprobaciones', id_proyecto=id_proyecto, id_fase=id_fase, currentPage=currentPage)


    @expose()
    def aprobar(self, id_proyecto, id_fase, id_linea_base, **kw):     
        """Metodo que aprueba la linea base"""
	linea_base = DBSession.query(LineaBase).get(id_linea_base)
	#Se realiza comprobaciones si la linea base se encuentra en estado de Revision
	if linea_base.estado=='Revision':
		sw=0
                items=linea_base.items
		for item in items:
			if item.estado=='Revision':
				sw=1
		if sw==1:
			flash(_("No puede aprobar la Linea Base, contiene items en revision"), 'error')
                	redirect("/admin/linea_base/listado_linea_bases",id_proyecto=id_proyecto, id_fase=id_fase)

	if linea_base.estado=='Aprobado':
		flash(_("La Linea Base ya se encuentra aprobada"), 'warning')
                redirect("/admin/linea_base/listado_linea_bases",id_proyecto=id_proyecto, id_fase=id_fase)
	items = linea_base.items
	#Se verifica antes de aprobar que la linea base tenga por lo menos un item
	if items == []:
		flash(_("No puede aprobar una Linea Base sin items"), 'error')
                redirect("/admin/linea_base/listado_linea_bases",id_proyecto=id_proyecto, id_fase=id_fase)
	#Aqui se aprueba la linea base
	linea_base.estado = 'Aprobado'
	DBSession.flush()
	################################### Modificacion de Estado de Fases ###############################
	linea_bases=DBSession.query(LineaBase).filter_by(id_fase=id_fase).filter_by(estado='Aprobado')
	itemsenLineaBase = []
	for linea_base in linea_bases:
		itemsLineaBase = linea_base.items
		for itemLineaBase in itemsLineaBase:
			itemsenLineaBase.append(itemLineaBase)
	contador_items_en_linea_base = 0
	for item in itemsenLineaBase:
		contador_items_en_linea_base = contador_items_en_linea_base + 1
	#Se almacena la cantidad de items que se encuentran en una linea base aprobada dentro de la fase actual en: contador_items_en_linea_base
	tipo_items=DBSession.query(TipoItem).filter_by(id_fase=id_fase)
	itemsDeFaseActual = []
	for tipo_item in tipo_items:
		itemsTipoItem = DBSession.query(Item).filter_by(id_tipo_item=tipo_item.id_tipo_item).filter_by(vivo=True).filter_by(estado='Aprobado')
		for itemTipoItem in itemsTipoItem:
			itemsDeFaseActual.append(itemTipoItem)
	contador_items_en_fase_actual = 0
	for item in itemsDeFaseActual:
		contador_items_en_fase_actual = contador_items_en_fase_actual + 1
	#Se almacena la cantidad de items que se encuentran en la fase actual en: contador_items_en_fase_actual
	fase=DBSession.query(Fase).get(id_fase)
	#Aqui se verifica si todos los items de la fase actual se encuentran en una linea base
	if contador_items_en_linea_base == contador_items_en_fase_actual:
		#En caso positivo el estado de la fase actual pasa al estado Con Lineas Bases(Id=4)
		fase.id_estado_fase = '4'
	if contador_items_en_linea_base < contador_items_en_fase_actual:	
		#En este caso, el estado de la fase actual pasa al estado Con Lineas Bases Parciales(Id=3)
		fase.id_estado_fase = '3'
	DBSession.flush()
	maxnumerofase = DBSession.query(func.max(Fase.numero_fase)).filter_by(id_proyecto=id_proyecto).first()
	#A continuación se verifica que: si existe una fase posterior, dicha fase cambia a estado de Desarrollo(Id=2)
	if fase.numero_fase < maxnumerofase:
		numero_fase_siguiente = fase.numero_fase+1 
		fase_siguiente=DBSession.query(Fase).filter_by(id_proyecto=id_proyecto).filter_by(numero_fase=numero_fase_siguiente).first()
		fase_siguiente.id_estado_fase = '2'	        
        DBSession.flush()
	flash("Linea Base Aprobada")
        redirect("/admin/linea_base/listado_linea_bases",id_proyecto=id_proyecto, id_fase=id_fase)

    
    @expose()
    def romper(self,  id_proyecto, id_fase, id_linea_base, **kw):     
        """Metodo que rompe la linea base"""
	fase=DBSession.query(Fase).get(id_fase)
	linea_bases=DBSession.query(LineaBase).filter_by(id_fase=id_fase).filter_by(estado='Aprobado')
	itemsenLineaBase = []
	for linea_base in linea_bases:
		itemsLineaBase = linea_base.items
		for itemLineaBase in itemsLineaBase:
			itemsenLineaBase.append(itemLineaBase)
	contador_items_en_linea_base = 0
	for item in itemsenLineaBase:
		contador_items_en_linea_base = contador_items_en_linea_base + 1
	#Se almacena la cantidad de items que se encuentran en una linea base aprobada dentro de la fase actual en: contador_items_en_linea_base
	if contador_items_en_linea_base==1:
		if fase.relacion_estado_fase.nombre_estado=='Con Lineas Bases' or fase.relacion_estado_fase.nombre_estado=='Con Lineas Bases Parciales':
			fase.id_estado_fase='2'
			maxnumerofase = DBSession.query(func.max(Fase.numero_fase)).filter_by(id_proyecto=id_proyecto).first()
			#A continuación se verifica que: si existe una fase posterior, y si no tiene items, tendrá que tener el estado de su fase inicial
			if fase.numero_fase < maxnumerofase:
				numero_fase_siguiente = fase.numero_fase+1 
				fase_siguiente=DBSession.query(Fase).filter_by(id_proyecto=id_proyecto).filter_by(numero_fase=numero_fase_siguiente).first()
				tipo_items=DBSession.query(TipoItem).filter_by(id_fase=fase_siguiente.id_fase)
				itemsDeFaseActual = []
				for tipo_item in tipo_items:
					itemsTipoItem = DBSession.query(Item).filter_by(id_tipo_item=tipo_item.id_tipo_item).filter_by(vivo=True)
					for itemTipoItem in itemsTipoItem:
						itemsDeFaseActual.append(itemTipoItem)
				contador_items_en_fase_siguiente = 0
				for item in itemsDeFaseActual:
					contador_items_en_fase_siguiente = contador_items_en_fase_siguiente + 1
				if contador_items_en_fase_siguiente == 0:
					fase_siguiente.id_estado_fase='1'	
	
	#Comprueba si la fase se encuentra en el estado Con Linas Bases, cambia al estado Con Lineas Bases Parciales,
	# si es que existe más de un item en una linea base
	if contador_items_en_linea_base>1:
		if fase.relacion_estado_fase.nombre_estado=='Con Lineas Bases':
		      fase.id_estado_fase='3'

	DBSession.flush()
        linea_base = DBSession.query(LineaBase).get(id_linea_base)
	#Cambia el estado de la linea base de Aprobado a Desarrollo
	linea_base.estado = 'Desarrollo' 
	
	
	DBSession.flush()
	#Guarda en el historial la última linea base aprobada
	linea_baseHistorial = LineaBaseHistorial()
        linea_baseHistorial.id_linea_base = linea_base.id_linea_base
        linea_baseHistorial.nombre = linea_base.nombre
        linea_baseHistorial.descripcion = linea_base.descripcion
        linea_baseHistorial.estado = linea_base.estado
        linea_baseHistorial.id_fase = linea_base.id_fase
	linea_baseHistorial.version = linea_base.version
	DBSession.add(linea_baseHistorial)
	DBSession.flush() 
	linea_baseHistorial=DBSession.query(LineaBaseHistorial).filter_by(id_linea_base=linea_base.id_linea_base).filter_by(version=linea_base.version).first()
	items = linea_base.items
        #Aqui se van agregando registros a la tabla Linea_Base_Item_Historial para que el 
	#sistema guarde automáticamente el historial de los items que contiene la linea base
	for item in items:
        	#item.linea_bases_historial.append(linea_baseHistorial)
		linea_base_item_historial=LineaBaseItemHistorial()
		linea_base_item_historial.relacion=linea_baseHistorial
		linea_base_item_historial.id_item=item.id_item
		linea_base_item_historial.id_historial_linea_base=linea_baseHistorial.id_historial_linea_base
		linea_base_item_historial.version=item.version
		item.linea_bases_historial.append(linea_base_item_historial)
		DBSession.add(linea_base_item_historial)
		DBSession.flush()
		 
	
        version_aux = int(linea_base.version)+1
  	linea_base.version = str(version_aux)
	DBSession.flush()
	flash("Linea Base Rota")
        redirect("/admin/linea_base/listado_linea_bases", id_proyecto=id_proyecto, id_fase=id_fase)


    @expose('is2sap.templates.linea_base.confirmar_romper')
    def confirmar_romper(self, id_proyecto, id_fase, id_linea_base, **kw):
        """Despliega confirmar romper linea base"""
        linea_base=DBSession.query(LineaBase).get(id_linea_base)
	#Si la linea base se encuentra en estado Desarrollo o Revision no podrá romper
	if linea_base.estado=='Desarrollo' or linea_base.estado=='Revision':
		flash(_("La Linea Base no esta aprobada"), 'error')
                redirect("/admin/linea_base/listado_linea_bases",id_proyecto=id_proyecto, id_fase=id_fase)
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
        #fasesProyecto = proyecto.fases
	fasesProyecto = DBSession.query(Fase).filter_by(id_proyecto=id_proyecto).order_by(Fase.id_fase)
	fases=[]
	for fase in fasesProyecto:
	   if fase.id_estado_fase <> 1:
	        fases.append(fase)
        currentPage = paginate.Page(fases, page, items_per_page=5)
        return dict(fases=currentPage.items, page='listado_fases', 
           nombre_proyecto=proyecto.nombre, id_proyecto=proyecto.id_proyecto, currentPage=currentPage)


    @expose("is2sap.templates.linea_base.listado_linea_bases")
    def listado_linea_bases(self, id_proyecto, id_fase, page=1):
        """Metodo para listar las lineas bases de una Fase """
        fase = DBSession.query(Fase).get(id_fase)
        #linea_bases = fase.linea_bases
	linea_bases = DBSession.query(LineaBase).filter_by(id_fase=id_fase).order_by(LineaBase.id_linea_base)
        currentPage = paginate.Page(linea_bases, page, items_per_page=5)
        return dict(linea_bases=currentPage.items,
           page='listado_linea_bases', nombre_fase=fase.nombre, id_proyecto=id_proyecto, id_fase=id_fase, currentPage=currentPage)


    @expose("is2sap.templates.linea_base.historial_linea_bases")
    def historial_linea_bases(self, id_fase, id_linea_base, page=1):
        """Metodo para listar el historial de una linea base"""
	fase = DBSession.query(Fase).get(id_fase)
	id_proyecto=fase.id_proyecto
        linea_base = DBSession.query(LineaBase).get(id_linea_base)
        linea_bases = linea_base.linea_base_historial
	if linea_bases==[]:
		flash(_("La Linea Base no tiene historiales"), 'warning')
                redirect("/admin/linea_base/listado_linea_bases",id_proyecto=id_proyecto, id_fase=id_fase)
        currentPage = paginate.Page(linea_bases, page, items_per_page=5)
        return dict(linea_bases=currentPage.items,
           page='historial_linea_bases', nombre_linea_base=linea_base.nombre, id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base, currentPage=currentPage)


    @expose("is2sap.templates.linea_base.listadoItemsPorLineaBase")
    def listadoItemsPorLineaBase(self, id_proyecto, id_fase, id_linea_base, page=1):
        """Metodo para listar todos los items de la base de datos que pertenecen a la linea base"""
        linea_base=DBSession.query(LineaBase).get(id_linea_base)
	items = linea_base.items
        currentPage = paginate.Page(items, page)
        return dict(items=currentPage.items, page='listadoItemsPorLineaBase', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, currentPage=currentPage)

	
    @expose("is2sap.templates.linea_base.listadoItemsParaAsignaraLineaBase")
    def listadoItemsParaAsignaraLineaBase(self, id_proyecto, id_fase, id_linea_base, page=1):
        """Metodo para listar todos los items a asignar a la linea base"""
	lineabase=DBSession.query(LineaBase).get(id_linea_base)
        if lineabase.estado=='Aprobado':
		flash(_("La Linea Base ya se encuentra aprobada"), 'warning')
                redirect("/admin/linea_base/listado_linea_bases",id_proyecto=id_proyecto, id_fase=id_fase)
	linea_bases=DBSession.query(LineaBase).filter_by(id_fase=id_fase)
	itemsenLineaBase = []
	for linea_base in linea_bases:
		itemsLineaBase = linea_base.items
		for itemLineaBase in itemsLineaBase:
			itemsenLineaBase.append(itemLineaBase)
	#items Contiene todos los items que se encuentran en la fase actual
	tipo_items=DBSession.query(TipoItem).filter_by(id_fase=id_fase)
	itemsDeFaseActual = []
	for tipo_item in tipo_items:
		itemsTipoItem = DBSession.query(Item).filter_by(id_tipo_item=tipo_item.id_tipo_item).filter_by(vivo=True).filter_by(estado='Aprobado').order_by(Item.id_item)
		for itemTipoItem in itemsTipoItem:
			itemsDeFaseActual.append(itemTipoItem)
	items=itemsDeFaseActual 
	for item in itemsenLineaBase:
           items.remove(item)
        currentPage = paginate.Page(items, page)
        return dict(items=currentPage.items, page='listadoItemsParaAsignaraLineaBase', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, currentPage=currentPage)

    
    @expose()
    def asignarItem(self, id_proyecto, id_fase, id_linea_base, id_item):
        """Metodo que realiza la asignacion de un item a la linea base selecccionada"""
	linea_base=DBSession.query(LineaBase).get(id_linea_base)
	if linea_base.estado=='Aprobado':
		flash(_("La Linea Base esta Aprobada y no puede modificarse"), 'error')
                redirect("/admin/linea_base/listadoItemsParaAsignaraLineaBase",id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base)
        item = DBSession.query(Item).get(id_item)
        linea_base = DBSession.query(LineaBase).get(id_linea_base)
        item.linea_bases.append(linea_base)
	flash("Item Asignado a la Linea Base")
        redirect("/admin/linea_base/listadoItemsParaAsignaraLineaBase",id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base)


    @expose()
    def desasignar_item_linea_base(self, id_proyecto, id_fase, id_linea_base, id_item, **kw):
        """Metodo que desasigna un item de la linea base seleccionada"""
	linea_base=DBSession.query(LineaBase).get(id_linea_base)
	if linea_base.estado=='Aprobado':
		flash(_("La Linea Base esta Aprobada y no puede modificarse"), 'error')
                redirect("/admin/linea_base/listadoItemsPorLineaBase",id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base)
        item = DBSession.query(Item).get(id_item)
        linea_base = DBSession.query(LineaBase).get(id_linea_base)
        item.linea_bases.remove(linea_base)
	flash("Item Desasignado de la Linea Base")
        redirect("/admin/linea_base/listadoItemsPorLineaBase", id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base)


    @expose("is2sap.templates.linea_base.listado_detalles_items_linea_base")
    def listado_detalles_items_linea_base(self, id_proyecto, id_fase, id_linea_base, id_item, page=1):
        """Metodo para listar todos los detalles de los items que pertenecen a la linea base"""
        detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item).order_by(ItemDetalle.id_item_detalle)
        currentPage = paginate.Page(detalles, page)
        return dict(detalles=currentPage.items, page='listado_detalles_items_linea_base', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, id_item=id_item, currentPage=currentPage)


    @expose("is2sap.templates.linea_base.listadoItemsPorLineaBaseHistorial")
    def listadoItemsPorLineaBaseHistorial(self, id_proyecto, id_fase, id_linea_base, version, page=1):
        """Metodo para listar todos los items de la base de datos que pertenecen al historial de la linea base"""
	linea_base_historial=DBSession.query(LineaBaseHistorial).filter_by(id_linea_base=id_linea_base).filter_by(version=version).first()
	items=DBSession.query(LineaBaseItemHistorial).filter_by(id_historial_linea_base=linea_base_historial.id_historial_linea_base)
	
	items_historial_linea_base=[]
	
	for item in items:
		print item.id_item
		id_item=item.id_item
		version_buscar=item.version
		item_historial=DBSession.query(Item).filter_by(id_item=id_item).filter_by(version=version_buscar).first()
		if item_historial==None:
			item_historial=DBSession.query(ItemHistorial).filter_by(id_item=id_item).filter_by(version=version_buscar).first()
		if item_historial<>None:	
			items_historial_linea_base.append(item_historial)
		 
	items=items_historial_linea_base	
	#items = linea_base_historial.items_historial_assocs
	#items = linea_base_item_historial.item_historial
        currentPage = paginate.Page(items, page)
        return dict(items=currentPage.items, page='listadoItemsPorLineaBaseHistorial', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, version=version, currentPage=currentPage)


    @expose("is2sap.templates.linea_base.listado_detalles_items_linea_base_historial")
    def listado_detalles_items_linea_base_historial(self, id_proyecto, id_fase, id_linea_base, id_item, version, page=1):
        """Metodo para listar todos los detalles de los items que pertenecen a la linea base"""
	item=DBSession.query(Item).get(id_item)
	version_actual=item.version
	detalles=[]
	if version==version_actual:
        	detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item).order_by(ItemDetalle.id_item_detalle)
	if version<version_actual:
		detalles = DBSession.query(ItemDetalleHistorial).filter_by(id_item=id_item).filter_by(version=version).order_by(ItemDetalleHistorial.id_historial_item_detalle)
        currentPage = paginate.Page(detalles, page)
        return dict(detalles=currentPage.items, page='listado_detalles_items_linea_base_historial', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, id_item=id_item, version=version, currentPage=currentPage)

   
