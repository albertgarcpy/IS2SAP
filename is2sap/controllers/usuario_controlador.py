# -*- coding: utf-8 -*-
"""Controlador de Usuario"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates
from tg import tmpl_context, validate
from webhelpers import paginate

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
        tmpl_context.form = crear_usuario_form
        return dict(nombre_modelo='Usuario', page='nuevo_usuario', value=kw)

    @validate(crear_usuario_form, error_handler=nuevo)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
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
        redirect("/admin/usuario/listado")

    @expose("is2sap.templates.usuario.listado")
    def listado(self,page=1):
        """Metodo para listar todos los usuarios de la base de datos"""
        usuarios = DBSession.query(Usuario).order_by(Usuario.apellido)
        currentPage = paginate.Page(usuarios, page, items_per_page=5)
        return dict(usuarios=currentPage.items,
           page='listado_usuario', currentPage=currentPage)

    @expose('is2sap.templates.usuario.editar')
    def editar(self, id_usuario, **kw):
        """Metodo que rellena el formulario para editar los datos de un usuario"""
        tmpl_context.form = editar_usuario_form
        traerUsuario=DBSession.query(Usuario).get(id_usuario)
        kw['id_usuario']=traerUsuario.id_usuario
        kw['nombre']=traerUsuario.nombre
        kw['apellido']=traerUsuario.apellido
        kw['nombre_usuario']=traerUsuario.nombre_usuario
        #kw['password']=traerUsuario.password
        kw['direccion']=traerUsuario.direccion
        kw['telefono']=traerUsuario.telefono 
        kw['email']=traerUsuario.email
        return dict(nombre_modelo='Usuario', page='editar_usuario', value=kw)

    @validate(editar_usuario_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        usuario = DBSession.query(Usuario).get(kw['id_usuario'])   
        usuario.nombre = kw['nombre']
        usuario.apellido=kw['apellido']
        usuario.nombre_usuario = kw['nombre_usuario']
        #usuario.password = kw['password']
        usuario.direccion =kw['direccion']
        usuario.telefono = kw['telefono']
        usuario.email =kw['email']
        DBSession.flush()
        redirect("/admin/usuario/listado")

    @expose('is2sap.templates.usuario.confirmar_eliminar')
    def confirmar_eliminar(self, id_usuario, **kw):
        """Despliega confirmacion de eliminacion"""
        usuario=DBSession.query(Usuario).get(id_usuario)
        return dict(nombre_modelo='Usuario', page='eliminar_usuario', value=usuario)

    @expose()
    def delete(self, id_usuario, **kw):
        """Metodo que elimina un registro de la base de datos"""
        DBSession.delete(DBSession.query(Usuario).get(id_usuario))
        redirect("/admin/usuario/listado")

    @expose("is2sap.templates.usuario.listar_roles")
    def roles(self,id_usuario, page=1):
        """Metodo para listar todos los roles que tiene el usuario seleccionado"""
        usuario = DBSession.query(Usuario).get(id_usuario)
        roles = usuario.roles
        currentPage = paginate.Page(roles, page, items_per_page=5)
        return dict(roles=currentPage.items,
           page='listar_roles', currentPage=currentPage, usuario=usuario)

    @expose("is2sap.templates.usuario.agregar_roles")
    def rolUsuario(self, id_usuario, page=1):
        """Metodo que permite listar los roles que se pueden agregar al usuario seleccionado"""
        usuario = DBSession.query(Usuario).get(id_usuario)
        rolesUsuario = usuario.roles
        roles = DBSession.query(Rol).all()
        
        for rol in rolesUsuario:
           roles.remove(rol)

        currentPage = paginate.Page(roles, page, items_per_page=5)
        return dict(roles=currentPage.items,
           page='agregar_roles', currentPage=currentPage, 
           id_usuario=id_usuario, usuario=usuario)

    @expose()
    def agregarRol(self, id_usuario, id_rol):
        """Metodo que realiza la agregacion de un rol al usuario selecccionado"""
        rol = DBSession.query(Rol).get(id_rol)
        usuario = DBSession.query(Usuario).get(id_usuario)
        rol.usuarios.append(usuario)
        redirect("/admin/usuario/roles",id_usuario=id_usuario)

    @expose()
    def eliminar_rol_usuario(self, id_usuario, id_rol, **kw):
        """Metodo que elimina un rol al usuario seleccionado"""
        rol = DBSession.query(Rol).get(id_rol)
        usuario = DBSession.query(Usuario).get(id_usuario)
        rol.usuarios.remove(usuario)
        redirect("/admin/usuario/roles",id_usuario=id_usuario)

