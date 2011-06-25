# -*- coding: utf-8 -*-
"""Controlador de Rol"""

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
from is2sap.model.model import Rol, Permiso
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController
from is2sap.widgets.rol_form import crear_rol_form, editar_rol_form

__all__ = ['RolController']

class RolController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='Rol', page='index_rol')      

    @expose('is2sap.templates.rol.nuevo')
    @require(predicates.has_permission('administracion',  msg=l_('Solo para el Administrador')))
    def nuevo(self, **kw):
        """Despliega el formulario para añadir un nuevo Rol."""
        try:
            tmpl_context.form = crear_rol_form
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Creacion de Roles! SQLAlchemyError..."), 'error')
            redirect("/admin/rol/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Creacion de Roles! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/listado")

        return dict(nombre_modelo='Rol', page='nuevo_rol', value=kw)

    @validate(crear_rol_form, error_handler=nuevo)
    @expose()
    @require(predicates.has_permission('administracion',  msg=l_('Solo para el Administrador')))
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        try:
            rol = Rol()
            rol.tipo = kw['tipo']
            rol.nombre_rol = kw['nombre_rol']
            rol.descripcion = kw['descripcion']
            DBSession.add(rol)
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/listado")
        except SQLAlchemyError:
            flash(_("No se ha guardado! SQLAlchemyError..."), 'error')
            redirect("/admin/rol/listado")
        except (AttributeError, NameError):
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/listado")
        else:
            flash(_("Rol creado!"), 'ok')

        redirect("/admin/rol/listado")

    @expose("is2sap.templates.rol.listado")
    @require(predicates.has_any_permission('administracion', 'lider_proyecto',))
    def listado(self,page=1):
        """Metodo para listar todos los Roles existentes de la base de datos"""
        try:
            roles = DBSession.query(Rol).order_by(Rol.id_rol)
            currentPage = paginate.Page(roles, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Roles! SQLAlchemyError..."), 'error')
            redirect("/admin")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Roles! Hay Problemas con el servidor..."), 'error')
            redirect("/admin")

        return dict(roles=currentPage.items, page='listado_rol', currentPage=currentPage)

    @expose('is2sap.templates.rol.editar')
    @require(predicates.has_permission('administracion',  msg=l_('Solo para el Administrador')))
    def editar(self, id_rol, **kw):
        """Metodo que rellena el formulario para editar los datos de un Rol"""
        try:
            tmpl_context.form = editar_rol_form
            traerRol = DBSession.query(Rol).get(id_rol)
            kw['id_rol'] = traerRol.id_rol
            kw['tipo'] = traerRol.tipo
            kw['nombre_rol'] = traerRol.nombre_rol
            kw['descripcion'] = traerRol.descripcion
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Edicion de Roles! SQLAlchemyError..."), 'error')
            redirect("/admin/rol/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Edicion de Roles! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/listado")

        return dict(nombre_modelo='Rol', page='editar_rol', value=traerRol)

    @validate(editar_rol_form, error_handler=editar)
    @expose()
    @require(predicates.has_permission('administracion',  msg=l_('Solo para el Administrador')))
    def update(self, **kw):        
        """Metodo que actualizar la base de datos"""
        try:
            rol = DBSession.query(Rol).get(kw['id_rol'])   
            rol.tipo=kw['tipo']
            rol.nombre_rol=kw['nombre_rol']
            rol.descripcion = kw['descripcion']
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/listado")
        except SQLAlchemyError:
            flash(_("No se han guardado los cambios! SQLAlchemyError..."), 'error')
            redirect("/admin/rol/listado")
        except (AttributeError, NameError):
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/listado")
        else:
            flash(_("Se han guardado los cambios!"), 'ok')

        redirect("/admin/rol/listado")

    @expose('is2sap.templates.rol.confirmar_eliminar')
    @require(predicates.has_permission('administracion',  msg=l_('Solo para el Administrador')))
    def confirmar_eliminar(self, id_rol, **kw):
        """Despliega confirmacion de eliminacion"""
        try:
            rol=DBSession.query(Rol).get(id_rol)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Eliminacion de Roles! SQLAlchemyError..."), 'error')
            redirect("/admin/rol/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Eliminacion de Roles! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/listado")

        return dict(nombre_modelo='Rol', page='eliminar_rol', value=rol)

    @expose()
    @require(predicates.has_permission('administracion',  msg=l_('Solo para el Administrador')))
    def delete(self, id_rol, **kw):
        """Metodo que elimina un registro de la base de datos"""
        try:
            DBSession.delete(DBSession.query(Rol).get(id_rol))
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha eliminado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/listado")
        except SQLAlchemyError:
            flash(_("No se ha eliminado! SQLAlchemyError..."), 'error')
            redirect("/admin/rol/listado")
        except (AttributeError, NameError):
            flash(_("No se ha eliminado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/listado")
        else:
            flash(_("Rol eliminado!"), 'ok')

        redirect("/admin/rol/listado")

    @expose("is2sap.templates.rol.listar_permisos")
    @require(predicates.has_permission('administracion',  msg=l_('Solo para el Administrador')))
    def permisos(self, id_rol, page=1):
        """Metodo para listar todos los permisos que tiene el rol seleccionado"""
        try:
            rol = DBSession.query(Rol).get(id_rol)
            permisos = rol.permisos
            currentPage = paginate.Page(permisos, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Permisos de Roles! SQLAlchemyError..."), 'error')
            redirect("/admin/rol/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Permisos de Roles! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/listado")

        return dict(permisos=currentPage.items, page='listar_permisos', currentPage=currentPage, rol=rol)

    @expose()
    @require(predicates.has_permission('administracion',  msg=l_('Solo para el Administrador')))
    def eliminar_rol_permiso(self, id_rol, id_permiso, **kw):
        """Metodo que elimina un permiso al rol seleccionado"""
        try:
            permiso = DBSession.query(Permiso).get(id_permiso)
            rol = DBSession.query(Rol).get(id_rol)
            permiso.roles.remove(rol)
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se pudo desasignar el Permiso! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/permisos", id_rol=id_rol)
        except SQLAlchemyError:
            flash(_("No se pudo desasignar el Permiso! SQLAlchemyError..."), 'error')
            redirect("/admin/rol/permisos", id_rol=id_rol)
        except (AttributeError, NameError):
            flash(_("No se pudo desasignar el Permiso! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/permisos", id_rol=id_rol)
        else:
            flash(_("Permiso desasignado!"), 'ok')

        redirect("/admin/rol/permisos", id_rol=id_rol)

    @expose("is2sap.templates.rol.agregar_permisos")
    @require(predicates.has_permission('administracion',  msg=l_('Solo para el Administrador')))
    def rolPermiso(self, id_rol, page=1):
        """Metodo que permite listar los permisos que se pueden agregar al rol seleccionado"""
        try:
            rol = DBSession.query(Rol).get(id_rol)
            permisosRol = rol.permisos
            permisos = DBSession.query(Permiso).all()
        
            for permiso in permisosRol:
                permisos.remove(permiso)

            currentPage = paginate.Page(permisos, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Asignar Permisos! SQLAlchemyError..."), 'error')
            redirect("/admin/rol/permisos", id_rol=id_rol)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Asignar Permisos! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/permisos", id_rol=id_rol)

        return dict(permisos=currentPage.items, page='agregar_permisos', 
                    currentPage=currentPage, id_rol=id_rol, rol=rol)

    @expose()
    @require(predicates.has_permission('administracion',  msg=l_('Solo para el Administrador')))
    def agregarPermiso(self, id_rol, id_permiso):
        """Metodo que realiza la agregacion de un permiso al rol selecccionado"""
        try:
            permiso = DBSession.query(Permiso).get(id_permiso)
            rol = DBSession.query(Rol).get(id_rol)
            permiso.roles.append(rol)
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se pudo asignar el Permiso! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/rolPermiso",id_rol=id_rol)
        except SQLAlchemyError:
            flash(_("No se pudo asignar el Permiso! SQLAlchemyError..."), 'error')
            redirect("/admin/rol/rolPermiso",id_rol=id_rol)
        except (AttributeError, NameError):
            flash(_("No se pudo asignar el Permiso! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/rol/rolPermiso",id_rol=id_rol)
        else:
            flash(_("Permiso asignado!"), 'ok')

        redirect("/admin/rol/rolPermiso",id_rol=id_rol)
