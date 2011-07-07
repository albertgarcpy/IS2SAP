# -*- coding: utf-8 -*-
"""Controlador de Atributo"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates
from tg import tmpl_context, validate
from webhelpers import paginate
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import transaction

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import Proyecto, TipoItem, Atributo, Fase
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController
from is2sap.widgets.atributo_form import crear_atributo_form, editar_atributo_form

__all__ = ['AtributoController']

class AtributoController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='Atributo', page='index_atributo')        

    @expose('is2sap.templates.atributo.nuevoDesdeTipoItem')
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def nuevoDesdeTipoItem(self, id_tipo_item, **kw):
        """Despliega el formulario para añadir un nuevo atributo."""
        try:
            tmpl_context.form = crear_atributo_form
            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
            id_fase = tipo_item.id_fase
            fase = DBSession.query(Fase).get(id_fase)
            id_proyecto = fase.id_proyecto
            kw['id_tipo_item']=id_tipo_item
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Creacion de Atributo! SQLAlchemyError..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Creacon de Atributo! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)

        return dict(nombre_modelo='Atributo', page='nuevo_atributo', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, value=kw)

    @validate(crear_atributo_form, error_handler=nuevoDesdeTipoItem)
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        try:
            atributo = Atributo()
            atributo.id_tipo_item = kw['id_tipo_item']
            atributo.nombre = kw['nombre']
            atributo.descripcion = kw['descripcion']
            atributo.tipo = kw['tipo']
            DBSession.add(atributo)
            DBSession.flush()
            transaction.commit()
            tipo_item = DBSession.query(TipoItem).get(kw['id_tipo_item'])
            id_tipo_item = tipo_item.id_tipo_item
            fase = tipo_item.relacion_fase
            id_fase = fase.id_fase
            id_proyecto = fase.id_proyecto
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)
        except SQLAlchemyError:
            flash(_("No se ha guardado! SQLAlchemyError..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)
        else:
            flash(_("Atributo creado!"), 'ok')

        redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                 id_fase=id_fase, id_tipo_item=id_tipo_item)

    @expose("is2sap.templates.atributo.listadoAtributosPorTipoItem")
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def listadoAtributosPorTipoItem(self, id_proyecto, id_fase, id_tipo_item, page=1):
        """Metodo para listar todos los atributos de la base de datos"""
        try:
            atributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item).order_by(Atributo.id_atributo)
            currentPage = paginate.Page(atributos, page, items_per_page=10)
            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Atributos de Tipo de Item! SQLAlchemyError..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Atributos de Tipo de Item! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)

        return dict(atributos=currentPage.items,page='listado_atributos', nombre_tipo_item=tipo_item.nombre, 
                    id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, currentPage=currentPage)

    @expose('is2sap.templates.atributo.editar')
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def editar(self, id_atributo, **kw):
        """Metodo que rellena el formulario para editar los datos de un usuario"""
        try:
            tmpl_context.form = editar_atributo_form
            traerAtributo = DBSession.query(Atributo).get(id_atributo)
            id_tipo_item = traerAtributo.id_tipo_item
            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
            id_fase = tipo_item.id_fase
            fase = DBSession.query(Fase).get(id_fase)
            id_proyecto = fase.id_proyecto
            proyecto = DBSession.query(Proyecto).get(id_proyecto)

            if proyecto.iniciado == True:
               flash(_("Proyecto ya iniciado. No puede editar Atributo!"), 'error')
               redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                        id_fase=id_fase, id_tipo_item=id_tipo_item)

            kw['id_atributo']=traerAtributo.id_atributo
            kw['id_tipo_item']=traerAtributo.id_tipo_item
            kw['nombre']=traerAtributo.nombre
            kw['descripcion']=traerAtributo.descripcion
            kw['tipo']=traerAtributo.tipo
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Edicion de Atributo! SQLAlchemyError..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Edicion de Atributo! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)

        return dict(nombre_modelo='Atributo', page='editar', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, value=kw)

    @validate(editar_atributo_form, error_handler=editar)
    @expose()
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        try:
            atributo = DBSession.query(Atributo).get(kw['id_atributo'])   
            atributo.id_tipo_item = kw['id_tipo_item']
            atributo.nombre=kw['nombre']
            atributo.descripcion = kw['descripcion']
            atributo.tipo = kw['tipo']
            DBSession.flush()
            transaction.commit()
            tipo_item = DBSession.query(TipoItem).get(kw['id_tipo_item'])
            id_tipo_item = tipo_item.id_tipo_item
            fase = tipo_item.relacion_fase
            id_fase = fase.id_fase        
            id_proyecto = fase.id_proyecto
        except IntegrityError:
            transaction.abort()
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)
        except SQLAlchemyError:
            flash(_("No se han guardado los cambios! SQLAlchemyError..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)
        else:
            flash(_("Se han guardado los cambios!"), 'ok')

        redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                 id_fase=fase.id_fase, id_tipo_item=id_tipo_item)

    @expose('is2sap.templates.atributo.confirmar_eliminar')
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def confirmar_eliminar(self, id_proyecto, id_fase, id_tipo_item, id_atributo, **kw):
        """Despliega confirmacion de eliminacion"""
        try:
            proyecto = DBSession.query(Proyecto).get(id_proyecto)

            if proyecto.iniciado == True:
               flash(_("Proyecto ya iniciado. No puede eliminar Atributo!"), 'error')
               redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                        id_fase=id_fase, id_tipo_item=id_tipo_item)

            atributo = DBSession.query(Atributo).get(id_atributo)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Eliminacion de Atributo! SQLAlchemyError..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Eliminacion de Atributo! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)

        return dict(nombre_modelo='Atributo', page='editar', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, value=atributo)

    @expose()
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def delete(self, id_proyecto, id_fase, id_tipo_item, id_atributo, **kw):
        """ Metodo que elimina el registro de un atributo
            Parametros: - id_atributo: Para identificar el atributo a eliminar
                        - id_tipo_item: Para redireccionar al listado de atributos correspondientes al tipo de item 
        """
        try:
            DBSession.delete(DBSession.query(Atributo).get(id_atributo))
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha eliminado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)
        except SQLAlchemyError:
            flash(_("No se ha eliminado! SQLAlchemyError..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se ha eliminado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                     id_fase=id_fase, id_tipo_item=id_tipo_item)
        else:
            flash(_("Atributo eliminado!"), 'ok')

        redirect("/admin/atributo/listadoAtributosPorTipoItem", id_proyecto=id_proyecto, 
                 id_fase=id_fase, id_tipo_item=id_tipo_item)
