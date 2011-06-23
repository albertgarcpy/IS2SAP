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
    def listado(self,page=1):
        """Metodo para listar todos los Proyectos existentes de la base de datos"""
        try:
            proyectos = DBSession.query(Proyecto).order_by(Proyecto.id_proyecto)
            currentPage = paginate.Page(proyectos, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Proyectos! SQLAlchemyError..."), 'error')
            redirect("/admin")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Proyectos! Hay Problemas con el servidor..."), 'error')
            redirect("/admin")

        return dict(proyectos=currentPage.items, page='listado_proyecto', currentPage=currentPage)

    @expose('is2sap.templates.proyecto.editar')
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
    def rolProyecto(self, id_proyecto, page=1):
        """Metodo que permite listar los roles que se pueden agregar al proyecto seleccionado"""
        try:
            proyecto = DBSession.query(Proyecto).get(id_proyecto)
            id_proyecto = proyecto.id_proyecto
            rolesProyecto = proyecto.roles
            roles = DBSession.query(Rol).order_by(Rol.id_rol).all()
        
            for rol in rolesProyecto:
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
    def listaProyectos_a_iniciar(self,page=1):
        """Metodo para listar todos los Proyectos a iniciar de la base de datos"""
        try:
            proyectos = DBSession.query(Proyecto).filter_by(iniciado=False).order_by(Proyecto.id_proyecto)
            currentPage = paginate.Page(proyectos, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Proyectos! SQLAlchemyError..."), 'error')
            redirect("/admin")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Proyectos! Hay Problemas con el servidor..."), 'error')
            redirect("/admin")

        return dict(proyectos=currentPage.items, page='listaProyectos_a_iniciar', currentPage=currentPage)

    @expose()
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
   
