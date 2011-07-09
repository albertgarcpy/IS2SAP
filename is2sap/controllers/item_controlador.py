# -*- coding: utf-8 -*-
"""Controlador de Item"""

from tg import expose, flash, require, url, request, redirect, response
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates
from tg import tmpl_context, validate
from webhelpers import paginate
from tg.controllers import RestController, redirect
from repoze.what.predicates import has_permission
import formencode
from tw import forms
from tw.forms import TableForm, Spacer, TextField, PasswordField, CalendarDatePicker, TextArea, SingleSelectField
from tw.forms.fields import Button, SubmitButton, HiddenField, CheckBox, FileField
from tw.forms.validators import *
from sqlalchemy.orm import contains_eager
import shutil
import os
from pkg_resources import resource_filename
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import transaction
from tg.controllers import CUSTOM_CONTENT_TYPE

public_dirname = os.path.join(os.path.abspath(resource_filename('is2sap', 'public')))
items_dirname = os.path.join(public_dirname, 'items')

from is2sap.widgets.mi_validador.mi_validador import *
from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import TipoItem, Item, Proyecto, Usuario, Fase, Atributo, ItemDetalle, ItemHistorial, ItemDetalleHistorial, LineaBase, LineaBase_Item, LineaBaseHistorial, RelacionItem, ItemArchivo, RelacionHistorial
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController
from is2sap.widgets.item_form import ItemForm, EditItemForm
import pydot

import networkx as nx
import matplotlib.pyplot as plt
import random

itemsAfectados=[]
listaRelaciones = []
id_item_actual = []

__all__ = ['ItemController']


class ItemController(BaseController):

    
    @expose('is2sap.templates.item.index')
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='Item', page='index_item')


#--------------------------- Creacion de Items ---------------------------------
    @expose('is2sap.templates.item.nuevo')
    @require(predicates.has_any_permission('administracion','crear_item', msg=l_('No posee los permisos de creacion de item')))
    def nuevo(self, id_proyecto, id_fase, id_tipo_item, **kw):
        """Despliega el formulario para añadir un nuevo Item."""
        try:
            #Creamos la Lista fields para el widget de creacion de Item
            complejidad_options = ['1','2','3','4','5','6','7','8','9','10']
            prioridad_options = ['Baja','Media','Alta']
            estado_options = ['Desarrollo','Revision','Aprobado']

            fields = [
                HiddenField('id_item', label_text='Id'),
                HiddenField('id_tipo_item', validator=NotEmpty, label_text='Tipo de Item'),
                Spacer(),
                HiddenField('codigo', validator=NotEmpty, label_text='Codigo'),
                Spacer(),
                TextArea('descripcion', validator=NotEmpty, attrs=dict(rows=10, cols=50), label_text='Descripcion',
                      help_text='Introduzca una descripcion'),
                Spacer(),
                SingleSelectField('complejidad', validator=NotEmpty, options=complejidad_options, label_text='Complejidad',
                      help_text='Introduzca la complejidad del item.'),
                Spacer(),
                SingleSelectField('prioridad', validator=NotEmpty, options=prioridad_options, label_text='Prioridad',
                      help_text='Introduzca la prioridad'),
                Spacer(),
                TextField('estado', disabled='False', label_text='Estado'),
                Spacer(),
	        HiddenField('version', validator=NotEmpty, label_text='Version',
                      help_text='Introduzca una version'),
                Spacer(),
	        TextArea('observacion', validator=PlainText, attrs=dict(rows=10, cols=50), label_text='Observacion',
                      help_text='Introduzca una observacion'),
                Spacer(),
	        CalendarDatePicker('fecha_modificacion', validator=NotEmpty, label_text='Fecha de Modificacion', 
                      date_format='%d/%m/%Y'),
                Spacer(),
                CheckBox('vivo', disabled='False', label_text='Vivo', default='True',
                     help_text='Indica si esta vivo'),
                Spacer()]

            #Añadimos los Atributos especificos del Item
            atributos_nuevos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item)

            for atributo_nuevo in atributos_nuevos:
                id_atributo = str(atributo_nuevo.id_atributo)
                nombre = atributo_nuevo.nombre            
                tipo = atributo_nuevo.tipo
        
                if tipo=='Texto':
                   fields.append(TextField(id_atributo, label_text=nombre, size=38,
                              help_text='Introduzca un texto'))
                   fields.append(Spacer())
                elif tipo=='Numerico':
                   fields.append(TextField(id_atributo, label_text=nombre, size=38,
                              help_text='Introduzca un valor numerico'))
                   fields.append(Spacer())
                else:
                   fields.append(CalendarDatePicker(id_atributo, label_text=nombre, date_format='%d/%m/%Y',
                              help_text='Seleccione una fecha'))
                   fields.append(Spacer())

            #Creamos el Widget de Creacion de Item
            crear_item_form = ItemForm("CrearItem", action='add',fields=fields)
            tmpl_context.form = crear_item_form

            #Rellenamos algunos campos
            kw['id_tipo_item']= int(id_tipo_item)
            items = DBSession.query(Item).filter_by(id_tipo_item=id_tipo_item)
            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
            cont = 0

            for item in items:
                cont = cont + 1
            
            kw['codigo'] = str(tipo_item.codigo) + "-" + str(cont + 1)
            kw['version'] = 1
            kw['estado'] = "Desarrollo"

        except SQLAlchemyError:
            flash(_("No se pudo acceder a Creacion de Items! SQLAlchemyError..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Creacion de Items! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        
        return dict(nombre_modelo='Item', id_proyecto=id_proyecto, id_fase=id_fase, 
                    id_tipo_item=id_tipo_item, page='nuevo_item', value=kw)
    
    #@validate(crear_item_form)#form=globals().get('crear_form'),error_handler=nuevo)
    @expose()
    @require(predicates.has_any_permission('administracion','crear_item', msg=l_('No posee los permisos de creacion de item')))
    def add(self, **kw):
        """Metodo para agregar un nuevo item a la base de datos """
        try:
            #Datos necesarios para redireccionar
            id_tipo_item = kw['id_tipo_item']
            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
            id_fase = tipo_item.id_fase
            fase = DBSession.query(Fase).get(id_fase)
            id_proyecto = fase.id_proyecto

            #Creamos una nueva instancia de Item
            item = Item()
            item.id_tipo_item = kw['id_tipo_item']
            item.codigo = kw['codigo']

            #Validamos el campo Descripcion, no puede estar vacio
            if kw['descripcion'] == "":
               flash(_("Rellene el campo 'Descripcion'"), 'warning')
               redirect("/item/nuevo", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
            else:
               item.descripcion = kw['descripcion']

            #Continuamos cargando el objeto
            item.complejidad = kw['complejidad']
            item.prioridad = kw['prioridad']
            item.estado = "Desarrollo"
            item.version = kw['version']
            item.observacion = kw['observacion']

            #Validamos el campo Fecha de Modificacion
            try:
                validador_fecha = validators.DateConverter()
                validador_fecha.to_python(kw['fecha_modificacion'])

                if kw['fecha_modificacion'] == "":
                  flash(_("Rellene el campo 'Fecha de Modificacion'"), 'warning')
                  redirect("/item/nuevo", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

            except formencode.Invalid, e:
                flash(_("Formato incorrecto del campo 'Fecha de Modificacion'"), 'warning')
                redirect("/item/nuevo", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
            else:
                item.fecha_modificacion = kw['fecha_modificacion']

            #Completamos la carga de atributos del objeto
            item.vivo = True

            #Validamos los campos de tipo Fecha que puedan existir entre los atributos especificos
            #antes de insertar el objeto Item a la base de datos
            atributos_nuevos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item)

            if atributos_nuevos != None:
               for atributo_nuevo in atributos_nuevos:
                   if atributo_nuevo.tipo == "Fecha":
                      try:
                          validador_fecha_atr = validators.DateConverter()
                          validador_fecha_atr.to_python(kw[str(atributo_nuevo.id_atributo)])
                      except formencode.Invalid, e:
                          flash(_("Formato incorrecto del campo '" + atributo_nuevo.nombre + "'" ), 'warning')
                          redirect("/item/nuevo", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

            #Guardamos el nuevo Item en la base de datos
            DBSession.add(item)
            DBSession.flush()

            id_item = item.id_item
            atributos_nuevos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item)
            
            #Creamos los atributos especificos del Item e insertamos en la BD
            if atributos_nuevos != None:
               for atributo_nuevo in atributos_nuevos:
                   itemDetalle = ItemDetalle()
                   itemDetalle.id_item = id_item
                   itemDetalle.id_atributo = atributo_nuevo.id_atributo
                   itemDetalle.nombre_atributo = atributo_nuevo.nombre
                   itemDetalle.valor = kw[str(atributo_nuevo.id_atributo)]
                   DBSession.add(itemDetalle)
            
            #Si al crear el Item la Fase correspondiente se encuentra con el estado
            #"Con Lineas Bases", cambiarlo al estado "Con Lineas Bases Parciales"
	    if fase.relacion_estado_fase.nombre_estado == 'Con Lineas Bases':
               fase.id_estado_fase = '3'

            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except SQLAlchemyError:
            flash(_("No se ha guardado! SQLAlchemyError..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se ha guardado! Problemas de atributo..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        else:
            flash(_("Item creado!"), 'ok')

        redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

#--------------------------- Adjuntar Archivos ---------------------------------

    @expose('is2sap.templates.item.archivos_adjuntos')
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee permiso de visualizacion')))
    def archivos_adjuntos(self, id_proyecto, id_fase, id_tipo_item, id_item):
        """Despliega el formulario para añadir un nuevo Archivo o Eliminar de la BD"""
        global id_item_actual
        id_item_actual = []
        id_item_actual.append(id_item)
        item = DBSession.query(Item).get(id_item)
        codigo_item = item.codigo
        version = item.version
        current_files = DBSession.query(ItemArchivo).filter_by(id_item=id_item).filter_by(version_item=version)

        return dict(codigo_item=codigo_item, page='archivos_adjuntos', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item, current_files=current_files)
        
    @expose('is2sap.templates.item.archivos_adjuntos')
    @require(predicates.has_any_permission('administracion','guardar_archivo', msg=l_('No posee los permisos de almacenamiento de archivos')))
    def save(self, userfile):
        """Metodo para agregar un nuevo archivo a la base de datos """
        try:
            global id_item_actual
            item = DBSession.query(Item).get(id_item_actual[0])
            id_item = item.id_item
            version_anterior = item.version
            version_nueva = int(item.version) + 1
            id_tipo_item = item.id_tipo_item
            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
            id_fase = tipo_item.id_fase
            fase = DBSession.query(Fase).get(id_fase)
            id_proyecto = fase.id_proyecto
            linea_bases_item = item.linea_bases

            #Comprobamos que el Item no se encuentre en una Linea Base
            if linea_bases_item != []:
               for linea_base_item in linea_bases_item:
                   flash(_("No se puede agregar el archivo! El Item se encuentra en una Linea Base..."), 'error')
                   redirect("/item/archivos_adjuntos", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)

            if userfile == "":
               flash(_("Introduzca una ruta de archivo!"), 'error')
               redirect("/item/archivos_adjuntos", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)

            forbidden_files = [".js", ".htm", ".html", ".mp3"]
            for forbidden_file in forbidden_files:
                if userfile.filename.find(forbidden_file) != -1:
                   flash(_("No se puede guardar el contenido..."), 'error')
                   redirect("/item/archivos_adjuntos", id_proyecto=id_proyecto, id_fase=id_fase, 
                            id_tipo_item=id_tipo_item, id_item=id_item)

            #Guardamos el archivo nuevo
            nombre_archivo = userfile.filename
            contenido_archivo = userfile.file.read()
            nuevo_archivo = ItemArchivo()
            nuevo_archivo.id_item = item.id_item
            nuevo_archivo.version_item = version_nueva
            nuevo_archivo.nombre_archivo = nombre_archivo
            nuevo_archivo.contenido_archivo = contenido_archivo
            DBSession.add(nuevo_archivo)

            #El item actual cambia de version a tener un nuevo archivo adjunto
            itemHistorial = ItemHistorial()
            itemHistorial.id_item = item.id_item
            itemHistorial.id_tipo_item = item.id_tipo_item
            itemHistorial.codigo = item.codigo
            itemHistorial.descripcion = item.descripcion
            itemHistorial.complejidad = item.complejidad
            itemHistorial.prioridad = item.prioridad
            itemHistorial.estado = "Desarrollo"
            itemHistorial.version = version_anterior
            itemHistorial.observacion = item.observacion
            itemHistorial.fecha_modificacion = item.fecha_modificacion
            item.version = version_nueva
            item.estado = "Desarrollo"
            DBSession.add(itemHistorial)
            DBSession.flush()

            #Consultamos los detalles que tiene el Item a ser editado y tambien
            #los atributos actuales de su Tipo de Item correspondiente
            detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item)
            atributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item)
            lista_id_atributo = []

            if atributos != None:
               for atributo in atributos:
                   lista_id_atributo.append(atributo.id_atributo)

            #Enviamos al historial los detalles del item a ser editado
            if detalles != None:
               for detalle in detalles:
                   lista_id_atributo.remove(detalle.id_atributo)
                   itemDetalleHistorial = ItemDetalleHistorial()
                   itemDetalleHistorial.id_item = id_item
                   itemDetalleHistorial.id_item_detalle = detalle.id_item_detalle
                   itemDetalleHistorial.id_atributo = detalle.id_atributo
                   itemDetalleHistorial.nombre_atributo = detalle.nombre_atributo
                   itemDetalleHistorial.valor = detalle.valor
                   itemDetalleHistorial.version = version_anterior
                   DBSession.add(itemDetalleHistorial)
                   DBSession.flush()

            #Cargamos a vacio los atributos que no contemplaban los detalles actuales
            if lista_id_atributo != None:
               for id_atributo in lista_id_atributo:
                   atributo = DBSession.query(Atributo).get(id_atributo)
                   itemDetalle = ItemDetalle()
                   itemDetalle.id_item = id_item
                   itemDetalle.id_atributo = atributo.id_atributo
                   itemDetalle.nombre_atributo = atributo.nombre
                   itemDetalle.valor = ""
                   DBSession.add(itemDetalle)
                   DBSession.flush()

            #Enviamos sus relaciones actuales al historial de relaciones
            hijos = DBSession.query(RelacionItem).filter_by(id_item1=id_item)
            antecesores = DBSession.query(RelacionItem).filter_by(id_item2=id_item)
            if hijos != None:
               for hijo in hijos:
                   relacion_historial = RelacionHistorial()
                   relacion_historial.tipo = hijo.tipo
                   relacion_historial.id_item1 = hijo.id_item1
                   relacion_historial.id_item2 = hijo.id_item2
                   relacion_historial.version_modif = version_anterior
                   DBSession.add(relacion_historial)
                   DBSession.flush()
            if antecesores != None:
               for antecesor in antecesores:
                   relacion_historial = RelacionHistorial()
                   relacion_historial.tipo = antecesor.tipo
                   relacion_historial.id_item1 = antecesor.id_item1
                   relacion_historial.id_item2 = antecesor.id_item2
                   relacion_historial.version_modif = version_anterior
                   DBSession.add(relacion_historial)
                   DBSession.flush()

            #Ponemos a revision todos los items afectados por el Item editado
            #Tambien colocamos a "Revision" las Lineas Bases correspondientes
            global itemsAfectados
            global listaRelaciones
            itemsAfectados = []
            listaRelaciones = []
            
            itemsAfectados.append(id_item)

            for item_afectado in itemsAfectados:
                self.buscarRelaciones(item_afectado)

            for item_afectado in itemsAfectados:
                item_cambio = DBSession.query(Item).get(item_afectado)
                item_cambio.estado = "Revision"
                linea_bases_item = item_cambio.linea_bases
                if linea_bases_item != None:
                   for linea_base_item in linea_bases_item:
                       if linea_base_item.estado == "Aprobado":
                          id_linea_base = linea_base_item.id_linea_base 
                          linea_base = DBSession.query(LineaBase).get(id_linea_base)
                          linea_base.estado = "Revision"
                          fase = DBSession.query(Fase).get(linea_base.id_fase)
                          if fase.relacion_estado_fase.nombre == "Finalizado":
                             fase.id_estado_fase = '4'
                          DBSession.flush()
                DBSession.flush() 

            #Los archivos adjuntos del item a se editado, se copian
            #para tener el registro de estos archivos con esa version de item
            archivos_item_editado = DBSession.query(ItemArchivo).filter_by(id_item=id_item).filter_by(version_item=version_anterior)
            if archivos_item_editado != None:
               for archivo in archivos_item_editado:
                   nuevo_archivo = ItemArchivo()
                   nuevo_archivo.id_item = archivo.id_item
                   nuevo_archivo.version_item = version_anterior
                   nuevo_archivo.nombre_archivo = archivo.nombre_archivo
                   nuevo_archivo.contenido_archivo = archivo.contenido_archivo
                   archivo.version_item = version_nueva
                   DBSession.add(nuevo_archivo)
                   DBSession.flush()

            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/item/archivos_adjuntos", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)
        except SQLAlchemyError:
            flash(_("No se ha guardado! SQLAlchemyError..."), 'error')
            redirect("/item/archivos_adjuntos", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)
        except (AttributeError, NameError):
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/item/archivos_adjuntos", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)
        else:
            flash(_("Archivo guardado!"), 'ok')

        redirect("/item/archivos_adjuntos", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)
    
    @expose(content_type=CUSTOM_CONTENT_TYPE)
    @require(predicates.has_any_permission('administracion', 'crear_item', msg=l_('No posee los permisos de creacion de item')))
    def view(self, fileid):
        """Metodo que muestra el contenido de un archivo en pantalla"""
        try:
            userfile = DBSession.query(ItemArchivo).filter_by(id_item_archivo=fileid).one()
            id_item = userfile.id_item
            item = DBSession.query(Item).get(id_item)
            id_tipo_item = item.id_tipo_item
            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
            id_fase = tipo_item.id_fase
            fase = DBSession.query(Fase).get(id_fase)
            id_proyecto = fase.id_proyecto
        except:
            flash(_("No se puede mostrar el contenido..."), 'error')
            redirect("/item/archivos_adjuntos", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)

        content_types = {
            'display': {'.png': 'image/jpeg', '.jpeg':'image/jpeg', '.jpg':'image/jpeg', '.gif':'image/jpeg', '.txt': 'text/plain'},
            'download': {'.pdf':'application/pdf', '.zip':'application/zip', '.rar':'application/x-rar-compressed'}
        }

        for file_type in content_types['display']:
            if userfile.nombre_archivo.endswith(file_type):
                response.headers["Content-Type"] = content_types['display'][file_type]

        for file_type in content_types['download']:
            if userfile.nombre_archivo.endswith(file_type):
                response.headers["Content-Type"] = content_types['download'][file_type]
                response.headers["Content-Disposition"] = 'attachment; filename="'+userfile.nombre_archivo+'"'

        if userfile.nombre_archivo.find(".") == -1:
            response.headers["Content-Type"] = "text/plain"

        return userfile.contenido_archivo
    
    @expose()
    @require(predicates.has_any_permission('administracion','eliminar_archivo', msg=l_('No posee los permisos para eliminar de archivos')))
    def eliminar_archivo(self, fileid):
        """Metodo para eliminar un archivo de la base de datos """
        try:
            global id_item_actual
            item = DBSession.query(Item).get(id_item_actual[0])
            id_item = item.id_item
            version_anterior = item.version
            version_nueva = int(item.version) + 1
            id_tipo_item = item.id_tipo_item
            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
            id_fase = tipo_item.id_fase
            fase = DBSession.query(Fase).get(id_fase)
            id_proyecto = fase.id_proyecto
            linea_bases_item = item.linea_bases

            #Comprobamos que el Item no se encuentre en una Linea Base
            if linea_bases_item != []:
               for linea_base_item in linea_bases_item:
                   flash(_("No se puede eliminar el archivo! El Item se encuentra en una Linea Base..."), 'error')
                   redirect("/item/archivos_adjuntos", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)

            #El Item actual cambia de version al tener un archivo menos
            itemHistorial = ItemHistorial()
            itemHistorial.id_item = item.id_item
            itemHistorial.id_tipo_item = item.id_tipo_item
            itemHistorial.codigo = item.codigo
            itemHistorial.descripcion = item.descripcion
            itemHistorial.complejidad = item.complejidad
            itemHistorial.prioridad = item.prioridad
            itemHistorial.estado = "Desarrollo"
            itemHistorial.version = version_anterior
            itemHistorial.observacion = item.observacion
            itemHistorial.fecha_modificacion = item.fecha_modificacion
            item.version = version_nueva
            item.estado = "Desarrollo"
            DBSession.add(itemHistorial)
            DBSession.flush()

            #Consultamos los detalles que tiene el Item a ser editado y tambien
            #los atributos actuales de su Tipo de Item correspondiente
            detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item)
            atributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item)
            lista_id_atributo = []

            if atributos != None:
               for atributo in atributos:
                   lista_id_atributo.append(atributo.id_atributo)

            #Enviamos al historial los detalles del item a ser editado
            if detalles != None:
               for detalle in detalles:
                   lista_id_atributo.remove(detalle.id_atributo)
                   itemDetalleHistorial = ItemDetalleHistorial()
                   itemDetalleHistorial.id_item = id_item
                   itemDetalleHistorial.id_item_detalle = detalle.id_item_detalle
                   itemDetalleHistorial.id_atributo = detalle.id_atributo
                   itemDetalleHistorial.nombre_atributo = detalle.nombre_atributo
                   itemDetalleHistorial.valor = detalle.valor
                   itemDetalleHistorial.version = version_anterior
                   DBSession.add(itemDetalleHistorial)
                   DBSession.flush()

            #Cargamos a vacio los atributos que no contemplaban los detalles actuales
            if lista_id_atributo != None:
               for id_atributo in lista_id_atributo:
                   atributo = DBSession.query(Atributo).get(id_atributo)
                   itemDetalle = ItemDetalle()
                   itemDetalle.id_item = id_item
                   itemDetalle.id_atributo = atributo.id_atributo
                   itemDetalle.nombre_atributo = atributo.nombre
                   itemDetalle.valor = ""
                   DBSession.add(itemDetalle)
                   DBSession.flush()

            #Enviamos sus relaciones actuales al historial de relaciones
            hijos = DBSession.query(RelacionItem).filter_by(id_item1=id_item)
            antecesores = DBSession.query(RelacionItem).filter_by(id_item2=id_item)
            if hijos != None:
               for hijo in hijos:
                   relacion_historial = RelacionHistorial()
                   relacion_historial.tipo = hijo.tipo
                   relacion_historial.id_item1 = hijo.id_item1
                   relacion_historial.id_item2 = hijo.id_item2
                   relacion_historial.version_modif = version_anterior
                   DBSession.add(relacion_historial)
                   DBSession.flush()
            if antecesores != None:
               for antecesor in antecesores:
                   relacion_historial = RelacionHistorial()
                   relacion_historial.tipo = antecesor.tipo
                   relacion_historial.id_item1 = antecesor.id_item1
                   relacion_historial.id_item2 = antecesor.id_item2
                   relacion_historial.version_modif = version_anterior
                   DBSession.add(relacion_historial)
                   DBSession.flush()

            #Ponemos a revision todos los items afectados por el Item editado
            #Tambien colocamos a "Revision" las Lineas Bases correspondientes
            global itemsAfectados
            global listaRelaciones
            itemsAfectados = []
            listaRelaciones = []
            
            itemsAfectados.append(id_item)

            for item_afectado in itemsAfectados:
                self.buscarRelaciones(item_afectado)

            for item_afectado in itemsAfectados:
                item_cambio = DBSession.query(Item).get(item_afectado)
                item_cambio.estado = "Revision"
                linea_bases_item = item_cambio.linea_bases
                if linea_bases_item != None:
                   for linea_base_item in linea_bases_item:
                       if linea_base_item.estado == "Aprobado":
                          id_linea_base = linea_base_item.id_linea_base 
                          linea_base = DBSession.query(LineaBase).get(id_linea_base)
                          linea_base.estado = "Revision"
                          fase = DBSession.query(Fase).get(linea_base.id_fase)
                          if fase.relacion_estado_fase.nombre == "Finalizado":
                             fase.id_estado_fase = '4'
                          DBSession.flush()
                DBSession.flush()

            #Los archivos adjuntos del item a se editado, se copian
            #para tener el registro de estos archivos con esa version de item
            archivos_item_editado = DBSession.query(ItemArchivo).filter_by(id_item=id_item).filter_by(version_item=version_anterior)
            userfile = DBSession.query(ItemArchivo).filter_by(id_item_archivo=fileid).one()
            if archivos_item_editado != None:
               for archivo in archivos_item_editado:
                   nuevo_archivo = ItemArchivo()
                   nuevo_archivo.id_item = archivo.id_item
                   nuevo_archivo.version_item = version_anterior
                   nuevo_archivo.nombre_archivo = archivo.nombre_archivo
                   nuevo_archivo.contenido_archivo = archivo.contenido_archivo
                   DBSession.add(nuevo_archivo)
                   DBSession.flush()
                   if archivo.id_item_archivo != userfile.id_item_archivo:
                      archivo.version_item = version_nueva
                      DBSession.flush()

            DBSession.delete(userfile)
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se ha eliminado! Hay Problemas con el servidor..."), 'error')
            redirect("/item/archivos_adjuntos", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)
        except SQLAlchemyError:
            flash(_("No se ha eliminado! SQLAlchemyError..."), 'error')
            redirect("/item/archivos_adjuntos", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)
        except (AttributeError, NameError):
            flash(_("No se ha eliminado! Hay Problemas con el servidor..."), 'error')
            redirect("/item/archivos_adjuntos", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)
        else:
            flash(_("Archivo eliminado!"), 'ok')
        
        redirect("/item/archivos_adjuntos", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)


#--------------------------- Edicion de Items ----------------------------------
    @expose('is2sap.templates.item.editar')
    @require(predicates.has_any_permission('administracion','editar_item', msg=l_('No posee los permisos para edicion de items')))
    def editar(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):
        """Metodo que rellena el formulario para editar los datos de un item"""
        item = DBSession.query(Item).get(id_item)
        linea_bases_item = item.linea_bases

        #Comprobamos que no se encuentre en una Linea Base
        if linea_bases_item != None:
           for linea_base_item in linea_bases_item:
               flash(_("No puede Editar el Item! Se encuentra en una Linea Base..."), 'error')
               redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

        try:
            complejidad_options = ['1','2','3','4','5','6','7','8','9','10']
            prioridad_options = ['Baja','Media','Alta']
            estado_options = ['Desarrollo','Revision','Aprobado']

            fields = [
                HiddenField('id_item', label_text='Id'),
                HiddenField('id_tipo_item', validator=NotEmpty, label_text='Tipo de Item'),
                Spacer(),
                HiddenField('codigo', validator=NotEmpty, label_text='Codigo'),
                Spacer(),
                TextArea('descripcion', validator=NotEmpty, attrs=dict(rows=10, cols=50), label_text='Descripcion',
                      help_text='Introduzca una descripcion'),
                Spacer(),
                SingleSelectField('complejidad', validator=NotEmpty, options=complejidad_options, label_text='Complejidad',
                      help_text='Introduzca la complejidad del item.'),
                Spacer(),
                SingleSelectField('prioridad', validator=NotEmpty, options=prioridad_options, label_text='Prioridad',
                      help_text='Introduzca la prioridad'),
                Spacer(),
                TextField('estado', disabled='False', label_text='Estado'),
                Spacer(),
	        HiddenField('version', validator=NotEmpty, label_text='Version',
                      help_text='Introduzca una version'),
                Spacer(),
	        TextArea('observacion', validator=PlainText, attrs=dict(rows=10, cols=50), label_text='Observacion',
                      help_text='Introduzca una observacion'),
                Spacer(),
	        CalendarDatePicker('fecha_modificacion', validator=NotEmpty, label_text='Fecha de Modificacion', 
                      date_format='%d/%m/%Y'),
                Spacer(),
                CheckBox('vivo', disabled='False', label_text='Vivo', default='True',
                     help_text='Indica si esta vivo'),
                Spacer()]

            atributos_nuevos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item)

            for atributo_nuevo in atributos_nuevos:
                id_atributo = str(atributo_nuevo.id_atributo)
                nombre = atributo_nuevo.nombre            
                tipo = atributo_nuevo.tipo
        
                if tipo=='Texto':
                   fields.append(TextField(id_atributo, label_text=nombre, size=38,
                              help_text='Introduzca un texto'))
                   fields.append(Spacer())
                elif tipo=='Numerico':
                   fields.append(TextField(id_atributo, label_text=nombre, size=38,
                              help_text='Introduzca un valor numerico'))
                   fields.append(Spacer())
                else:
                   fields.append(CalendarDatePicker(id_atributo, label_text=nombre, date_format='%d/%m/%Y',
                              help_text='Seleccione una fecha'))
                   fields.append(Spacer())
            
            editar_item_form = ItemForm("EditarItem", action='update',fields=fields)
            tmpl_context.form = editar_item_form
            
            kw['id_item'] = item.id_item
            kw['id_tipo_item'] = item.id_tipo_item
            kw['codigo'] = item.codigo
            kw['descripcion'] = item.descripcion
            kw['complejidad'] = item.complejidad
            kw['prioridad'] = item.prioridad
            kw['estado'] = "Desarrollo"
            kw['version'] = item.version
            kw['observacion'] = item.observacion
            kw['fecha_modificacion'] = item.fecha_modificacion
            kw['vivo'] = item.vivo
            id_item = item.id_item
            detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item)

            for detalle in detalles:
                valor = detalle.valor
                kw[str(detalle.id_atributo)] = valor

        except SQLAlchemyError:
            flash(_("No se pudo acceder a Edicion de Items! SQLAlchemyError..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Edicion de Items! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

	return dict(nombre_modelo='Item', id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, page='editar_item', value=kw)

    @expose()
    #@validate(editar_item_form, error_handler=editar)
    @require(predicates.has_any_permission('administracion','editar_item', msg=l_('No posee los permisos para edicion de items')))
    def update(self, **kw):        
        """Metodo que actualiza los datos de un item"""
        try:
            #Consultamos algunas informaciones referentes al item
            item = DBSession.query(Item).get(kw['id_item'])
            id_item = item.id_item
            id_tipo_item = item.id_tipo_item
            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
            id_fase = tipo_item.id_fase
            fase = DBSession.query(Fase).get(id_fase)
            id_proyecto = fase.id_proyecto

            #Validamos el campo Descripcion, no puede estar vacio
            if kw['descripcion'] == "":
               flash(_("Rellene el campo 'Descripcion'"), 'warning')
               redirect("/item/editar", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)

            #Validamos el campo Fecha de Modificacion
            try:
                validador_fecha = validators.DateConverter()
                validador_fecha.to_python(kw['fecha_modificacion'])

                if kw['fecha_modificacion'] == "":
                  flash(_("Rellene el campo 'Fecha de Modificacion'"), 'warning')
                  redirect("/item/editar", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)

            except formencode.Invalid, e:
                flash(_("Formato incorrecto del campo 'Fecha de Modificacion'"), 'warning')
                redirect("/item/editar", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)

            #Validamos los atributos especificos del tipo Fecha
            atributos_especificos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item)

            if atributos_especificos != None:
               for atributo_especifico in atributos_especificos:
                   if atributo_especifico.tipo == "Fecha":
                      try:
                          validador_fecha_atr = validators.DateConverter()
                          validador_fecha_atr.to_python(kw[str(atributo_especifico.id_atributo)])
                      except formencode.Invalid, e:
                          flash(_("Formato incorrecto del campo '" + atributo_especifico.nombre + "'" ), 'warning')
                          redirect("/item/editar", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item)

            #Llevamos al historial el item a ser editado
            version_a_editar = item.version   
            itemHistorial = ItemHistorial()
            itemHistorial.id_item = item.id_item
            itemHistorial.id_tipo_item = item.id_tipo_item
            itemHistorial.codigo = item.codigo
            itemHistorial.descripcion = item.descripcion
            itemHistorial.complejidad = item.complejidad
            itemHistorial.prioridad = item.prioridad
            itemHistorial.estado = "Desarrollo"
            itemHistorial.version = item.version
            itemHistorial.observacion = item.observacion
            itemHistorial.fecha_modificacion = item.fecha_modificacion
            DBSession.add(itemHistorial)
            DBSession.flush()

            #Enviamos sus relaciones actuales al historial de relaciones
            hijos = DBSession.query(RelacionItem).filter_by(id_item1=item.id_item)
            antecesores = DBSession.query(RelacionItem).filter_by(id_item2=item.id_item)
            if hijos != None:
               for hijo in hijos:
                   relacion_historial = RelacionHistorial()
                   relacion_historial.tipo = hijo.tipo
                   relacion_historial.id_item1 = hijo.id_item1
                   relacion_historial.id_item2 = hijo.id_item2
                   relacion_historial.version_modif = item.version
                   DBSession.add(relacion_historial)
                   DBSession.flush()
            if antecesores != None:
               for antecesor in antecesores:
                   relacion_historial = RelacionHistorial()
                   relacion_historial.tipo = antecesor.tipo
                   relacion_historial.id_item1 = antecesor.id_item1
                   relacion_historial.id_item2 = antecesor.id_item2
                   relacion_historial.version_modif = item.version
                   DBSession.add(relacion_historial)
                   DBSession.flush()
            
            #Cargamos el item con los valores nuevos
            item.id_tipo_item = kw['id_tipo_item']
            item.codigo = kw['codigo']
            item.descripcion = kw['descripcion']
            item.complejidad = kw['complejidad']
            item.prioridad = kw['prioridad']
            item.estado = "Desarrollo"
            item.version = int(kw['version']) + 1
            version_d_editar = item.version
            item.observacion = kw['observacion']
            item.fecha_modificacion = kw['fecha_modificacion']
            item.vivo = True
            DBSession.flush()

            #Consultamos los detalles que tiene el Item a ser editado y tambien
            #los atributos actuales de su Tipo de Item correspondiente
            detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item)
            atributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item)
            lista_id_atributo = []

            if atributos != None:
               for atributo in atributos:
                   lista_id_atributo.append(atributo.id_atributo)

            #Enviamos al historial los detalles del item a ser editado
            if detalles != None:
               for detalle in detalles:
                   lista_id_atributo.remove(detalle.id_atributo)
                   itemDetalleHistorial = ItemDetalleHistorial()
                   itemDetalleHistorial.id_item = id_item
                   itemDetalleHistorial.id_item_detalle = detalle.id_item_detalle
                   itemDetalleHistorial.id_atributo = detalle.id_atributo
                   itemDetalleHistorial.nombre_atributo = detalle.nombre_atributo
                   itemDetalleHistorial.valor = detalle.valor
                   itemDetalleHistorial.version = itemHistorial.version
                   detalle.valor = kw[str(detalle.id_atributo)]
                   DBSession.add(itemDetalleHistorial)
                   DBSession.flush()

            #Cargamos los atributos que no contemplaban los detalles actuales
            if lista_id_atributo != None:
               for id_atributo in lista_id_atributo:
                   atributo = DBSession.query(Atributo).get(id_atributo)
                   itemDetalle = ItemDetalle()
                   itemDetalle.id_item = id_item
                   itemDetalle.id_atributo = atributo.id_atributo
                   itemDetalle.nombre_atributo = atributo.nombre
                   itemDetalle.valor = kw[str(atributo.id_atributo)]
                   DBSession.add(itemDetalle)
                   DBSession.flush()

            linea_bases_item = item.linea_bases

            #Desasignamos automaticamente de la Linea Base en que se encuentra
            #si se encuentra en una Linea Base con estado distinto a "Aprobado"
            #if linea_bases_item != None:
            #   for linea_base_item in linea_bases_item:
            #       if linea_base_item.estado != "Aprobado":
            #          id_linea_base = linea_base_item.id_linea_base 
            #          linea_base = DBSession.query(LineaBase).get(id_linea_base)
            #          item.linea_bases.remove(linea_base)
            #          DBSession.flush()

            global itemsAfectados
            global listaRelaciones
            itemsAfectados = []
            listaRelaciones = []
            
            itemsAfectados.append(id_item)

            for item_afectado in itemsAfectados:
                self.buscarRelaciones(item_afectado)

            #Ponemos a revision todos los items afectados por el Item editado
            #Tambien colocamos a "Revision" las Lineas Bases correspondientes
            for item_afectado in itemsAfectados:
                item_cambio = DBSession.query(Item).get(item_afectado)
                item_cambio.estado = "Revision"
                linea_bases_item = item_cambio.linea_bases
                if linea_bases_item != None:
                   for linea_base_item in linea_bases_item:
                       if linea_base_item.estado == "Aprobado":
                          id_linea_base = linea_base_item.id_linea_base 
                          linea_base = DBSession.query(LineaBase).get(id_linea_base)
                          linea_base.estado = "Revision"
                          fase = DBSession.query(Fase).get(linea_base.id_fase)
                          if fase.relacion_estado_fase.nombre == "Finalizado":
                             fase.id_estado_fase = '4'
                          DBSession.flush()

                DBSession.flush()

            #Los archivos adjuntos del item a ser editado, se copian
            #para tener el registro de estos archivos con esa version de item
            archivos_item_editado = DBSession.query(ItemArchivo).filter_by(id_item=id_item).filter_by(version_item=version_a_editar)
            if archivos_item_editado != None:
               for archivo in archivos_item_editado:
                   nuevo_archivo = ItemArchivo()
                   nuevo_archivo.id_item = archivo.id_item
                   nuevo_archivo.version_item = version_a_editar
                   nuevo_archivo.nombre_archivo = archivo.nombre_archivo
                   nuevo_archivo.contenido_archivo = archivo.contenido_archivo
                   archivo.version_item = version_d_editar
                   DBSession.add(nuevo_archivo)
                   DBSession.flush()
                
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except SQLAlchemyError:
            flash(_("No se han guardado los cambios! SQLAlchemyError..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se han guardado los cambios! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        else:
            flash(_("Se han guardado los cambios!"), 'ok')

        redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

#--------------------------- Eliminacion de Items ------------------------------
    @expose('is2sap.templates.item.confirmar_eliminar')
    @require(predicates.has_any_permission('administracion','eliminar_item', msg=l_('No posee los permisos para eliminar de items')))
    def confirmar_eliminar(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):
        """Despliega confirmacion de eliminacion"""
        try:
            item = DBSession.query(Item).get(id_item)
            tipo_item = DBSession.query(TipoItem).get(item.id_tipo_item)
            linea_bases_item = item.linea_bases

            #Comprobamos que no se encuentre en una Linea Base
            if linea_bases_item != []:
               for linea_base_item in linea_bases_item:
                   flash(_("No puede Eliminar el Item! Se encuentra en una Linea Base..."), 'error')
                   redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

        except SQLAlchemyError:
            flash(_("No se pudo acceder a Eliminacion de Item! SQLAlchemyError..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Eliminacion de Item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

        return dict(nombre_modelo='Item', page='confirmar_eliminar', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, nombre_tipo_item=tipo_item.nombre, item=item)

    @expose()
    @require(predicates.has_any_permission('administracion','eliminar_item', msg=l_('No posee los permisos para eliminar de items')))
    def delete(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):
        """Metodo que elimina un registro de la base de datos"""
        try:
            global itemsAfectados
            global listaRelaciones
            itemsAfectados = []
            listaRelaciones = []
            
            itemsAfectados.append(id_item)

            for item_afectado in itemsAfectados:
                self.buscarRelaciones(item_afectado)

            #Ponemos a revision todos los items afectados por el Item eliminado
            for item_afectado in itemsAfectados:
                item_cambio = DBSession.query(Item).get(item_afectado)
                item_cambio.estado = "Revision"
                linea_bases_item = item_cambio.linea_bases
                if linea_bases_item != []:
                   for linea_base_item in linea_bases_item:
                       if linea_base_item.estado == "Aprobado":
                          id_linea_base = linea_base_item.id_linea_base 
                          linea_base = DBSession.query(LineaBase).get(id_linea_base)
                          linea_base.estado = "Revision"
                          fase = DBSession.query(Fase).get(linea_base.id_fase)
                          if fase.relacion_estado_fase.nombre == "Finalizado":
                             fase.id_estado_fase = '4'
                          DBSession.flush()
                DBSession.flush()

            #Eliminamos todas las Relaciones con sus Items inmediatos
            if listaRelaciones != []:
               hijos = DBSession.query(RelacionItem).filter_by(id_item1=id_item)
               antecesores = DBSession.query(RelacionItem).filter_by(id_item2=id_item)
               if hijos != []:
                  for hijo in hijos:
                      id_relacion = hijo.id_relacion
                      DBSession.delete(DBSession.query(RelacionItem).get(id_relacion))
                      DBSession.flush()
               if antecesores != []:
                  for antecesor in antecesores:
                      id_relacion = antecesor.id_relacion
                      DBSession.delete(DBSession.query(RelacionItem).get(id_relacion))
                      DBSession.flush()
                   
            #Por ultimo, eliminamos el Item logicamente y lo dejamos en estado "Desarrollo"
            item = DBSession.query(Item).get(id_item)
            item.vivo = False
            item.estado = "Desarrollo"
            linea_bases_item = item.linea_bases
            DBSession.flush()

            #Desasignamos automaticamente de la Linea Base en que se encuentra
            #si se encuentra en una Linea Base con estado distinto a "Aprobado"
            #if linea_bases_item != None:
            #   for linea_base_item in linea_bases_item:
            #       if linea_base_item.estado != "Aprobado":
            #          id_linea_base = linea_base_item.id_linea_base 
            #          linea_base = DBSession.query(LineaBase).get(id_linea_base)
            #          item.linea_bases.remove(linea_base)
            #          DBSession.flush()

            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se pudo eliminar! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except SQLAlchemyError:
            flash(_("No se pudo eliminar! SQLAlchemyError..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo eliminar! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        else:
            flash(_("Item eliminado!"), 'ok')

        redirect("/item/listado",id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

#--------------------------- Listado de Items ----------------------------------
    @expose("is2sap.templates.item.listado")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para eliminar de items')))
    def listado(self, id_proyecto, id_fase, id_tipo_item, page=1):
        """Metodo para listar todos los items de la base de datos"""
        try:
            items = DBSession.query(Item).filter_by(id_tipo_item=id_tipo_item).filter_by(vivo=True).order_by(Item.id_item)
            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
            currentPage = paginate.Page(items, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Listado de Items! SQLAlchemyError..."), 'error')
            redirect("/item/tipoItems", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Listado de Items! Hay Problemas con el servidor..."), 'error')
            redirect("/item/tipoItems", id_proyecto=id_proyecto, id_fase=id_fase)

        return dict(items=currentPage.items, page='listado_item', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, nombre_tipo_item=tipo_item.nombre, 
                    currentPage=currentPage)

    @expose("is2sap.templates.item.listado_detalles")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar')))
    def listado_detalles(self, id_proyecto, id_fase, id_tipo_item, id_item, page=1):
        """Metodo para listar todos los items de la base de datos"""
        try:
            detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item).order_by(ItemDetalle.id_item_detalle)
            currentPage = paginate.Page(detalles, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder al Detalle del Item! SQLAlchemyError..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder al Detalle del Item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

        return dict(detalles=currentPage.items, page='listado_detalles', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item, currentPage=currentPage)


#--------------------------- Revivir Items -------------------------------------
    @expose("is2sap.templates.item.listado_revivir")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar')))
    def listado_revivir(self, id_proyecto, id_fase, id_tipo_item, page=1):
        """Metodo para listar los items del tipo correspondiente que pueden ser revividos"""
        try:
            items = DBSession.query(Item).filter_by(id_tipo_item=id_tipo_item).filter_by(vivo=False).order_by(Item.id_item)
            currentPage = paginate.Page(items, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Items revivibles! SQLAlchemyError..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Items revivibles! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

        return dict(items=currentPage.items, page='listado_revivir', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, currentPage=currentPage)

    @expose("is2sap.templates.item.listado_detalles_revivir")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar')))
    def listado_detalles_revivir(self, id_proyecto, id_fase, id_tipo_item, id_item, page=1):
        """Metodo para listar los detalles del item a ser revivido"""
        try:
            item_detalle = DBSession.query(ItemDetalle).filter_by(id_item=id_item)
            currentPage = paginate.Page(item_detalle, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Detalles de Items revivibles! SQLAlchemyError..."), 'error')
            redirect("/item/listado_revivir", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Detalles de Items revivibles! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado_revivir", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

        return dict(item_detalle=currentPage.items, page='listado_detalles_revivir', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item, currentPage=currentPage)

    @expose()
    @require(predicates.has_any_permission('administracion','revivir_item', msg=l_('No posee los permisos para revivir Items')))
    def revivir_item(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):        
        """Metodo que revive un item que habia sido eliminado"""
        try:
            item = DBSession.query(Item).get(id_item)
            item.vivo = True
            item.estado = "Desarrollo"
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se pudo revivir el item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado_revivir", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except SQLAlchemyError:
            flash(_("No se pudo revivir el item! SQLAlchemyError..."), 'error')
            redirect("/item/listado_revivir", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo revivir el item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado_revivir", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        else:
            flash(_("Item revivido!"), 'ok')
           
        redirect("/item/listado_revivir", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

    @expose("is2sap.templates.item.revivir_desde_fase")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar')))
    def revivir_desde_fase(self, id_proyecto, id_fase, page=1):
        """Metodo para listar los items de la fase correspondiente que pueden ser revividos"""
        try:
            fase = DBSession.query(Fase).get(id_fase)
            tipo_items = fase.tipoitems
            items = []

            for tipo_item in tipo_items:
                id_tipo_item = tipo_item.id_tipo_item
                items_por_tipo = DBSession.query(Item).filter_by(id_tipo_item=id_tipo_item).filter_by(vivo=False).order_by(Item.id_item)
                for item in items_por_tipo:
                    items.append(item)

            nombre_fase = fase.nombre
            currentPage = paginate.Page(items, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Items revivibles! SQLAlchemyError..."), 'error')
            redirect("/item/fases", id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Items revivibles! Hay Problemas con el servidor..."), 'error')
            redirect("/item/fases", id_proyecto=id_proyecto)

        return dict(items=currentPage.items, page='revivir_desde_fase', id_proyecto=id_proyecto, 
                    id_fase=id_fase, nombre_fase=nombre_fase, currentPage=currentPage)

    @expose("is2sap.templates.item.detalles_revivir_desde_fase")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar')))
    def detalles_revivir_desde_fase(self, id_proyecto, id_fase, id_tipo_item, id_item, page=1):
        """Metodo para listar los detalles del item a ser revivido"""
        try:
            item_detalle = DBSession.query(ItemDetalle).filter_by(id_item=id_item)
            currentPage = paginate.Page(item_detalle, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Detalles de Items revivibles! SQLAlchemyError..."), 'error')
            redirect("/item/revivir_desde_fase", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Detalles de Items revivibles! Hay Problemas con el servidor..."), 'error')
            redirect("/item/revivir_desde_fase", id_proyecto=id_proyecto, id_fase=id_fase)

        return dict(item_detalle=currentPage.items, page='detalles_revivir_desde_fase', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item, currentPage=currentPage)

    @expose()
    @require(predicates.has_any_permission('administracion','revivir_item', msg=l_('No posee los permisos para revivir Items')))
    def revivir_item_desde_fase(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):        
        """Metodo que revive un item que habia sido eliminado"""
        try:
            item = DBSession.query(Item).get(id_item)
            item.vivo = True
            item.estado = "Desarrollo"
            DBSession.flush()
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se pudo revivir el item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/revivir_desde_fase", id_proyecto=id_proyecto, id_fase=id_fase)
        except SQLAlchemyError:
            flash(_("No se pudo revivir el item! SQLAlchemyError..."), 'error')
            redirect("/item/revivir_desde_fase", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se pudo revivir el item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/revivir_desde_fase", id_proyecto=id_proyecto, id_fase=id_fase)
        else:
            flash(_("Item revivido!"), 'ok')
           
        redirect("/item/revivir_desde_fase", id_proyecto=id_proyecto, id_fase=id_fase)


#--------------------------- Aprobacion de Items -------------------------------
    @expose()
    @require(predicates.has_any_permission('administracion','aprobar_item', msg=l_('No posee los permisos para aprobar!')))
    def aprobar(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):        
        """Metodo que cambia el estado de un item al de Aprobado"""
        try:
            # Esto busca los antecesores del item actual que se esta revisando
            antecesores = DBSession.query(RelacionItem).filter_by(id_item2=id_item).filter_by(tipo="Antecesor-Sucesor").order_by(RelacionItem.id_item1).all()
            item = DBSession.query(Item).get(id_item)
            fase = DBSession.query(Fase).get(id_fase)
	    
	    # Se emite un mensaje de error si el item no tiene antecesores(a excepción de la 1era. fase)	
	    if antecesores == [] and fase.numero_fase != 1:
			flash(_("El item no se puede aprobar. Requiere de un antecesor por lo menos..."), 'error')
               		redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

	    # Se comprueba si todos sus antecesores(padres y antecesores juntos) están aprobados
	    todos_antecesores = DBSession.query(RelacionItem).filter_by(id_item2=id_item).order_by(RelacionItem.id_item1)
	    if todos_antecesores != []:
		items_aprobados = 0
		total_items = 0
		for antecesor in todos_antecesores:
			item_antecesor=DBSession.query(Item).get(antecesor.id_item1)
			if item_antecesor.estado == 'Aprobado':
				items_aprobados = items_aprobados + 1
			total_items = total_items + 1
		print total_items
		print items_aprobados
		if total_items > items_aprobados:
			flash(_("El item no se puede aprobar. Requiere que todos sus padres y/o antecesores esten aprobados"), 'error')
               		redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

            if antecesores != []:
               if item.estado != "Aprobado": 
                  item.estado = "Aprobado"
                  DBSession.flush()
                  transaction.commit()
               else:
                  flash(_("El item ya esta aprobado..."), 'notice')
                  redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
            elif fase.numero_fase == 1:
               if item.estado != "Aprobado": 
                  item.estado = "Aprobado"
                  DBSession.flush()
                  transaction.commit()
               else:
                  flash(_("El item ya esta aprobado..."), 'notice')
                  redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
            
        except IntegrityError:
            transaction.abort()
            flash(_("No se pudo aprobar el Item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except SQLAlchemyError:
            flash(_("No se pudo aprobar el Item! SQLAlchemyError..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo aprobar el Item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        else:
            flash(_("Item aprobado!"), 'ok')
          
        redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

    @expose("is2sap.templates.item.listado_aprobar")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar!')))
    def listado_aprobar(self, id_proyecto, id_fase, page=1):
        """Metodo para listar todos los items de una fase correspondiente y que aun no estan aprobados"""
        try:
            fase = DBSession.query(Fase).get(id_fase)
            tipo_items = fase.tipoitems
            items = []

            for tipo_item in tipo_items:
                id_tipo_item = tipo_item.id_tipo_item
                items_por_tipo = DBSession.query(Item).filter_by(id_tipo_item=id_tipo_item).filter_by(vivo=True).order_by(Item.id_item)
                for item in items_por_tipo:
                    if item.estado != "Aprobado": 
                       items.append(item)

            nombre_fase = fase.nombre
            currentPage = paginate.Page(items, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Listado de Items por fase! SQLAlchemyError..."), 'error')
            redirect("/item/fases", id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Listado de Items por fase! Hay Problemas con el servidor..."), 'error')
            redirect("/item/fases", id_proyecto=id_proyecto)

        return dict(items=currentPage.items, page='listado_aprobar', id_proyecto=id_proyecto, 
                    id_fase=id_fase, nombre_fase=nombre_fase, currentPage=currentPage)

    @expose()
    @require(predicates.has_any_permission('administracion','aprobar_item', msg=l_('No posee los permisos para aprobar!')))
    def aprobar_desde_fase(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):        
        """Metodo que cambia el estado de un item al de Aprobado"""
        try:
            # Esto busca los antecesores del item actual que se esta revisando
            antecesores = DBSession.query(RelacionItem).filter_by(id_item2=id_item).filter_by(tipo="Antecesor-Sucesor").order_by(RelacionItem.id_item1).all()
            item = DBSession.query(Item).get(id_item)
            fase = DBSession.query(Fase).get(id_fase)

            if antecesores != None:
               if item.estado != "Aprobado": 
                  item.estado = "Aprobado"
                  DBSession.flush()
                  transaction.commit()
               else:
                  flash(_("El item ya esta aprobado..."), 'notice')
                  redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
            elif fase.numero_fase == 1:
               if item.estado != "Aprobado": 
                  item.estado = "Aprobado"
                  DBSession.flush()
                  transaction.commit()
               else:
                  flash(_("El item ya esta aprobado..."), 'notice')
                  redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
            else:
               flash(_("El item no se puede aprobar. Requiere de un antecesor por lo menos..."), 'error')
               redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

        except IntegrityError:
            transaction.abort()
            flash(_("No se pudo aprobar el Item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado_aprobar", id_proyecto=id_proyecto, id_fase=id_fase)
        except SQLAlchemyError:
            flash(_("No se pudo aprobar el Item! SQLAlchemyError..."), 'error')
            redirect("/item/listado_aprobar", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se pudo aprobar el Item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado_aprobar", id_proyecto=id_proyecto, id_fase=id_fase)
        else:
            flash(_("Item aprobado!"), 'ok')
          
        redirect("/item/listado_aprobar", id_proyecto=id_proyecto, id_fase=id_fase)

    @expose("is2sap.templates.item.listado_detalles_aprobar")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar!')))
    def listado_detalles_aprobar(self, id_proyecto, id_fase, id_tipo_item, id_item, page=1):
        """Metodo para listar los detalles de items a aprobar de una fase"""
        try:
            detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item).order_by(ItemDetalle.id_item_detalle)
            currentPage = paginate.Page(detalles, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder al Detalle del Item! SQLAlchemyError..."), 'error')
            redirect("/item/listado_aprobar", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder al Detalle del Item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado_aprobar", id_proyecto=id_proyecto, id_fase=id_fase)

        return dict(detalles=currentPage.items, page='listado_detalles_aprobar', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item, currentPage=currentPage)


#--------------------------- Revertir versiones de Items -----------------------
    @expose("is2sap.templates.item.listado_revertir")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar!')))
    def listado_revertir(self, id_proyecto, id_fase, id_tipo_item, id_item, page=1):
        """Metodo para listar las versiones revertibles de un item"""
        try:
            item_historial = DBSession.query(ItemHistorial).filter_by(id_item=id_item).order_by(ItemHistorial.version)
            currentPage = paginate.Page(item_historial, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Items revertibles! SQLAlchemyError..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Items revertibles! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

        return dict(item_historial=currentPage.items, page='listado_revertir', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item, currentPage=currentPage)

    @expose("is2sap.templates.item.listado_detalles_revertir")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar!')))
    def listado_detalles_revertir(self, id_proyecto, id_fase, id_tipo_item, id_item, version, page=1):
        """Metodo para listar todos los items de la base de datos"""
        try:
            item_detalle_historial = DBSession.query(ItemDetalleHistorial).filter_by(id_item=id_item).filter_by(version=version)
            currentPage = paginate.Page(item_detalle_historial, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a los Detalles del Item revertible! SQLAlchemyError..."), 'error')
            redirect("/item/listado_revertir", id_proyecto=id_proyecto, id_fase=id_fase, 
                     id_tipo_item=id_tipo_item, id_item=id_item)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a los Detalles del Item revertible! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado_revertir", id_proyecto=id_proyecto, id_fase=id_fase, 
                     id_tipo_item=id_tipo_item, id_item=id_item)

        return dict(item_detalle_historial=currentPage.items, page='listado_detalles_revertir', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item, version=version, currentPage=currentPage)

    @expose()
    @require(predicates.has_any_permission('administracion','revertir_item', msg=l_('No posee los permisos para revertir!')))
    def revertir_item(self, id_proyecto, id_fase, id_tipo_item, id_historial_item, **kw):        
        """Metodo que actualiza la base de datos"""
        try:
            #Consultamos el item que se encuentra en el historial
            item_a_revertir = DBSession.query(ItemHistorial).get(id_historial_item)
            version_a_revertir = item_a_revertir.version
            id_item = item_a_revertir.id_item
            item_actual = DBSession.query(Item).get(id_item)
            version_actual = item_actual.version
            linea_bases_item = item_actual.linea_bases

            #Comprobamos que el Item actual no se encuentre en una Linea Base
            if linea_bases_item != []:
               for linea_base_item in linea_bases_item:
                   flash(_("No se puede revertir! El Item actual se encuentra en una Linea Base..."), 'error')
                   redirect("/item/listado_revertir", id_proyecto=id_proyecto, id_fase=id_fase, 
                            id_tipo_item=id_tipo_item, id_item=id_item)

            #Cargamos en el historial el item que esta con los datos actuales
            item_hist_nuevo = ItemHistorial()
            item_hist_nuevo.id_item = item_actual.id_item
            item_hist_nuevo.id_tipo_item = item_actual.id_tipo_item
            item_hist_nuevo.codigo = item_actual.codigo
            item_hist_nuevo.descripcion = item_actual.descripcion
            item_hist_nuevo.complejidad = item_actual.complejidad
            item_hist_nuevo.prioridad = item_actual.prioridad
            item_hist_nuevo.estado = item_actual.estado
            item_hist_nuevo.version = item_actual.version
            item_hist_nuevo.observacion = item_actual.observacion
            item_hist_nuevo.fecha_modificacion = item_actual.fecha_modificacion
            DBSession.add(item_hist_nuevo)
        
            #Cargamos el item actual con los datos de la version a revertir 
            item_actual.id_tipo_item = item_a_revertir.id_tipo_item
            item_actual.codigo = item_a_revertir.codigo
            item_actual.descripcion = item_a_revertir.descripcion
            item_actual.complejidad = item_a_revertir.complejidad
            item_actual.prioridad = item_a_revertir.prioridad
            item_actual.estado = "Desarrollo"
            item_actual.version = int(item_actual.version) + 1
            version_nueva_item = item_actual.version
            item_actual.observacion = item_a_revertir.observacion
            item_actual.fecha_modificacion = item_a_revertir.fecha_modificacion
            item_actual.vivo = True

            #Consultamos los detalles actuales del item
            detalles_actuales = DBSession.query(ItemDetalle).filter_by(id_item=id_item)
            atributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item).all()
            lista_id_atributo = []

            for atributo in atributos:
                lista_id_atributo.append(atributo.id_atributo)

            #Cargamos en el historial los detalles actuales del item
            for detalle in detalles_actuales:
                lista_id_atributo.remove(detalle.id_atributo)
                item_detalle_historial = ItemDetalleHistorial()
                item_detalle_historial.id_item = detalle.id_item
                item_detalle_historial.id_item_detalle = detalle.id_item_detalle
                item_detalle_historial.id_atributo = detalle.id_atributo
                item_detalle_historial.nombre_atributo = detalle.nombre_atributo
                item_detalle_historial.valor = detalle.valor
                item_detalle_historial.version = version_actual

                #Consultamos el detalle a revertir, de la version del item correspondiente
                detalle_a_revertir = DBSession.query(ItemDetalleHistorial).filter_by(id_item_detalle=detalle.id_item_detalle).filter_by(version=version_a_revertir).first()

                #Cargamos el detalle del item con los valores de la version a revertir
                if detalle_a_revertir!=None:
                   detalle.valor = detalle_a_revertir.valor
                else:
                   detalle.valor = ""

                DBSession.add(item_detalle_historial)
                DBSession.flush()

            #Los detalles que no existian en la version a revertir se establecen a vacio
            for id_atributo in lista_id_atributo:
                atributo = DBSession.query(Atributo).get(id_atributo)
                itemDetalle = ItemDetalle()
                itemDetalle.id_item = id_item
                itemDetalle.id_atributo = atributo.id_atributo
                itemDetalle.nombre_atributo = atributo.nombre
                itemDetalle.valor = ""
                DBSession.add(itemDetalle)
                DBSession.flush()

            #Los archivos adjuntos de la version del item a se revertido, se copian
            #y se les coloca con la version actual del item revertido.
            archivos_item_revertido = DBSession.query(ItemArchivo).filter_by(id_item=id_item).filter_by(version_item=version_a_revertir)
            if archivos_item_revertido != None:
               for archivo in archivos_item_revertido:
                   nuevo_archivo = ItemArchivo()
                   nuevo_archivo.id_item = archivo.id_item
                   nuevo_archivo.version_item = version_nueva_item
                   nuevo_archivo.nombre_archivo = archivo.nombre_archivo
                   nuevo_archivo.contenido_archivo = archivo.contenido_archivo
                   DBSession.add(nuevo_archivo)
                   DBSession.flush()

            #Buscamos todas las relaciones que tenia el Item en la version a revertir
            relaciones_revertir1 = DBSession.query(RelacionHistorial).filter_by(id_item1=id_item).filter_by(version_modif=version_a_revertir)
	    relaciones_revertir2 = DBSession.query(RelacionHistorial).filter_by(id_item2=id_item).filter_by(version_modif=version_a_revertir)
	    relaciones_revertir=[]

            for relacion in relaciones_revertir1:
		relaciones_revertir.append(relacion)
	    for relacion in relaciones_revertir2:
		relaciones_revertir.append(relacion)
			
            #Buscamos todos los Item con los que estaba relacionado en esas relaciones a revertir
            #Cargamos en una Lista todos los items que aun estan vivos
            relaciones_a_restablecer = []
            if relaciones_revertir != []:
               for relacion_revertir in relaciones_revertir:
                   id_item1 = relacion_revertir.id_item1
                   id_item2 = relacion_revertir.id_item2
                   if id_item1 == id_item:
                      item_a_relacionar = DBSession.query(Item).get(id_item2)
                      if item_a_relacionar.vivo == True:
                         relaciones_a_restablecer.append(relacion_revertir)
                   else:
                      item_a_relacionar = DBSession.query(Item).get(id_item1)
                      if item_a_relacionar.vivo == True:
                         relaciones_a_restablecer.append(relacion_revertir)

            #Antes de Eliminar las relaciones actuales, se debe poner a "Revision"
            #todos los items afectados
            global itemsAfectados
            global listaRelaciones
            itemsAfectados = []
            listaRelaciones = []
            
            itemsAfectados.append(id_item)

            for item_afectado in itemsAfectados:
                self.buscarRelaciones(item_afectado)

            for item_afectado in itemsAfectados:
                item_cambio = DBSession.query(Item).get(item_afectado)
                item_cambio.estado = "Revision"
                linea_bases_item = item_cambio.linea_bases
                if linea_bases_item != []:
                   for linea_base_item in linea_bases_item:
                       if linea_base_item.estado == "Aprobado":
                          id_linea_base = linea_base_item.id_linea_base 
                          linea_base = DBSession.query(LineaBase).get(id_linea_base)
                          linea_base.estado = "Revision"
                          fase = DBSession.query(Fase).get(linea_base.id_fase)
                          if fase.relacion_estado_fase.nombre == "Finalizado":
                             fase.id_estado_fase = '4'
                          DBSession.flush()
                DBSession.flush()

            #Buscamos todas las relaciones que tiene antes de revertir, para enviar
            #esas relaciones al historial de relaciones. Se eliminan las relacines actuales del Item
            hijos = DBSession.query(RelacionItem).filter_by(id_item1=id_item)
            antecesores = DBSession.query(RelacionItem).filter_by(id_item2=id_item)
            if hijos != []:
               for hijo in hijos:
                   id_relacion = hijo.id_relacion
                   relacion_historial = RelacionHistorial()
                   relacion_historial.tipo = hijo.tipo
                   relacion_historial.id_item1 = hijo.id_item1
                   relacion_historial.id_item2 = hijo.id_item2
                   relacion_historial.version_modif = version_actual
                   DBSession.add(relacion_historial)
                   DBSession.delete(DBSession.query(RelacionItem).get(id_relacion))
                   DBSession.flush()
            if antecesores != []:
               for antecesor in antecesores:
                   id_relacion = antecesor.id_relacion
                   relacion_historial = RelacionHistorial()
                   relacion_historial.tipo = antecesor.tipo
                   relacion_historial.id_item1 = antecesor.id_item1
                   relacion_historial.id_item2 = antecesor.id_item2
                   relacion_historial.version_modif = version_actual
                   DBSession.add(relacion_historial)
                   DBSession.delete(DBSession.query(RelacionItem).get(id_relacion))
                   DBSession.flush()

            #Restablecer las relaciones revertibles
            if relaciones_a_restablecer != []:
               for relacion_a_restablecer in relaciones_a_restablecer:
                   nueva_relacion = RelacionItem()
                   nueva_relacion.id_item1 = relacion_a_restablecer.id_item1
                   nueva_relacion.id_item2 = relacion_a_restablecer.id_item2
                   nueva_relacion.tipo = relacion_a_restablecer.tipo
                   DBSession.add(nueva_relacion)
                   DBSession.flush()

            #Despues de Reestablecer las relaciones revertibles, se debe poner a "Revision"
            #todos los items afectados
            global itemsAfectados
            global listaRelaciones
            itemsAfectados = []
            listaRelaciones = []
            
            itemsAfectados.append(id_item)

            for item_afectado in itemsAfectados:
                self.buscarRelaciones(item_afectado)

            for item_afectado in itemsAfectados:
                item_cambio = DBSession.query(Item).get(item_afectado)
                item_cambio.estado = "Revision"
                linea_bases_item = item_cambio.linea_bases
                if linea_bases_item != []:
                   for linea_base_item in linea_bases_item:
                       if linea_base_item.estado == "Aprobado":
                          id_linea_base = linea_base_item.id_linea_base 
                          linea_base = DBSession.query(LineaBase).get(id_linea_base)
                          linea_base.estado = "Revision"
                          fase = DBSession.query(Fase).get(linea_base.id_fase)
                          if fase.relacion_estado_fase.nombre == "Finalizado":
                             fase.id_estado_fase = '4'
                          DBSession.flush()
                DBSession.flush()

            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se pudo revertir el Item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado_revertir", id_proyecto=id_proyecto, id_fase=id_fase, 
                     id_tipo_item=id_tipo_item, id_item=id_item)
        except SQLAlchemyError:
            flash(_("No se pudo revertir el Item! SQLAlchemyError..."), 'error')
            redirect("/item/listado_revertir", id_proyecto=id_proyecto, id_fase=id_fase, 
                     id_tipo_item=id_tipo_item, id_item=id_item)
        except (AttributeError, NameError):
            flash(_("No se pudo revertir el Item! Hay Problemas de Atributos o de Nombres con el servidor..."), 'error')
            redirect("/item/listado_revertir", id_proyecto=id_proyecto, id_fase=id_fase, 
                     id_tipo_item=id_tipo_item, id_item=id_item)
        else:
            flash(_("Item revertido!"), 'ok')
           
        redirect("/item/listado_revertir", id_proyecto=id_proyecto, id_fase=id_fase, 
                 id_tipo_item=id_tipo_item, id_item=id_item)

    @expose("is2sap.templates.item.revertir_desde_fase")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar')))
    def revertir_desde_fase(self, id_proyecto, id_fase, page=1):
        """Metodo para listar todos los items revertibles de una determinada fase"""
        try:
            fase = DBSession.query(Fase).get(id_fase)
            tipo_items = fase.tipoitems
            items_historial = []

            for tipo_item in tipo_items:
                id_tipo_item = tipo_item.id_tipo_item
                items_historial_por_tipo = DBSession.query(ItemHistorial).filter_by(id_tipo_item=id_tipo_item).order_by(ItemHistorial.id_item)
                for item in items_historial_por_tipo:
                    item_actual = DBSession.query(Item).get(item.id_item)
                    if item_actual.vivo == True:
                       items_historial.append(item)

            nombre_fase = fase.nombre
            currentPage = paginate.Page(items_historial, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Items revertibles! SQLAlchemyError..."), 'error')
            redirect("/item/fases", id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Items revertibles! Hay Problemas con el servidor..."), 'error')
            redirect("/item/fases", id_proyecto=id_proyecto)

        return dict(items_historial=currentPage.items, page='revertir_desde_fase', id_proyecto=id_proyecto, 
                    id_fase=id_fase, nombre_fase=nombre_fase, currentPage=currentPage)

    @expose("is2sap.templates.item.detalles_revertir_desde_fase")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar')))
    def detalles_revertir_desde_fase(self, id_proyecto, id_fase, id_tipo_item, id_item, version, page=1):
        """Metodo para listar todos los items de la base de datos"""
        try:
            item_detalle_historial = DBSession.query(ItemDetalleHistorial).filter_by(id_item=id_item).filter_by(version=version)
            currentPage = paginate.Page(item_detalle_historial, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a los Detalles del Item revertible! SQLAlchemyError..."), 'error')
            redirect("/item/revertir_desde_fase", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a los Detalles del Item revertible! Hay Problemas con el servidor..."), 'error')
            redirect("/item/revertir_desde_fase", id_proyecto=id_proyecto, id_fase=id_fase)

        return dict(item_detalle_historial=currentPage.items, page='detalles_revertir_desde_fase', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item, version=version, currentPage=currentPage)

    @expose()
    @require(predicates.has_any_permission('administracion','revertir_item', msg=l_('No posee los permisos para revertir items!')))
    def revertir_item_desde_fase(self, id_proyecto, id_fase, id_tipo_item, id_historial_item, **kw):        
        """Metodo que actualiza la base de datos"""
        try:
            #Consultamos el item que se encuentra en el historial
            item_a_revertir = DBSession.query(ItemHistorial).get(id_historial_item)
            version_a_revertir = item_a_revertir.version
            id_item = item_a_revertir.id_item
            item_actual = DBSession.query(Item).get(id_item)
            version_actual = item_actual.version
            linea_bases_item = item_actual.linea_bases

            #Comprobamos que el Item actual no se encuentre en una Linea Base
            if linea_bases_item != []:
               for linea_base_item in linea_bases_item:
                   flash(_("No se puede revertir! El Item actual se encuentra en una Linea Base..."), 'error')
                   redirect("/item/revertir_desde_fase", id_proyecto=id_proyecto, id_fase=id_fase)

            #Cargamos en el historial el item que esta con los datos actuales
            item_hist_nuevo = ItemHistorial()
            item_hist_nuevo.id_item = item_actual.id_item
            item_hist_nuevo.id_tipo_item = item_actual.id_tipo_item
            item_hist_nuevo.codigo = item_actual.codigo
            item_hist_nuevo.descripcion = item_actual.descripcion
            item_hist_nuevo.complejidad = item_actual.complejidad
            item_hist_nuevo.prioridad = item_actual.prioridad
            item_hist_nuevo.estado = item_actual.estado
            item_hist_nuevo.version = item_actual.version
            item_hist_nuevo.observacion = item_actual.observacion
            item_hist_nuevo.fecha_modificacion = item_actual.fecha_modificacion
            DBSession.add(item_hist_nuevo)
        
            #Cargamos el item actual con los datos de la version a revertir 
            item_actual.id_tipo_item = item_a_revertir.id_tipo_item
            item_actual.codigo = item_a_revertir.codigo
            item_actual.descripcion = item_a_revertir.descripcion
            item_actual.complejidad = item_a_revertir.complejidad
            item_actual.prioridad = item_a_revertir.prioridad
            item_actual.estado = "Desarrollo"
            item_actual.version = int(item_actual.version) + 1
            version_nueva_item = item_actual.version
            item_actual.observacion = item_a_revertir.observacion
            item_actual.fecha_modificacion = item_a_revertir.fecha_modificacion
            item_actual.vivo = True

            #Consultamos los detalles actuales del item
            detalles_actuales = DBSession.query(ItemDetalle).filter_by(id_item=id_item)
            atributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item).all()
            lista_id_atributo = []

            for atributo in atributos:
                lista_id_atributo.append(atributo.id_atributo)

            #Cargamos en el historial los detalles actuales del item
            for detalle in detalles_actuales:
                lista_id_atributo.remove(detalle.id_atributo)
                item_detalle_historial = ItemDetalleHistorial()
                item_detalle_historial.id_item = detalle.id_item
                item_detalle_historial.id_item_detalle = detalle.id_item_detalle
                item_detalle_historial.id_atributo = detalle.id_atributo
                item_detalle_historial.nombre_atributo = detalle.nombre_atributo
                item_detalle_historial.valor = detalle.valor
                item_detalle_historial.version = version_actual

                #Consultamos el detalle a revertir, de la version del item correspondiente
                detalle_a_revertir = DBSession.query(ItemDetalleHistorial).filter_by(id_item_detalle=detalle.id_item_detalle).filter_by(version=version_a_revertir).first()

                #Cargamos el detalle del item con los valores de la version a revertir
                if detalle_a_revertir!=None:
                   detalle.valor = detalle_a_revertir.valor
                else:
                   detalle.valor = ""

                DBSession.add(item_detalle_historial)
                DBSession.flush()

            #Los detalles que no existian en la version a revertir se establecen a vacio
            for id_atributo in lista_id_atributo:
                atributo = DBSession.query(Atributo).get(id_atributo)
                itemDetalle = ItemDetalle()
                itemDetalle.id_item = id_item
                itemDetalle.id_atributo = atributo.id_atributo
                itemDetalle.nombre_atributo = atributo.nombre
                itemDetalle.valor = ""
                DBSession.add(itemDetalle)
                DBSession.flush()

            #Los archivos adjuntos de la version del item a se revertido, se copian
            #y se les coloca con la version actual del item revertido.
            archivos_item_editado = DBSession.query(ItemArchivo).filter_by(id_item=id_item).filter_by(version_item=version_a_revertir)
            if archivos_item_editado != None:
               for archivo in archivos_item_editado:
                   nuevo_archivo = ItemArchivo()
                   nuevo_archivo.id_item = archivo.id_item
                   nuevo_archivo.version_item = version_nueva_item
                   nuevo_archivo.nombre_archivo = archivo.nombre_archivo
                   nuevo_archivo.contenido_archivo = archivo.contenido_archivo
                   DBSession.add(nuevo_archivo)
                   DBSession.flush()

            #Buscamos todas las relaciones que tenia el Item en la version a revertir
            relaciones_revertir1 = DBSession.query(RelacionHistorial).filter_by(id_item1=id_item).filter_by(version_modif=version_a_revertir)
	    relaciones_revertir2 = DBSession.query(RelacionHistorial).filter_by(id_item2=id_item).filter_by(version_modif=version_a_revertir)
	    relaciones_revertir=[]

            for relacion in relaciones_revertir1:
		relaciones_revertir.append(relacion)
	    for relacion in relaciones_revertir2:
		relaciones_revertir.append(relacion)
			
            #Buscamos todos los Item con los que estaba relacionado en esas relaciones a revertir
            #Cargamos en una Lista todos los items que aun estan vivos
            relaciones_a_restablecer = []
            if relaciones_revertir != None:
               for relacion_revertir in relaciones_revertir:
                   id_item1 = relacion_revertir.id_item1
                   id_item2 = relacion_revertir.id_item2
                   if id_item1 == id_item:
                      item_a_relacionar = DBSession.query(Item).get(id_item2)
                      if item_a_relacionar.vivo == True:
                         relaciones_a_restablecer.append(relacion_revertir)
                   else:
                      item_a_relacionar = DBSession.query(Item).get(id_item1)
                      if item_a_relacionar.vivo == True:
                         relaciones_a_restablecer.append(relacion_revertir)

            #Antes de Eliminar las relaciones actuales, se debe poner a "Revision"
            #todos los items afectados
            global itemsAfectados
            global listaRelaciones
            itemsAfectados = []
            listaRelaciones = []
            
            itemsAfectados.append(id_item)

            for item_afectado in itemsAfectados:
                self.buscarRelaciones(item_afectado)

            for item_afectado in itemsAfectados:
                item_cambio = DBSession.query(Item).get(item_afectado)
                item_cambio.estado = "Revision"
                linea_bases_item = item_cambio.linea_bases
                if linea_bases_item != None:
                   for linea_base_item in linea_bases_item:
                       if linea_base_item.estado == "Aprobado":
                          id_linea_base = linea_base_item.id_linea_base 
                          linea_base = DBSession.query(LineaBase).get(id_linea_base)
                          linea_base.estado = "Revision"
                          fase = DBSession.query(Fase).get(linea_base.id_fase)
                          if fase.relacion_estado_fase.nombre == "Finalizado":
                             fase.id_estado_fase = '4'
                          DBSession.flush()
                DBSession.flush()

            #Buscamos todas las relaciones que tenia antes de revertir, para enviar
            #esas relaciones al historial de relaciones. Se eliminan las relacines actuales del Item
            hijos = DBSession.query(RelacionItem).filter_by(id_item1=id_item)
            antecesores = DBSession.query(RelacionItem).filter_by(id_item2=id_item)
            if hijos != None:
               for hijo in hijos:
                   id_relacion = hijo.id_relacion
                   relacion_historial = RelacionHistorial()
                   relacion_historial.tipo = hijo.tipo
                   relacion_historial.id_item1 = hijo.id_item1
                   relacion_historial.id_item2 = hijo.id_item2
                   relacion_historial.version_modif = version_actual
                   DBSession.add(relacion_historial)
                   DBSession.delete(DBSession.query(RelacionItem).get(id_relacion))
                   DBSession.flush()
            if antecesores != None:
               for antecesor in antecesores:
                   id_relacion = antecesor.id_relacion
                   relacion_historial = RelacionHistorial()
                   relacion_historial.tipo = antecesor.tipo
                   relacion_historial.id_item1 = antecesor.id_item1
                   relacion_historial.id_item2 = antecesor.id_item2
                   relacion_historial.version_modif = version_actual
                   DBSession.add(relacion_historial)
                   DBSession.delete(DBSession.query(RelacionItem).get(id_relacion))
                   DBSession.flush()

            #Restablecer las relaciones revertibles
            if relaciones_a_restablecer != None:
               for relacion_a_restablecer in relaciones_a_restablecer:
                   nueva_relacion = RelacionItem()
                   nueva_relacion.id_item1 = relacion_a_restablecer.id_item1
                   nueva_relacion.id_item2 = relacion_a_restablecer.id_item2
                   nueva_relacion.tipo = relacion_a_restablecer.tipo
                   DBSession.add(nueva_relacion)
                   DBSession.flush()

            #Despues de Reestablecer las relaciones revertibles, se debe poner a "Revision"
            #todos los items afectados
            global itemsAfectados
            global listaRelaciones
            itemsAfectados = []
            listaRelaciones = []
            
            itemsAfectados.append(id_item)

            for item_afectado in itemsAfectados:
                self.buscarRelaciones(item_afectado)

            for item_afectado in itemsAfectados:
                item_cambio = DBSession.query(Item).get(item_afectado)
                item_cambio.estado = "Revision"
                linea_bases_item = item_cambio.linea_bases
                if linea_bases_item != None:
                   for linea_base_item in linea_bases_item:
                       if linea_base_item.estado == "Aprobado":
                          id_linea_base = linea_base_item.id_linea_base 
                          linea_base = DBSession.query(LineaBase).get(id_linea_base)
                          linea_base.estado = "Revision"
                          fase = DBSession.query(Fase).get(linea_base.id_fase)
                          if fase.relacion_estado_fase.nombre == "Finalizado":
                             fase.id_estado_fase = '4'
                          DBSession.flush()
                DBSession.flush()

            transaction.commit()
        except IntegrityError:
            transaction.abort()
            flash(_("No se pudo revertir el Item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/revertir_desde_fase", id_proyecto=id_proyecto, id_fase=id_fase)
        except SQLAlchemyError:
            flash(_("No se pudo revertir el Item! SQLAlchemyError..."), 'error')
            redirect("/item/revertir_desde_fase", id_proyecto=id_proyecto, id_fase=id_fase)
        except (AttributeError, NameError):
            flash(_("No se pudo revertir el Item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/revertir_desde_fase", id_proyecto=id_proyecto, id_fase=id_fase)
        else:
            flash(_("Item revertido!"), 'ok')
           
        redirect("/item/revertir_desde_fase", id_proyecto=id_proyecto, id_fase=id_fase)


#--------------------------- Listado de Proyectos ------------------------------
    @expose("is2sap.templates.item.listado_proyectos")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar')))
    def proyectos(self,page=1):
        """Metodo para listar todos los Proyectos existentes de la base de datos"""
        try:
            usuario = DBSession.query(Usuario).filter_by(nombre_usuario=request.identity['repoze.who.userid']).first()
            todosProyectos = usuario.proyectos

            proyectos = []

            if proyectos != None:
               for proyecto in todosProyectos:
                   if proyecto.iniciado == True:
                      proyectos.append(proyecto)

            currentPage = paginate.Page(proyectos, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Proyectos Iniciados! SQLAlchemyError..."), 'error')
            redirect("/desa")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Proyectos Iniciados! Hay Problemas con el servidor..."), 'error')
            redirect("/desa")

        return dict(proyectos=currentPage.items, page='listado_proyectos', currentPage=currentPage)


#--------------------------- Listado de Fases por Proyecto ----------------------
    @expose("is2sap.templates.item.listado_fases")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar')))
    def fases(self,id_proyecto, page=1):
        """Metodo para listar las Fases de un proyecto """
        try:
            fases_todas = DBSession.query(Fase).join(Fase.relacion_estado_fase).filter(Fase.id_proyecto==id_proyecto).options(contains_eager(Fase.relacion_estado_fase)).order_by(Fase.numero_fase)
            nombreProyecto = DBSession.query(Proyecto.nombre).filter_by(id_proyecto=id_proyecto).first()

            fases = []

            for fase in fases_todas:
                if fase.relacion_estado_fase.nombre_estado != "Inicial":
                   fases.append(fase)

            currentPage = paginate.Page(fases, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Fases de Proyecto! SQLAlchemyError..."), 'error')
            redirect("/item/proyectos")
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Fases de Proyecto! Hay Problemas con el servidor..."), 'error')
            redirect("/item/proyectos")

        return dict(fases=currentPage.items, page='listado_fases', nombre_proyecto=nombreProyecto, 
                    id_proyecto=id_proyecto, currentPage=currentPage)


#--------------------------- Listado de Tipo de Items por Fase -----------------
    @expose("is2sap.templates.item.listado_tipo_items")
    @require(predicates.has_any_permission('administracion','desarrollo', msg=l_('No posee los permisos para visualizar')))
    def tipoItems(self, id_proyecto, id_fase, page=1):
        """Metodo para listar los Tipos de Items de una Fase """
        try:
            fase = DBSession.query(Fase).get(id_fase)
            tipoItems = fase.tipoitems
            currentPage = paginate.Page(tipoItems, page, items_per_page=10)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Tipo de Items de Fase! SQLAlchemyError..."), 'error')
            redirect("/item/fases", id_proyecto=id_proyecto)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Tipo de Items de Fase! Hay Problemas con el servidor..."), 'error')
            redirect("/item/fases", id_proyecto=id_proyecto)

        return dict(tipoItems=currentPage.items, page='listado_tipo_items', 
                    nombre_fase=fase.nombre, id_proyecto=id_proyecto, id_fase=id_fase, currentPage=currentPage)

#------------ Busca todos los items relacionados a un item en particular--------        
    def buscarRelaciones(self, idItemActual):
        global itemsAfectados
        global listaRelaciones
        # En esta busqueda yo busco todos los que son hijos del item actual que esta revisando
        hijos = DBSession.query(RelacionItem).filter_by(id_item1=idItemActual).filter_by(tipo="Padre-Hijo").order_by(RelacionItem.id_item2).all()
        for hijo in hijos:
            relacion = (hijo.id_item1, hijo.id_item2)
            if listaRelaciones.count(relacion) == 0:
                listaRelaciones.append(relacion)
            if itemsAfectados.count(hijo.id_item2) == 0:
                itemsAfectados.append(hijo.id_item2)

        # Esto busca los padres del item actual que esta revisando
        padres = DBSession.query(RelacionItem).filter_by(id_item2=idItemActual).filter_by(tipo="Padre-Hijo").order_by(RelacionItem.id_item1).all()
        for padre in padres:
            relacion = (padre.id_item1, padre.id_item2)
            if listaRelaciones.count(relacion) == 0:
                listaRelaciones.append(relacion)
            if itemsAfectados.count(padre.id_item1) == 0:
                itemsAfectados.append(padre.id_item1)

        # Esto busca los antecesores del item actual que se esta revisando
        antecesores = DBSession.query(RelacionItem).filter_by(id_item2=idItemActual).filter_by(tipo="Antecesor-Sucesor").order_by(RelacionItem.id_item1).all()
        for antecesor in antecesores:
            relacion = (antecesor.id_item1, antecesor.id_item2)
            if listaRelaciones.count(relacion) == 0:
                listaRelaciones.append(relacion)
            if itemsAfectados.count(antecesor.id_item1) == 0:
                itemsAfectados.append(antecesor.id_item1)

        # Esto busca los sucesores del item actual que se esta revisando
        sucesores = DBSession.query(RelacionItem).filter_by(id_item1=idItemActual).filter_by(tipo="Antecesor-Sucesor").order_by(RelacionItem.id_item2).all()
        for sucesor in sucesores:
            relacion = (sucesor.id_item1, sucesor.id_item2)
            if listaRelaciones.count(relacion) == 0:
                listaRelaciones.append(relacion)
            if itemsAfectados.count(sucesor.id_item2) == 0:
                itemsAfectados.append(sucesor.id_item2)

#------- Calcula el impacto que produce el cambio de un item en particular------
    @expose("is2sap.templates.item.GraficoImpacto")
    @require(predicates.has_any_permission('administracion','calcular_impacto', msg=l_('No posee los permisos para visualizar el Impacto')))
    def calcularImpacto(self, id_proyecto, itemActual):
        global itemsAfectados
        global listaRelaciones
        itemsAfectados = []
        listaRelaciones = []
        id_item_actual= int(itemActual)
        itemsAfectados.append(id_item_actual) # este realiza la primera insercion del item para el cual se quiere calcular el impacto
        impactoTotal=0
        for item in itemsAfectados:
            self.buscarRelaciones(item)
        itemsAfectados.sort()
        listaRelaciones.sort()
        print "Lista de Items: ", itemsAfectados
        print "Lista de Relaciones", listaRelaciones
        ## traer las fases del proyecto y luego los items de las fases, sumar por fases, y luego un total
        fases = DBSession.query(Fase).filter_by(id_proyecto=id_proyecto).order_by(Fase.id_fase)
        sumaImpactoPorFases=[]


        G=nx.DiGraph(weighted=False)
        G.posicion={}
        G.poslabels={}
        G.labels={}
        G.colores={}
        G.posComp={}
        G.complej={}
        
        posX=0
        for fase in fases:
            y=30
            itemsDeFase = DBSession.query(Item).join(TipoItem).join(Fase).filter(Fase.id_fase==fase.id_fase).all()
            impactoPorFase=0
            for item in itemsDeFase:
                if itemsAfectados.count(item.id_item) == 1:
                    x=posX+random.random()
                    y=y-1 
                    G.add_node(item.id_item)
                    G.posicion[item.id_item]=(x, y)
                    G.colores[item.id_item]='coral'
                    G.poslabels[item.id_item]=(x, y+0.30)                    
                    G.labels[item.id_item]='Cod:'+item.codigo
                    G.posComp[item.id_item]=(x, y+0.18)                    
                    G.complej[item.id_item]='Comp:'+item.complejidad
                    impactoPorFase = impactoPorFase + int(item.complejidad)
                else:
                    x=posX+random.random()
                    y=y-1 
                    G.add_node(item.id_item)
                    G.posicion[item.id_item]=(x, y)
                    G.poslabels[item.id_item]=(x, y+0.30)
                    G.colores[item.id_item]='grey'
                    G.labels[item.id_item]='Cod:'+item.codigo
                    G.posComp[item.id_item]=(x, y+0.18)                    
                    G.complej[item.id_item]='Comp:'+item.complejidad
            posX=posX+3
            sumaImpactoPorFases.append([fase,impactoPorFase])
            impactoTotal = impactoTotal + impactoPorFase
            print "El impacto de la "+fase.nombre+" es :", impactoPorFase
        print "El impacto total es :", impactoTotal   

        
        #graph = pydot.Dot(graph_type='digraph')        
        #for i in itemsAfectados:
        #    graph.add_node(pydot.Node(str(i)))
        for x in listaRelaciones:
            G.add_edge(x[0], x[1])
            #graph.add_edge(pydot.Edge(str(x[0]), str(x[1])))
        #graph.write_png('../IS2SAP/is2sap/public/images/example2_graph.png')
        plt.clf()
        nx.draw(G, G.posicion, node_color=[G.colores[v] for v in G], node_size=700)
        nx.draw_networkx_labels(G, G.poslabels, G.labels, fontsize=14)
        nx.draw_networkx_labels(G, G.posComp, G.complej, fontsize=14)
        
        plt.savefig("../IS2SAP/is2sap/public/images/example2_graph.png")
        #plt.show()
        return dict(nombre_modelo="CalculoImpacto", impactoTotal=impactoTotal, sumaImpactoPorFases=sumaImpactoPorFases)
