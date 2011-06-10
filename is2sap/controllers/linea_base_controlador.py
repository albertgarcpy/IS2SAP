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

from is2sap.model.model import TipoItem, Item, Proyecto, Usuario, Fase, Atributo, ItemDetalle, ItemHistorial, ItemDetalleHistorial, LineaBase
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
        """Despliega el formulario para añadir una linea base a la fase"""
        tmpl_context.form = crear_linea_base_form
        return dict(nombre_modelo='LineaBase', page='nueva_linea_base', value=kw)


    @expose('is2sap.templates.linea_base.nuevo')
    def nuevoDesdeFase(self, id_fase, **kw):
        """Despliega el formulario para añadir una linea base a la fase"""
        tmpl_context.form = crear_linea_base_form
        kw['id_estado']= 'Desarrollo'
        kw['id_fase']= id_fase
	kw['version']= '1'
        return dict(nombre_modelo='LineaBase', idFase=id_fase, page='nuevo', value=kw)


    @validate(crear_linea_base_form, error_handler=nuevoDesdeFase)
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
        tmpl_context.form = editar_linea_base_form
        traerLineaBase=DBSession.query(LineaBase).get(id_linea_base)
        kw['id_linea_base']=traerLineaBase.id_linea_base
	kw['nombre']=traerLineaBase.nombre
        kw['descripcion']=traerLineaBase.descripcion
        kw['estado']=traerLineaBase.estado
        kw['id_fase']=traerLineaBase.id_fase
        kw['version']=traerLineaBase.version
	return dict(nombre_modelo='LineaBase', id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base, page='editar', value=kw)


    @validate(editar_linea_base_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        linea_base = DBSession.query(LineaBase).get(kw['id_linea_base'])
	linea_base.nombre = kw['nombre']   
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
	if linea_base.estado == 'Revision':
		version_aux = int(linea_base.version)+1
  		linea_base.version = str(version_aux)
	  
        linea_base.estado = 'Aprobado'

        DBSession.flush()
        redirect("/admin/linea_base/aprobaciones")

    
    @expose()
    def romper(self, id_linea_base, **kw):     
        """Metodo que rompe la linea base"""
        linea_base = DBSession.query(LineaBase).get(id_linea_base)   
        linea_base.estado = 'Revision'
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
        fases = proyecto.fases
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
           page='historial_linea_bases', nombre_linea_base=linea_base.nombre, id_proyecto=id_proyecto, id_fase=id_fase, currentPage=currentPage)


   
