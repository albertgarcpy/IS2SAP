# -*- coding: utf-8 -*-
"""Controlador de Tipo de Item"""

import tg
from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates
from tg import tmpl_context, validate
from webhelpers import paginate
from sqlalchemy.orm import contains_eager
from tw.jquery import TreeView
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import transaction

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import Atributo, TipoItem, Fase, Proyecto
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController
from is2sap.widgets.tipo_item_form import crear_tipo_item_form, editar_tipo_item_form

__all__ = ['TipoItemController']

class TipoItemController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='Tipo de Item', page='index_tipo_item')

    @expose('is2sap.templates.tipo_item.listadoImportar')
    def listadoImportar(self, id_proyecto, id_fase):
        """Metodo para listar los Tipos de Items que se pueden Importar"""
        try:
            listaProyectos=DBSession.query(Proyecto).order_by(Proyecto.id_proyecto)
            for proyecto in listaProyectos:
                for fase in proyecto.fases:
                    for tipoitem in fase.tipoitems:
                        for atributo in tipoitem.atributos:
                            print atributo.nombre
            myTree = TreeView(treeDiv='navTree')
            tmpl_context.form = myTree
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Importacion de Tipo de Item! SQLAlchemyError..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Importacion de Tipo de Item! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)

        return dict(listaProyectos=listaProyectos, id_proyecto=id_proyecto, id_fase=id_fase)

    @expose()
    def importar(self, id_proyecto, id_fase, id_tipo_item, nombre, descripcion, codigo):
        """Metodo que realiza la importacion del Tipo de Item con todos sus Atributos"""
        try:
            tipo_item = TipoItem()
            tipo_item.id_fase = id_fase
            tipo_item.nombre = nombre
            tipo_item.codigo = codigo
            tipo_item.descripcion = descripcion
            DBSession.add(tipo_item)
            DBSession.flush()

            listaAtributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item).all()

            for unAtributo in listaAtributos:
                print unAtributo.nombre
                atributo = Atributo()
                atributo.id_tipo_item = tipo_item.id_tipo_item
                atributo.nombre = unAtributo.nombre
                atributo.descripcion = unAtributo.descripcion   
                atributo.tipo = unAtributo.tipo 
                DBSession.add(atributo)
                DBSession.flush()

            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha realizado la importacion! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        except SQLAlchemyError:
            flash(_("No se ha realizado la importacion! SQLAlchemyError..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se ha realizado la importacion! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        else:
            flash(_("Se ha importado correctamente!"), 'ok')

        redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)

    @expose('is2sap.templates.tipo_item.nuevo')
    def nuevoDesdeFase(self, id_fase, **kw):
        """Despliega el formulario para añadir un Nuevo Tipo de Item a la fase de un proyecto."""
        try:
            tmpl_context.form = crear_tipo_item_form
            fase = DBSession.query(Fase).get(id_fase)
            id_proyecto = fase.id_proyecto
            kw['id_fase'] = id_fase
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Creacion de Tipo de Item! SQLAlchemyError..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Creacon de Tipo de Item! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        
        return dict(nombre_modelo='Tipo Item', page='nuevo_tipo_item', id_proyecto=id_proyecto, id_fase=id_fase, value=kw)

    @expose()
    @validate(crear_tipo_item_form, error_handler=nuevoDesdeFase)
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        try:
            tipo_item = TipoItem()
            tipo_item.id_fase = kw['id_fase']
            tipo_item.nombre = kw['nombre']
            tipo_item.codigo = kw['codigo']
            tipo_item.descripcion = kw['descripcion']
            DBSession.add(tipo_item)
            DBSession.flush()
            transaction.commit()
            fase = DBSession.query(Fase).get(kw['id_fase'])
            id_fase = fase.id_fase
            id_proyecto = fase.id_proyecto
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        except SQLAlchemyError:
            flash(_("No se ha guardado! SQLAlchemyError..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        else:
            flash(_("Tipo de Item creado!"), 'ok')

        redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)

    @expose("is2sap.templates.tipo_item.listadoTipoItemPorFase")
    def listadoTipoItemPorFase(self, id_proyecto, id_fase, page=1):
        """Metodo para listar los Tipos de Items de una Fase """
        try:         
            tipoItemPorFase = DBSession.query(TipoItem).join(TipoItem.relacion_fase).filter(TipoItem.id_fase==id_fase).options(contains_eager(TipoItem.relacion_fase)).order_by(TipoItem.id_tipo_item)
            nombreFase = DBSession.query(Fase.nombre).filter_by(id_fase=id_fase).first()
            idProyectoFase = DBSession.query(Fase.id_proyecto).filter_by(id_fase=id_fase).first()
            currentPage = paginate.Page(tipoItemPorFase, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Tipo de Items de Fase! SQLAlchemyError..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Tipo de Items de Fase! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/fase/listadoFasesPorProyecto", id_proyecto=id_proyecto)

        return dict(tipoItemPorFase=currentPage.items, page='listado', 
                    nombre_fase=nombreFase, id_proyecto=id_proyecto, id_fase=id_fase, currentPage=currentPage)

    @expose('is2sap.templates.tipo_item.editar')
    def editar(self, id_tipo_item, **kw):
        """Metodo que rellena el formulario para editar los datos de un usuario"""
        try:
            tmpl_context.form = editar_tipo_item_form
            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
            id_fase = tipo_item.id_fase
            fase = DBSession.query(Fase).get(id_fase)
            id_proyecto = fase.id_proyecto
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            
            if proyecto.iniciado == True:
               flash(_("Proyecto ya iniciado. No puede editar Tipo de Item!"), 'error')
               redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)

            traertipo_item = DBSession.query(TipoItem).get(id_tipo_item)
            kw['id_tipo_item'] = traertipo_item.id_tipo_item
            kw['nombre'] = traertipo_item.nombre
            kw['codigo'] = traertipo_item.codigo
            kw['descripcion'] = traertipo_item.descripcion
            kw['id_fase'] = traertipo_item.id_fase
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Edicion de Tipo de Item! SQLAlchemyError..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Edicion de Tipo de Item! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        
        return dict(nombre_modelo='Tipo Item', id_proyecto=id_proyecto, id_fase=id_fase, page='editar', value=kw)

    @validate(editar_tipo_item_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        try:
            tipo_item = DBSession.query(TipoItem).get(kw['id_tipo_item'])   
            tipo_item.nombre = kw['nombre']
            tipo_item.codigo = kw['codigo']
            tipo_item.descripcion = kw['descripcion']
            tipo_item.id_fase = kw['id_fase']
            DBSession.flush()
            transaction.commit()
            fase = DBSession.query(Fase).get(kw['id_fase'])
            id_fase = fase.id_fase
            id_proyecto = fase.id_proyecto
        except IntegrityError:
            transaction.abort()
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        except SQLAlchemyError:
            flash(_("No se han guardado los cambios! SQLAlchemyError..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        else:
            flash(_("Se han guardado los cambios!"), 'ok')

        redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)

    @expose('is2sap.templates.tipo_item.confirmar_eliminar')
    def confirmar_eliminar(self, id_proyecto, id_fase, id_tipo_item, **kw):
        """Despliega confirmacion de eliminacion"""
        try:
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            if proyecto.iniciado == True:
               flash(_("Proyecto ya iniciado. No puede eliminar Tipo de Item!"), 'error')
               redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)

            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Edicion de Tipo de Item! SQLAlchemyError..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Edicion de Tipo de Item! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)

        return dict(nombre_modelo='Tipo Item', page='editar', id_proyecto=id_proyecto, id_fase=id_fase, value=tipo_item)

    @expose()
    def delete(self, id_proyecto, id_fase, id_tipo_item, **kw):
        """Metodo que elimina un registro de la base de datos"""
        try:
            atributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item).all()

            for atributo in atributos:
                DBSession.delete(DBSession.query(Atributo).get(atributo.id_atributo))

            DBSession.delete(DBSession.query(TipoItem).get(id_tipo_item))
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha eliminado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        except SQLAlchemyError:
            flash(_("No se ha eliminado! SQLAlchemyError..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se ha eliminado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
        else:
            flash(_("Tipo de Item eliminado!"), 'ok')

        redirect("/admin/tipo_item/listadoTipoItemPorFase", id_proyecto=id_proyecto, id_fase=id_fase)
