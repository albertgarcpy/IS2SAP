# -*- coding: utf-8 -*-
"""Controlador de Proyecto"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates
from tg import tmpl_context, validate
from webhelpers import paginate

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import Proyecto, Usuario, Rol
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController


from is2sap.widgets.proyecto_form import crear_proyecto_form, editar_proyecto_form


__all__ = ['ProyectoController']

class ProyectoController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='Proyecto', page='index_proyecto')        

    @expose('is2sap.templates.proyecto.nuevo')
    def nuevo(self, **kw):
        """Despliega el formulario para añadir un nuevo Proyecto."""
        tmpl_context.form = crear_proyecto_form
        usuario_id= DBSession.query(Usuario.id_usuario).filter_by(nombre_usuario=request.identity['repoze.who.userid']).first()
        kw['id_usuario']=usuario_id
        return dict(nombre_modelo='Proyecto', page='nuevo_proyecto', value=kw)

    @validate(crear_proyecto_form, error_handler=nuevo)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        proyecto = Proyecto()
        proyecto.id_usuario=kw['id_usuario']
        proyecto.nombre = kw['nombre']
        proyecto.descripcion = kw['descripcion']
        proyecto.fecha = kw['fecha']
        proyecto.iniciado = kw['iniciado']
        DBSession.add(proyecto)
        DBSession.flush()    
        redirect("/admin/proyecto/listado")

    @expose("is2sap.templates.proyecto.listado")
    def listado(self,page=1):
        """Metodo para listar todos los Proyectos existentes de la base de datos"""
        proyectos = DBSession.query(Proyecto).order_by(Proyecto.id_proyecto)
        currentPage = paginate.Page(proyectos, page, items_per_page=5)
        return dict(proyectos=currentPage.items,
           page='listado_proyecto', currentPage=currentPage)

    @expose('is2sap.templates.proyecto.editar')
    def editar(self, id_proyecto, **kw):
        """Metodo que rellena el formulario para editar los datos de un Proyecto"""
        tmpl_context.form = editar_proyecto_form
        traerProyecto=DBSession.query(Proyecto).get(id_proyecto)
        kw['id_proyecto']=traerProyecto.id_proyecto
        kw['id_usuario']=traerProyecto.id_usuario
        kw['nombre']=traerProyecto.nombre
        kw['descripcion']=traerProyecto.descripcion
        kw['fecha']=traerProyecto.fecha
        kw['iniciado']=traerProyecto.iniciado
        return dict(nombre_modelo='Proyecto', page='editar_proyecto', value=kw)

    @validate(editar_proyecto_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        proyecto = DBSession.query(Proyecto).get(kw['id_proyecto'])   
        proyecto.id_usuario = kw['id_usuario']
        proyecto.nombre=kw['nombre']
        proyecto.descripcion = kw['descripcion']
        proyecto.fecha = kw['fecha']
        proyecto.inciado =kw['iniciado']
        DBSession.flush()
        redirect("/admin/proyecto/listado")

    @expose('is2sap.templates.proyecto.confirmar_eliminar')
    def confirmar_eliminar(self, id_proyecto, **kw):
        """Despliega confirmacion de eliminacion"""
        proyecto=DBSession.query(Proyecto).get(id_proyecto)
        return dict(nombre_modelo='Proyecto', page='eliminar_proyecto', value=proyecto)

    @expose()
    def delete(self, id_proyecto, **kw):
        """Metodo que elimina un registro de la base de datos"""
        DBSession.delete(DBSession.query(Proyecto).get(id_proyecto))
        redirect("/admin/proyecto/listado")

    @expose("is2sap.templates.proyecto.listar_roles")
    def roles(self,id_proyecto, page=1):
        """Metodo para listar todos los roles que tiene el proyecto seleccionado"""
        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        roles = proyecto.roles
        currentPage = paginate.Page(roles, page, items_per_page=5)
        return dict(roles=currentPage.items,
           page='listar_roles', currentPage=currentPage, proyecto=proyecto)

    @expose("is2sap.templates.proyecto.agregar_roles")
    def rolProyecto(self, id_proyecto, page=1):
        """Metodo que permite listar los roles que se pueden agregar al proyecto seleccionado"""
        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        rolesProyecto = proyecto.roles
        roles = DBSession.query(Rol).all()
        
        for rol in rolesProyecto:
           roles.remove(rol)

        currentPage = paginate.Page(roles, page, items_per_page=5)
        return dict(roles=currentPage.items,
           page='agregar_roles', currentPage=currentPage, 
           id_proyecto=id_proyecto, proyecto=proyecto)

    @expose()
    def agregarRol(self, id_proyecto, id_rol):
        """Metodo que realiza la agregacion de un rol al proyecto selecccionado"""
        rol = DBSession.query(Rol).get(id_rol)
        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        rol.proyectos.append(proyecto)
        redirect("/admin/proyecto/roles",id_proyecto=id_proyecto)

    @expose()
    def eliminar_rol_proyecto(self, id_proyecto, id_rol, **kw):
        """Metodo que elimina un rol al proyecto seleccionado"""
        rol = DBSession.query(Rol).get(id_rol)
        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        rol.proyectos.remove(proyecto)
        redirect("/admin/proyecto/roles",id_proyecto=id_proyecto)

    @expose("is2sap.templates.proyecto.listar_usuarios")
    def usuarios(self,id_proyecto, page=1):
        """Metodo para listar todos los usuarios que tiene el proyecto seleccionado"""
        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        usuarios = proyecto.usuarios
        currentPage = paginate.Page(usuarios, page, items_per_page=5)
        return dict(usuarios=currentPage.items,
           page='listar_usuarios', currentPage=currentPage, proyecto=proyecto)

    @expose("is2sap.templates.proyecto.agregar_usuarios")
    def usuarioProyecto(self, id_proyecto, page=1):
        """Metodo que permite listar los usuarios que se pueden agregar al proyecto seleccionado"""
        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        usuariosProyecto = proyecto.usuarios
        usuarios = DBSession.query(Usuario).all()
        
        for usuario in usuariosProyecto:
           usuarios.remove(usuario)

        currentPage = paginate.Page(usuarios, page, items_per_page=5)
        return dict(usuarios=currentPage.items,
           page='agregar_usuarios', currentPage=currentPage, 
           id_proyecto=id_proyecto, proyecto=proyecto)

    @expose()
    def agregarUsuario(self, id_proyecto, id_usuario):
        """Metodo que realiza la agregacion de un usuario al proyecto selecccionado"""
        usuario = DBSession.query(Usuario).get(id_usuario)
        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        usuario.proyectos.append(proyecto)
        redirect("/admin/proyecto/usuarios",id_proyecto=id_proyecto)

    @expose()
    def eliminar_usuario_proyecto(self, id_proyecto, id_usuario, **kw):
        """Metodo que elimina un usuario al proyecto seleccionado"""
        usuario = DBSession.query(Usuario).get(id_usuario)
        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        usuario.proyectos.remove(proyecto)
        redirect("/admin/proyecto/usuarios",id_proyecto=id_proyecto)


