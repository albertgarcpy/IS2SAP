# -*- coding: utf-8 -*-
"""Controlador de Proyecto"""

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
from is2sap.model.model import Proyecto, Usuario, Rol, Fase, TipoItem, Atributo 
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
    @require(predicates.has_any_permission('administracion'))
    def nuevo(self, **kw):
        """Despliega el formulario para añadir un nuevo Proyecto."""
        try:
            tmpl_context.form = crear_proyecto_form
            usuario_id = DBSession.query(Usuario.id_usuario).filter_by(nombre_usuario=request.identity['repoze.who.userid']).first()
            kw['id_usuario']=usuario_id
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Creacion de Proyectos! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Creacion de Proyecto! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listado")

        return dict(nombre_modelo='Proyecto', page='nuevo_proyecto', value=kw)

    @validate(crear_proyecto_form, error_handler=nuevo)
    @expose()
    @require(predicates.has_any_permission('administracion'))
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        try:
            proyecto = Proyecto()
            proyecto.id_usuario=kw['id_usuario']
            proyecto.nombre = kw['nombre']
            proyecto.descripcion = kw['descripcion']
            proyecto.fecha = kw['fecha']
            proyecto.iniciado = kw['iniciado']
            DBSession.add(proyecto)
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listado")
        except SQLAlchemyError:
            flash(_("No se ha guardado! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/listado")
        except (AttributeError, NameError):
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listado")
        else:
            flash(_("Proyecto creado!"), 'ok')
    
        redirect("/admin/proyecto/listado")

    @expose("is2sap.templates.proyecto.listado")
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def listado(self,page=1):
        """Metodo para listar todos los Proyectos existentes de la base de datos"""
        try:
            proyectos=[]
            if predicates.has_permission('administracion'):
                proyectos = DBSession.query(Proyecto).order_by(Proyecto.id_proyecto)
            elif predicates.has_permission('lider_proyecto'):
                usuario = DBSession.query(Usuario).filter_by(nombre_usuario=request.identity['repoze.who.userid']).first()
                proyectos = usuario.proyectos
            currentPage = paginate.Page(proyectos, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Proyectos! SQLAlchemyError..."), 'error')
            redirect("/admin")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Proyectos! Hay Problemas con el servidor..."), 'error')
            redirect("/admin")

        return dict(proyectos=currentPage.items, page='listado_proyecto', currentPage=currentPage)

    @expose('is2sap.templates.proyecto.editar')
    @require(predicates.has_any_permission('administracion'))
    def editar(self, id_proyecto, **kw):
        """Metodo que rellena el formulario para editar los datos de un Proyecto"""
        try:
            tmpl_context.form = editar_proyecto_form       
            traerProyecto=DBSession.query(Proyecto).get(id_proyecto)

            if traerProyecto.iniciado:
               flash(_("El proyecto no puede modificarse porque ya se encuentra iniciado."), 'error')
               redirect("/admin/proyecto/listado")

            kw['id_proyecto']=traerProyecto.id_proyecto
            kw['id_usuario']=traerProyecto.id_usuario
            kw['nombre']=traerProyecto.nombre
            kw['descripcion']=traerProyecto.descripcion
            kw['fecha']=traerProyecto.fecha
            kw['iniciado']=traerProyecto.iniciado
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Edicion de Proyectos! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Edicion de Proyecto! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listado")

        return dict(nombre_modelo='Proyecto', page='editar_proyecto', value=kw)

    @validate(editar_proyecto_form, error_handler=editar)
    @expose()
    @require(predicates.has_any_permission('administracion'))
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""
        try:
            proyecto = DBSession.query(Proyecto).get(kw['id_proyecto'])   
            proyecto.id_usuario = kw['id_usuario']
            proyecto.nombre=kw['nombre']
            proyecto.descripcion = kw['descripcion']
            proyecto.fecha = kw['fecha']
            proyecto.inciado =kw['iniciado']
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listado")
        except SQLAlchemyError:
            flash(_("No se han guardado los cambios! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/listado")
        except (AttributeError, NameError):
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listado")
        else:
            flash(_("Se han guardado los cambios!"), 'ok')

        redirect("/admin/proyecto/listado")

    @expose('is2sap.templates.proyecto.confirmar_eliminar')
    @require(predicates.has_any_permission('administracion'))
    def confirmar_eliminar(self, id_proyecto, **kw):
        """Despliega confirmacion de eliminacion"""
        try:
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            if proyecto.iniciado == True:
               flash(_("Proyecto ya iniciado. No puede eliminar!"), 'error')
               redirect("/admin/proyecto/listado")
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Eliminacion de Proyecto! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Eliminacion de Proyecto! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listado")

        return dict(nombre_modelo='Proyecto', page='eliminar_proyecto', value=proyecto)

    @expose()
    @require(predicates.has_any_permission('administracion'))
    def delete(self, id_proyecto, **kw):
        """Metodo que elimina un registro de la base de datos"""
        try:
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            fases = proyecto.fases

            for fase in fases:
                id_fase = fase.id_fase
                tipo_items = DBSession.query(TipoItem).filter_by(id_fase=id_fase).all()
                for tipo_item in tipo_items:
                    id_tipo_item = tipo_item.id_tipo_item
                    atributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item).all()
                    for atributo in atributos:
                        DBSession.delete(DBSession.query(Atributo).get(atributo.id_atributo))
                    DBSession.delete(DBSession.query(TipoItem).get(id_tipo_item))
                DBSession.delete(DBSession.query(Fase).get(id_fase))

            DBSession.delete(DBSession.query(Proyecto).get(id_proyecto))
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se pudo eliminar! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listado")
        except SQLAlchemyError:
            flash(_("No se pudo eliminar! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo eliminar! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listado")
        else:
            flash(_("Proyecto eliminado!"), 'ok')

        redirect("/admin/proyecto/listado")

    @expose("is2sap.templates.proyecto.listar_roles")
    @require(predicates.has_any_permission('lider_proyecto'))
    def roles(self,id_proyecto, page=1):
        """Metodo para listar todos los roles que tiene el proyecto seleccionado"""
        try:
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            id_proyecto = proyecto.id_proyecto
            roles = proyecto.roles
            currentPage = paginate.Page(roles, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Roles del Proyecto! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Roles del Proyecto! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listado")

        return dict(roles=currentPage.items, page='listar_roles', 
                    currentPage=currentPage, id_proyecto=id_proyecto, proyecto=proyecto)

    @expose()
    @require(predicates.has_any_permission('lider_proyecto'))
    def eliminar_rol_proyecto(self, id_proyecto, id_rol, **kw):
        """Metodo que elimina un rol al proyecto seleccionado"""
        try:
            rol = DBSession.query(Rol).get(id_rol)
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            rol.proyectos.remove(proyecto)
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha desasignado dicho Rol! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/roles",id_proyecto=id_proyecto)
        except SQLAlchemyError:
            flash(_("No se ha desasignado dicho Rol! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/roles",id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se ha desasignado decho Rol! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/roles",id_proyecto=id_proyecto)
        else:
            flash(_("Rol desasignado!"), 'ok')

        redirect("/admin/proyecto/roles",id_proyecto=id_proyecto)

    @expose("is2sap.templates.proyecto.agregar_roles")
    @require(predicates.has_any_permission('lider_proyecto'))
    def rolProyecto(self, id_proyecto, page=1):
        """Metodo que permite listar los roles que se pueden agregar al proyecto seleccionado"""
        try:
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            id_proyecto = proyecto.id_proyecto
            rolesProyecto = proyecto.roles
            roles = DBSession.query(Rol).filter_by(tipo="Proyecto").order_by(Rol.id_rol).all()
        
            for rol in rolesProyecto:
                if roles.count(rol) == 1:               
                    roles.remove(rol)

            currentPage = paginate.Page(roles, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Agregar Roles al Proyecto! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/roles",id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Agregar Roles al Proyecto! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/roles",id_proyecto=id_proyecto)

        return dict(roles=currentPage.items,
           page='agregar_roles', currentPage=currentPage, 
           id_proyecto=id_proyecto, proyecto=proyecto)

    @expose()
    @require(predicates.has_any_permission('lider_proyecto'))
    def agregarRol(self, id_proyecto, id_rol):
        """Metodo que realiza la agregacion de un rol al proyecto selecccionado"""
        try:
            rol = DBSession.query(Rol).get(id_rol)
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            rol.proyectos.append(proyecto)
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha asignado dicho Rol! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/rolProyecto",id_proyecto=id_proyecto)
        except SQLAlchemyError:
            flash(_("No se ha asignado dicho Rol! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/rolProyecto",id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se ha asignado decho Rol! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/rolProyecto",id_proyecto=id_proyecto)
        else:
            flash(_("Rol asignado!"), 'ok')

        redirect("/admin/proyecto/rolProyecto",id_proyecto=id_proyecto)

    @expose("is2sap.templates.proyecto.listar_usuarios")
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def usuarios(self,id_proyecto, page=1):
        """Metodo para listar todos los usuarios que tiene el proyecto seleccionado"""
        try:
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            id_proyecto = proyecto.id_proyecto
            usuarios = proyecto.usuarios
            currentPage = paginate.Page(usuarios, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Usuarios del Proyecto! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/listado")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Usuarios del Proyecto! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listado")

        return dict(usuarios=currentPage.items,
           page='listar_usuarios', id_proyecto=id_proyecto, currentPage=currentPage, proyecto=proyecto)


    @expose()
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def eliminar_usuario_proyecto(self, id_proyecto, id_usuario, **kw):
        """Metodo que elimina un usuario al proyecto seleccionado"""
        try:
            usuario = DBSession.query(Usuario).get(id_usuario)
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            usuario.proyectos.remove(proyecto)
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha desasignado dicho Usuario! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/usuarios", id_proyecto=id_proyecto)
        except SQLAlchemyError:
            flash(_("No se ha desasignado dicho Usuario! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/usuarios", id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se ha desasignado decho Usuario! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/usuarios", id_proyecto=id_proyecto)
        else:
            flash(_("Usuario desasignado!"), 'ok')

        redirect("/admin/proyecto/usuarios", id_proyecto=id_proyecto)

    @expose("is2sap.templates.proyecto.agregar_usuarios")
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def usuarioProyecto(self, id_proyecto, page=1):
        """Metodo que permite listar los usuarios que se pueden agregar al proyecto seleccionado"""
        try:
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            id_proyecto = proyecto.id_proyecto
            usuariosProyecto = proyecto.usuarios
            usuarios = DBSession.query(Usuario).order_by(Usuario.id_usuario).all()
        
            for usuario in usuariosProyecto:
               usuarios.remove(usuario)

            currentPage = paginate.Page(usuarios, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Agregar Usuarios al Proyecto! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/usuarios", id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Agregar Usuarios al Proyecto! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/usuarios", id_proyecto=id_proyecto)

        return dict(usuarios=currentPage.items, page='agregar_usuarios', 
                    currentPage=currentPage, id_proyecto=id_proyecto, proyecto=proyecto)

    @expose()
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def agregarUsuario(self, id_proyecto, id_usuario):
        """Metodo que realiza la agregacion de un usuario al proyecto selecccionado"""
        try:
            usuario = DBSession.query(Usuario).get(id_usuario)
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            usuario.proyectos.append(proyecto)
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha asignado dicho Usuario! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/usuarioProyecto", id_proyecto=id_proyecto)
        except SQLAlchemyError:
            flash(_("No se ha asignado dicho Usuario! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/usuarioProyecto", id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se ha asignado decho Usuario! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/usuarioProyecto", id_proyecto=id_proyecto)
        else:
            flash(_("Usuario asignado!"), 'ok')

        redirect("/admin/proyecto/usuarioProyecto",id_proyecto=id_proyecto)

    @expose("is2sap.templates.proyecto.listaProyectos_a_iniciar")
    @require(predicates.has_any_permission('lider_proyecto'))
    def listaProyectos_a_iniciar(self,page=1):
        """Metodo para listar todos los Proyectos a iniciar de la base de datos"""
        try:
            proy = DBSession.query(Proyecto).filter_by(iniciado=False).order_by(Proyecto.id_proyecto)
            usuario = DBSession.query(Usuario).filter_by(nombre_usuario=request.identity['repoze.who.userid']).first()
            proyectos=[]
            for p in proy:
                if usuario.proyectos.count(p)==1:
                    proyectos.append(p)
            currentPage = paginate.Page(proyectos, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Proyectos! SQLAlchemyError..."), 'error')
            redirect("/admin")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Proyectos! Hay Problemas con el servidor..."), 'error')
            redirect("/admin")

        return dict(proyectos=currentPage.items, page='listaProyectos_a_iniciar', currentPage=currentPage)

    @expose()
    @require(predicates.has_any_permission('lider_proyecto'))
    def iniciar(self, id_proyecto, **kw):     
        """Metodo que da inicio a un proyecto"""
        try:
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            fases = proyecto.fases
            id_proyecto = proyecto.id_proyecto
            maxnumerofase = DBSession.query(func.max(Fase.numero_fase)).filter_by(id_proyecto=id_proyecto).first()

            if maxnumerofase[0]==None:
               flash(_("El Proyecto se encuentra sin fases! No puede iniciar..."), 'error')
               redirect("/admin/proyecto/listaProyectos_a_iniciar")
            else:
               proyecto.iniciado = True
               for fase in fases:
                   if fase.numero_fase == 1:
	              fase.id_estado_fase = '2'

               DBSession.flush()
               transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha realizado la inicializacion! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listaProyectos_a_iniciar")
        except SQLAlchemyError:
            flash(_("No se ha realizado la inicializacion! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/listaProyectos_a_iniciar")
        except (AttributeError, NameError):
            flash(_("No se ha realizado la inicializacion! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listaProyectos_a_iniciar")
        else:
            flash(_("Proyecto iniciado!"), 'ok')

        redirect("/admin/proyecto/listaProyectos_a_iniciar")

    @expose("is2sap.templates.proyecto.rolesProyectoUsuario")
    @require(predicates.has_any_permission('lider_proyecto'))
    def rolesProyectoUsuario(self,id_proyecto, id_usuario, page=1):
        """Metodo para listar todos los roles que tiene el usuario seleccionado"""
        try:
            usuario = DBSession.query(Usuario).get(id_usuario)
            rolesProyecto = DBSession.query(Rol).filter_by(tipo="Proyecto").all()
            roles = []
            for rol in rolesProyecto:
                if usuario.roles.count(rol) == 1:
                    roles.append(rol)
            
             
            currentPage = paginate.Page(roles, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Roles de Usuario! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/usuarios", id_proyecto=id_proyecto)
        except (AttributeError, NameError, ValueError):
            flash(_("No se pudo acceder a Roles de Usuario! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/usuarios", id_proyecto = id_proyecto)
        return dict(roles=currentPage.items, page='rolesProyectoUsuario', currentPage=currentPage, usuario=usuario, id_proyecto = id_proyecto)

    @expose("is2sap.templates.proyecto.agregarRolUsuario")
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def agregarRolUsuario(self, id_usuario, id_proyecto, page=1):
        """Metodo que permite listar los roles que se pueden agregar al usuario seleccionado"""
        try:
            usuario = DBSession.query(Usuario).get(id_usuario)
            rolesUsuario = usuario.roles
            rolesDB = DBSession.query(Rol).filter_by(tipo="Proyecto").all()
            roles = []
            for rol in rolesDB:
                if rolesUsuario.count(rol)==0:
                    roles.append(rol)

            currentPage = paginate.Page(roles, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Agregar Roles! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/agregarRolUsuario", id_usuario=id_usuario, id_proyecto=id_proyecto)
        except (AttributeError, NameError, ValueError):
            flash(_("No se pudo acceder a Agregar Roles! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/agregarRolUsuario", id_usuario=id_usuario, id_proyecto=id_proyecto)

        return dict(roles=currentPage.items, page='agregar_roles', currentPage=currentPage, 
                    id_usuario=id_usuario, usuario=usuario, id_proyecto=id_proyecto)

    @expose()
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def agregarRolUser(self, id_usuario, id_rol, id_proyecto):
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
            redirect("/admin/proyecto/rolesProyectoUsuario", id_proyecto=id_proyecto, id_usuario=id_usuario)
        except SQLAlchemyError:
            flash(_("No se pudo Asignar Rol! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/rolesProyectoUsuario", id_proyecto=id_proyecto, id_usuario=id_usuario)
        except (AttributeError, NameError):
            flash(_("No se pudo Asignar Rol! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/rolesProyectoUsuario", id_proyecto=id_proyecto, id_usuario=id_usuario)
        else:
            flash(_("Rol asignado!"), 'ok')

        redirect("/admin/proyecto/rolesProyectoUsuario", id_proyecto=id_proyecto, id_usuario=id_usuario)

    @expose()
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def eliminar_rol_usuario(self, id_usuario, id_rol, id_proyecto, **kw):
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
            redirect("/admin/proyecto/rolesProyectoUsuario",id_proyecto=id_proyecto, id_usuario=id_usuario)
        except SQLAlchemyError:
            flash(_("No se pudo Desasignar Rol! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/rolesProyectoUsuario",id_proyecto=id_proyecto, id_usuario=id_usuario)
        except (AttributeError, NameError):
            flash(_("No se pudo Desasignar Rol! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/rolesProyectoUsuario",id_proyecto=id_proyecto, id_usuario=id_usuario)
        else:
            flash(_("Rol desasignado!"), 'ok')

        redirect("/admin/proyecto/rolesProyectoUsuario",id_proyecto=id_proyecto, id_usuario=id_usuario)

    @expose("is2sap.templates.proyecto.listadoPermisoFase")
    @require(predicates.has_any_permission('administracion','lider_proyecto'))
    def listadoPermisoFase(self, id_usuario, id_rol, id_proyecto, page=1):
        """Metodo que permite listar los roles que se pueden agregar al usuario seleccionado"""
        try:
            roles = DBSession.query(Rol).get(id_rol)
            rolesFases = roles.fases
            rolesFases1 = roles.fases
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            listaFases =[]
            
            for fase in rolesFases:
                if proyecto.fases.count(fase) == 0:
                    rolesFases.remove(fase)
            

            for fase in proyecto.fases:
                if rolesFases1.count(fase) == 0:
                    listaFases.append(fase)
            currentPage = paginate.Page(rolesFases, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Listado Fases! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/rolesProyectoUsuario", id_proyecto=id_proyecto, id_usuario=id_usuario)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Agregar Roles! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/rolesProyectoUsuario", id_proyecto=id_proyecto, id_usuario=id_usuario)

        return dict(rolesFases=currentPage.items, page='agregar_roles', currentPage=currentPage, 
                    id_usuario=id_usuario, id_proyecto=id_proyecto, fasesRestantes=listaFases, id_rol=id_rol)

    @expose()
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def agregarPermisoFase(self, id_usuario, id_rol, id_proyecto, id_fase, page=1):
        """Metodo que permite listar los roles que se pueden agregar al usuario seleccionado"""
        try:
            roles = DBSession.query(Rol).get(id_rol)
            fase = DBSession.query(Fase).get(id_fase)
            usuario = DBSession.query(Usuario).get(id_usuario)
            roles.fases.append(fase)
            usuario.fases.append(fase)
            
            
        except SQLAlchemyError:
            redirect("/admin/proyecto/listadoPermisoFase", id_proyecto=id_proyecto, id_usuario=id_usuario, id_rol=id_rol)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Agregar Roles! Hay Problemas con el servidor..."), 'error')
            redirect("/admin/proyecto/listadoPermisoFase", id_proyecto=id_proyecto, id_usuario=id_usuario, id_rol=id_rol)

        redirect("/admin/proyecto/listadoPermisoFase", id_proyecto=id_proyecto, id_usuario=id_usuario, id_rol=id_rol)


    @expose()
    @require(predicates.has_any_permission('administracion',  'lider_proyecto'))
    def eliminarPermisoFase(self, id_usuario, id_rol, id_proyecto, id_fase, page=1):
        """Metodo que permite listar los roles que se pueden agregar al usuario seleccionado"""
        try:
            roles = DBSession.query(Rol).get(id_rol)
            fase = DBSession.query(Fase).get(id_fase)
            usuario = DBSession.query(Usuario).get(id_usuario)
            roles.fases.remove(fase)
            usuario.fases.remove(fase)
            
            
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Listado Fases! SQLAlchemyError..."), 'error')
            redirect("/admin/proyecto/listadoPermisoFase", id_proyecto=id_proyecto, id_usuario=id_usuario, id_rol=id_rol)
        except (AttributeError, NameError, ValueError):
            redirect("/admin/proyecto/listadoPermisoFase", id_proyecto=id_proyecto, id_usuario=id_usuario, id_rol=id_rol)

        redirect("/admin/proyecto/listadoPermisoFase", id_proyecto=id_proyecto, id_usuario=id_usuario, id_rol=id_rol)
