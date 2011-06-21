# -*- coding: utf-8 -*-
"""Controlador de Usuario"""

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
from is2sap.model.model import Usuario, Rol, Rol_Usuario
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController
from is2sap.widgets.usuario_form import crear_usuario_form, editar_usuario_form

__all__ = ['UsuarioController']

class UsuarioController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='Usuario', page='index_usuario')        

    @expose('is2sap.templates.usuario.nuevo')
    def nuevo(self, **kw):
        """Despliega el formulario para añadir un nuevo Usuario."""
        try:
            tmpl_context.form = crear_usuario_form
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Creacion de Usuarios! SQLAlchemyError..."), 'error')
            redirect("/admin/usuario/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Creacion de Usuarios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/listado")

        return dict(nombre_modelo='Usuario', page='nuevo_usuario', value=kw)

    @validate(crear_usuario_form, error_handler=nuevo)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        try:
            usuario = Usuario()
            usuario.nombre = kw['nombre']
            usuario.apellido = kw['apellido']
            usuario.nombre_usuario = kw['nombre_usuario']
            usuario.password = kw['password']
            usuario.direccion = kw['direccion']
            usuario.telefono = kw['telefono']
            usuario.email = kw['email']
            DBSession.add(usuario)
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/listado")
        except SQLAlchemyError:
            flash(_("No se ha guardado! SQLAlchemyError..."), 'error')
            redirect("/admin/usuario/listado")
        except (AttributeError, NameError):
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/listado")
        else:
            flash(_("Usuario creado!"), 'ok')
    
        redirect("/admin/usuario/listado")

    @expose("is2sap.templates.usuario.listado")
    def listado(self,page=1):
        """Metodo para listar todos los usuarios de la base de datos"""
        try:
            usuarios = DBSession.query(Usuario).order_by(Usuario.apellido)
            currentPage = paginate.Page(usuarios, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Usuarios! SQLAlchemyError..."), 'error')
            redirect("/admin")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Usuarios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin")

        return dict(usuarios=currentPage.items, page='listado_usuario', currentPage=currentPage)

    @expose('is2sap.templates.usuario.editar')
    def editar(self, id_usuario, **kw):
        """Metodo que rellena el formulario para editar los datos de un usuario"""
        try:
            tmpl_context.form = editar_usuario_form
            traerUsuario = DBSession.query(Usuario).get(id_usuario)
            kw['id_usuario'] = traerUsuario.id_usuario
            kw['nombre'] = traerUsuario.nombre
            kw['apellido'] = traerUsuario.apellido
            kw['nombre_usuario'] = traerUsuario.nombre_usuario
            kw['direccion'] = traerUsuario.direccion
            kw['telefono'] = traerUsuario.telefono 
            kw['email'] = traerUsuario.email
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Edicion de Usuarios! SQLAlchemyError..."), 'error')
            redirect("/admin/usuario/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Edicion de Usuarios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/listado")

        return dict(nombre_modelo='Usuario', page='editar_usuario', value=kw)

    @validate(editar_usuario_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        try:
            usuario = DBSession.query(Usuario).get(kw['id_usuario'])   
            usuario.nombre = kw['nombre']
            usuario.apellido = kw['apellido']
            usuario.nombre_usuario = kw['nombre_usuario']
            usuario.direccion =kw['direccion']
            usuario.telefono = kw['telefono']
            usuario.email = kw['email']
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/listado")
        except SQLAlchemyError:
            flash(_("No se han guardado los cambios! SQLAlchemyError..."), 'error')
            redirect("/admin/usuario/listado")
        except (AttributeError, NameError):
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/listado")
        else:
            flash(_("Se han guardado los cambios!"), 'ok')

        redirect("/admin/usuario/listado")

    @expose('is2sap.templates.usuario.confirmar_eliminar')
    def confirmar_eliminar(self, id_usuario, **kw):
        """Despliega confirmacion de eliminacion"""
        try:
            usuario=DBSession.query(Usuario).get(id_usuario)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Eliminacion de Usuarios! SQLAlchemyError..."), 'error')
            redirect("/admin/usuario/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Eliminacion de Usuarios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/listado")

        return dict(nombre_modelo='Usuario', page='eliminar_usuario', value=usuario)

    @expose()
    def delete(self, id_usuario, **kw):
        """Metodo que elimina un registro de la base de datos"""
        try:
            DBSession.delete(DBSession.query(Usuario).get(id_usuario))
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha eliminado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/listado")
        except SQLAlchemyError:
            flash(_("No se ha eliminado! SQLAlchemyError..."), 'error')
            redirect("/admin/usuario/listado")
        except (AttributeError, NameError):
            flash(_("No se ha eliminado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/listado")
        else:
            flash(_("Usuario eliminado!"), 'ok')

        redirect("/admin/usuario/listado")

    @expose("is2sap.templates.usuario.listar_roles")
    def roles(self,id_usuario, page=1):
        """Metodo para listar todos los roles que tiene el usuario seleccionado"""
        try:
            usuario = DBSession.query(Usuario).get(id_usuario)
            roles = usuario.roles
            currentPage = paginate.Page(roles, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Roles de Usuario! SQLAlchemyError..."), 'error')
            redirect("/admin/usuario/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Roles de Usuario! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/listado")

        return dict(roles=currentPage.items, page='listar_roles', currentPage=currentPage, usuario=usuario)

    @expose()
    def eliminar_rol_usuario(self, id_usuario, id_rol, **kw):
        """Metodo que elimina un rol al usuario seleccionado"""
        try:
            rol = DBSession.query(Rol).get(id_rol)
            usuario = DBSession.query(Usuario).get(id_usuario)
            rol.usuarios.remove(usuario)
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se pudo Desasignar Rol! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/roles", id_usuario=id_usuario)
        except SQLAlchemyError:
            flash(_("No se pudo Desasignar Rol! SQLAlchemyError..."), 'error')
            redirect("/admin/usuario/roles", id_usuario=id_usuario)
        except (AttributeError, NameError):
            flash(_("No se pudo Desasignar Rol! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/roles", id_usuario=id_usuario)
        else:
            flash(_("Rol desasignado!"), 'ok')

        redirect("/admin/usuario/roles", id_usuario=id_usuario)

    @expose("is2sap.templates.usuario.agregar_roles")
    def rolUsuario(self, id_usuario, page=1):
        """Metodo que permite listar los roles que se pueden agregar al usuario seleccionado"""
        try:
            usuario = DBSession.query(Usuario).get(id_usuario)
            rolesUsuario = usuario.roles
            roles = DBSession.query(Rol).all()
        
            for rol in rolesUsuario:
                roles.remove(rol)

            currentPage = paginate.Page(roles, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Agregar Roles! SQLAlchemyError..."), 'error')
            redirect("/admin/usuario/roles", id_usuario=id_usuario)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Agregar Roles! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/roles", id_usuario=id_usuario)

        return dict(roles=currentPage.items, page='agregar_roles', currentPage=currentPage, 
                    id_usuario=id_usuario, usuario=usuario)

    @expose()
    def agregarRol(self, id_usuario, id_rol):
        """Metodo que realiza la agregacion de un rol al usuario selecccionado"""
        try:
            rol = DBSession.query(Rol).get(id_rol)
            usuario = DBSession.query(Usuario).get(id_usuario)
            rol.usuarios.append(usuario)
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se pudo Asignar Rol! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/rolUsuario", id_usuario=id_usuario)
        except SQLAlchemyError:
            flash(_("No se pudo Asignar Rol! SQLAlchemyError..."), 'error')
            redirect("/admin/usuario/rolUsuario", id_usuario=id_usuario)
        except (AttributeError, NameError):
            flash(_("No se pudo Asignar Rol! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/usuario/rolUsuario", id_usuario=id_usuario)
        else:
            flash(_("Rol asignado!"), 'ok')

        redirect("/admin/usuario/rolUsuario",id_usuario=id_usuario)
