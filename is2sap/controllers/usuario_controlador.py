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
from is2sap.model.model import Usuario
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController


from is2sap.widgets.usuario_form import crear_usuario_form, editar_usuario_form



__all__ = ['UsuarioController']

class UsuarioController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla de bienvenida"""
        redirect("/admin/usuario/listado")        


    @expose('is2sap.templates.usuario.nuevo')
    def nuevo(self, **kw):
        """Despliega el formulario para añadir un nuevo Usuario."""
        tmpl_context.form = crear_usuario_form
        return dict(nombre_modelo='Usuario', page='nuevo', value=kw)

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
           page='listado', currentPage=currentPage)



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
        return dict(nombre_modelo='Usuario', page='editar', value=kw)


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
