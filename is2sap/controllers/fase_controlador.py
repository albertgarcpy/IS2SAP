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
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import transaction

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
    @require(predicates.has_any_permission('lider_proyecto'))
    def nuevoDesdeProyecto(self, id_proyecto, **kw):
        """Despliega el formulario para añadir una fase al proyecto."""
        try:
            tmpl_context.form = crear_fase_form
            proyecto = DBSession.query(Proyecto).get(id_proyecto)

            if proyecto.iniciado == True:
               flash(_("Proyecto ya iniciado. No puede crear fases!"), 'error')
               redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)
         
            maxnumerofase = DBSession.query(func.max(Fase.numero_fase)).filter_by(id_proyecto=id_proyecto).first()
            kw['id_proyecto']=id_proyecto
            kw['id_estado_fase']=1

            if maxnumerofase[0]==None:
               kw['numero_fase']=1
            else:
               kw['numero_fase']=maxnumerofase[0] + 1

        except SQLAlchemyError:
            flash(_("No se pudo acceder a Creacion de Fases! SQLAlchemyError..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Creacion de Fases! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)

        return dict(nombre_modelo='Fase', idProyecto=id_proyecto, page='nuevo', value=kw)

    @validate(crear_fase_form, error_handler=nuevoDesdeProyecto)
    @expose()
    @require(predicates.has_any_permission('lider_proyecto'))
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        try:
            fase = Fase()
            fase.id_estado_fase=kw['id_estado_fase']
            fase.id_proyecto = kw['id_proyecto']
            fase.nombre = kw['nombre']
            fase.descripcion = kw['descripcion']
            fase.numero_fase = kw['numero_fase']
            DBSession.add(fase)
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=kw['id_proyecto'])
        except SQLAlchemyError:
            flash(_("No se ha guardado! SQLAlchemyError..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=kw['id_proyecto'])
        except (AttributeError, NameError):
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=kw['id_proyecto'])
        else:
            flash(_("Fase creada!"), 'ok')
    
        redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=kw['id_proyecto'])

    @expose("is2sap.templates.fase.listadoFasesPorProyecto")
    @require(predicates.has_any_permission('lider_proyecto'))
    def listadoFasesPorProyecto(self,id_proyecto, page=1):
        """Metodo para listar las Fases de un proyecto """
        try:         
            fasesPorProyecto = DBSession.query(Fase).join(Fase.relacion_estado_fase).filter(Fase.id_proyecto==id_proyecto).options(contains_eager(Fase.relacion_estado_fase)).order_by(Fase.numero_fase)
#           fasesPorProyecto = DBSession.query(Fase).filter_by(id_proyecto=id_proyecto).order_by(Fase.numero_fase)
            nombreProyecto = DBSession.query(Proyecto.nombre).filter_by(id_proyecto=id_proyecto).first()
            currentPage = paginate.Page(fasesPorProyecto, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Fases del Proyecto! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Fases del Proyecto! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listado")

        return dict(fasesPorProyecto=currentPage.items, page='listado_fases', 
                    nombre_proyecto=nombreProyecto, id_proyecto=id_proyecto, currentPage=currentPage)

    @expose('is2sap.templates.fase.editar')
    @require(predicates.has_any_permission('lider_proyecto'))
    def editar(self, id_proyecto, id_fase, **kw):
        """Metodo que rellena el formulario para editar los datos de una Fase"""
        try:
            tmpl_context.form = editar_fase_form
            proyecto = DBSession.query(Proyecto).get(id_proyecto)

            if proyecto.iniciado == True:
               flash(_("Proyecto ya iniciado. No puede editar fases!"), 'error')
               redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)

            traerFase=DBSession.query(Fase).get(id_fase)
            kw['id_fase']=traerFase.id_fase
            kw['id_estado_fase']=traerFase.id_estado_fase
            kw['id_proyecto']=traerFase.id_proyecto
            kw['nombre']=traerFase.nombre
            kw['descripcion']=traerFase.descripcion
            kw['numero_fase']=traerFase.numero_fase
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Edicion de Fases! SQLAlchemyError..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Edicion de Fases! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)

        return dict(nombre_modelo='Fase', page='editar_fase', value=kw)

    @validate(editar_fase_form, error_handler=editar)
    @expose()
    @require(predicates.has_any_permission('lider_proyecto'))
    def update(self, **kw):        
        """Metodo que actualiza la fase en la base de datos"""
        try:
            fase = DBSession.query(Fase).get(kw['id_fase'])
            fase.nombre=kw['nombre']
            fase.numero_fase=kw['numero_fase']
            fase.descripcion = kw['descripcion']
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=kw['id_proyecto'])
        except SQLAlchemyError:
            flash(_("No se han guardado los cambios! SQLAlchemyError..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=kw['id_proyecto'])
        except (AttributeError, NameError):
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=kw['id_proyecto'])
        else:
            flash(_("Se han guardado los cambios!"), 'ok')

        redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=kw['id_proyecto'])

    @expose('is2sap.templates.fase.confirmar_eliminar')
    @require(predicates.has_any_permission('lider_proyecto'))
    def confirmar_eliminar(self, id_proyecto, id_fase, **kw):
        """Despliega confirmacion de eliminacion"""
        try:
            proyecto = DBSession.query(Proyecto).get(id_proyecto)

            if proyecto.iniciado == True:
               flash(_("Proyecto ya iniciado. No puede eliminar fases!"), 'error')
               redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)

            fase = DBSession.query(Fase).get(id_fase)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Eliminacion de Fases! SQLAlchemyError..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Eliminacion de Fases! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)

        return dict(nombre_modelo='Fase', page='eliminar_fase', value=fase)

    @expose()
    @require(predicates.has_any_permission('lider_proyecto'))
    def delete(self, id_proyecto, id_fase, **kw):
        """ Metodo que elimina un registro de la base de datos 
            Parametros:
                       -  id_fase: identificador de la fase
        """
        try:
            tipo_items = DBSession.query(TipoItem).filter_by(id_fase=id_fase).all()

            for tipo_item in tipo_items:
                id_tipo_item = tipo_item.id_tipo_item
                atributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item).all()
                for atributo in atributos:
                    DBSession.delete(DBSession.query(Atributo).get(atributo.id_atributo))
                DBSession.delete(DBSession.query(TipoItem).get(id_tipo_item))

            DBSession.delete(DBSession.query(Fase).get(id_fase))
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha eliminado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)
        except SQLAlchemyError:
            flash(_("No se ha eliminado! SQLAlchemyError..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se ha eliminado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)
        else:
            flash(_("Fase eliminada!"), 'ok')

        redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)
