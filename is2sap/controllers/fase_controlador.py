# -*- coding: utf-8 -*-
"""Controlador de Fase"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates
from tg import tmpl_context, validate
from webhelpers import paginate
from sqlalchemy.orm import contains_eager
from sqlalchemy import func

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import Fase, Proyecto, EstadoFase, TipoItem, Atributo
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController
from is2sap.widgets.fase_form import crear_fase_form, editar_fase_form

__all__ = ['FaseController']

class FaseController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='Fase', page='index_fase')     

    @expose('is2sap.templates.fase.nuevo')
    def nuevo(self, **kw):
        """Despliega el formulario para añadir una fase al proyecto."""
        tmpl_context.form = crear_fase_form
        return dict(nombre_modelo='Fase', page='nueva_fase', value=kw)

    @expose('is2sap.templates.fase.nuevo')
    def nuevoDesdeProyecto(self, id_proyecto, **kw):
        """Despliega el formulario para añadir una fase al proyecto."""
        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        if proyecto.iniciado == True:
            flash("Proyecto ya iniciado. No puede crear fases!")
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)

        tmpl_context.form = crear_fase_form
        maxnumerofase=DBSession.query(func.max(Fase.numero_fase)).filter_by(id_proyecto=id_proyecto).first()
        kw['id_proyecto']=id_proyecto
        kw['id_estado_fase']=1

        if maxnumerofase[0]==None:
           kw['numero_fase']=1
        else:
           kw['numero_fase']=maxnumerofase[0] + 1

        return dict(nombre_modelo='Fase', idProyecto=id_proyecto, page='nuevo', value=kw)

    @validate(crear_fase_form, error_handler=nuevoDesdeProyecto)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        fase = Fase()
        fase.id_estado_fase=kw['id_estado_fase']
        fase.id_proyecto = kw['id_proyecto']
        fase.nombre = kw['nombre']
        fase.descripcion = kw['descripcion']
        fase.numero_fase = kw['numero_fase']
        DBSession.add(fase)
        DBSession.flush()    
        redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=kw['id_proyecto'])

    @expose("is2sap.templates.fase.listado")
    def listado(self,page=1):
        """Metodo para listar las Fases de un proyecto """
        fases = DBSession.query(Fase)
        currentPage = paginate.Page(fases, page, items_per_page=5)
        return dict(fases=currentPage.items,
           page='listado', currentPage=currentPage)

    @expose("is2sap.templates.fase.listadoFasesPorProyecto")
    def listadoFasesPorProyecto(self,id_proyecto, page=1):
        """Metodo para listar las Fases de un proyecto """         
        fasesPorProyecto = DBSession.query(Fase).join(Fase.relacion_estado_fase).filter(Fase.id_proyecto==id_proyecto).options(contains_eager(Fase.relacion_estado_fase)).order_by(Fase.numero_fase)
#        fasesPorProyecto = DBSession.query(Fase).filter_by(id_proyecto=id_proyecto).order_by(Fase.numero_fase)
        nombreProyecto = DBSession.query(Proyecto.nombre).filter_by(id_proyecto=id_proyecto).first()
        currentPage = paginate.Page(fasesPorProyecto, page, items_per_page=5)
        return dict(fasesPorProyecto=currentPage.items,
           page='listado_fases', nombre_proyecto=nombreProyecto, id_proyecto=id_proyecto, currentPage=currentPage)

    @expose('is2sap.templates.fase.editar')
    def editar(self, id_proyecto, id_fase, **kw):
        """Metodo que rellena el formulario para editar los datos de una Fase"""

        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        if proyecto.iniciado == True:
            flash("Proyecto ya iniciado. No puede editar fases!")
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)

        tmpl_context.form = editar_fase_form
        traerFase=DBSession.query(Fase).get(id_fase)
        kw['id_fase']=traerFase.id_fase
        kw['id_estado_fase']=traerFase.id_estado_fase
        kw['id_proyecto']=traerFase.id_proyecto
        kw['nombre']=traerFase.nombre
        kw['descripcion']=traerFase.descripcion
        kw['numero_fase']=traerFase.numero_fase
        return dict(nombre_modelo='Fase', page='editar_fase', value=kw)

    @validate(editar_fase_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la fase en la base de datos"""
        fase = DBSession.query(Fase).get(kw['id_fase'])
        fase.nombre=kw['nombre']
        fase.numero_fase=kw['numero_fase']
        fase.descripcion = kw['descripcion']
        DBSession.flush()
        redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=kw['id_proyecto'])

    @expose('is2sap.templates.fase.confirmar_eliminar')
    def confirmar_eliminar(self, id_proyecto, id_fase, **kw):
        """Despliega confirmacion de eliminacion"""
        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        if proyecto.iniciado == True:
           flash("Proyecto ya iniciado. No puede eliminar fases!")
           redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)

        fase=DBSession.query(Fase).get(id_fase)
        return dict(nombre_modelo='Fase', page='eliminar_fase', value=fase)

    @expose()
    def delete(self, id_proyecto, id_fase, **kw):
        """ Metodo que elimina un registro de la base de datos 
            Parametros:
                       -  id_fase: identificador de la fase
        """
        tipo_items = DBSession.query(TipoItem).filter_by(id_fase=id_fase).all()

        for tipo_item in tipo_items:
           id_tipo_item = tipo_item.id_tipo_item
           atributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item).all()
           for atributo in atributos:
              DBSession.delete(DBSession.query(Atributo).get(atributo.id_atributo))
           DBSession.delete(DBSession.query(TipoItem).get(id_tipo_item))

        DBSession.delete(DBSession.query(Fase).get(id_fase))
        flash("Fase eliminada!")

        redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)
