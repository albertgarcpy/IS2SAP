# -*- coding: utf-8 -*-
"""Controlador de Item"""
from tg import expose, flash, require, url, request, redirect
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

public_dirname = os.path.join(os.path.abspath(resource_filename('is2sap', 'public')))
items_dirname = os.path.join(public_dirname, 'items')


from is2sap.widgets.mi_validador.mi_validador import *
from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import TipoItem, Item, Proyecto, Usuario, Fase, Atributo, ItemDetalle, ItemHistorial, ItemDetalleHistorial, LineaBase, LineaBase_Item
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController
from is2sap.widgets.item_form import ItemForm, EditItemForm


__all__ = ['ItemController']


class ItemController(BaseController):

    allow_only = has_permission('edicion',
                                msg=l_('Solo para usuarios con permiso "edicion"'))
    
    @expose()
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='Item', page='index_item')

    @expose('is2sap.templates.item.nuevo')
    def nuevo(self, id_proyecto, id_fase, id_tipo_item, **kw):
        """Despliega el formulario para anhadir un nuevo Item."""

        complejidad_options = ['1','2','3','4','5','6','7','8','9','10']
        prioridad_options = ['Baja','Media','Alta']
        estado_options = ['Desarrollo','Revision','Aprobado']

        fields = [
                HiddenField('id_item', label_text='Id'),
                HiddenField('id_tipo_item', validator=NotEmpty, label_text='Tipo de Item'),
                Spacer(),
                TextArea('descripcion', validator=NotEmpty, attrs=dict(rows=3, cols=33), label_text='Descripcion',
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
	        FileField('archivo_externo', label_text='Archivo Externo',
                      help_text='Introduzca un archivo externo'),
                Spacer(),
	        HiddenField('version', validator=NotEmpty, label_text='Version',
                      help_text='Introduzca una version'),
                Spacer(),
	        TextArea('observacion', validator=PlainText, attrs=dict(rows=3, cols=33), label_text='Observacion',
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

              nombre = atributo_nuevo.nombre
              tipo = atributo_nuevo.tipo              
        
              if tipo=='Texto':
                 fields.append(TextField(nombre.replace(" ", "_"), label_text=nombre,
                              help_text='Introduzca'))
              elif tipo=='Numerico':
                 fields.append(TextField(nombre.replace(" ", "_"), label_text=nombre,
                              help_text='Introduzca'))
              else:
                 fields.append(CalendarDatePicker(nombre.replace(" ", "_"), label_text=nombre, date_format='%d/%m/%Y',
                              help_text='Seleccione la fecha de Creacion del Proyecto'))

   
        
        crear_item_form = ItemForm("CrearItem", action='add',fields=fields)
        tmpl_context.form = crear_item_form
        kw['id_tipo_item']= int(id_tipo_item)
        kw['version']= 1
        kw['estado']="Desarrollo"
        
        return dict(nombre_modelo='Item', id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, page='nuevo_item', value=kw)

    
    #@validate(crear_item_form)#form=globals().get('crear_form'),error_handler=nuevo)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un registro a la base de datos """
        guardarArchivo = True
        item = Item()
        item.id_tipo_item = kw['id_tipo_item']
        item.descripcion = kw['descripcion']
        item.complejidad = kw['complejidad']
        item.prioridad = kw['prioridad']
        item.estado = "Desarrollo"

        if kw['archivo_externo'] != "":
           item.archivo_externo = kw['archivo_externo'].filename
        else:
           guardarArchivo = False

        item.version = kw['version']
        item.observacion = kw['observacion']
        item.fecha_modificacion = kw['fecha_modificacion']
        item.vivo = True
        DBSession.add(item)
        DBSession.flush()

        id_item = item.id_item
        id_tipo_item = item.id_tipo_item

        atributos_nuevos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item)

        for atributo_nuevo in atributos_nuevos:
            nombre = atributo_nuevo.nombre
            #if kw[nombre.join("_")] != " ":
            itemDetalle = ItemDetalle()
            itemDetalle.id_item = id_item
            itemDetalle.nombre_atributo = nombre

            itemDetalle.valor = kw[nombre.replace(" ", "_")]

            DBSession.add(itemDetalle)
            DBSession.flush()

        if guardarArchivo == True:
           #write the picture file to the public directory
           item_path = os.path.join(items_dirname, str(item.id_item))
           try:
               os.makedirs(item_path)
           except OSError:
               #ignore if the folder already exists
               pass
        
           item_path = os.path.join(item_path, item.archivo_externo)
           f = file(item_path, "w")
           f.write(kw['archivo_externo'].value)
           f.close()

        flash("Item insertado")
        
        tipo_item = DBSession.query(TipoItem).filter_by(id_tipo_item=id_tipo_item).first()
        id_fase = tipo_item.id_fase
        fase = DBSession.query(Fase).filter_by(id_fase=id_fase).first()
        id_proyecto = fase.id_proyecto

        redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

    @expose('is2sap.templates.item.editar')
    def editar(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):
        """Metodo que rellena el formulario para editar los datos de un item"""

        complejidad_options = ['1','2','3','4','5','6','7','8','9','10']
        prioridad_options = ['Baja','Media','Alta']
        estado_options = ['Desarrollo','Revision','Aprobado']

        fields = [
                HiddenField('id_item', label_text='Id'),
                HiddenField('id_tipo_item', validator=NotEmpty, label_text='Tipo de Item'),
                Spacer(),
                TextArea('descripcion', validator=NotEmpty, attrs=dict(rows=3, cols=33), label_text='Descripcion',
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
	        FileField('archivo_externo', label_text='Archivo Externo',
                      help_text='Introduzca un archivo externo'),
                Spacer(),
	        HiddenField('version', validator=NotEmpty, label_text='Version',
                      help_text='Introduzca una version'),
                Spacer(),
	        TextArea('observacion', validator=PlainText, attrs=dict(rows=3, cols=33), label_text='Observacion',
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

              nombre = atributo_nuevo.nombre
              tipo = atributo_nuevo.tipo              
        
              if tipo=='Texto':
                 fields.append(TextField(nombre.replace(" ", "_"), label_text=nombre,
                              help_text='Introduzca'))
              elif tipo=='Numerico':
                 fields.append(TextField(nombre.replace(" ", "_"), label_text=nombre,
                              help_text='Introduzca'))
              else:
                 fields.append(CalendarDatePicker(nombre.replace(" ", "_"), label_text=nombre, date_format='%d/%m/%Y',
                              help_text='Seleccione la fecha de Creacion del Proyecto'))
        
        editar_item_form = ItemForm("EditarItem", action='update',fields=fields)
        tmpl_context.form = editar_item_form

        item=DBSession.query(Item).get(id_item)
        kw['id_item']=item.id_item
        kw['id_tipo_item']=item.id_tipo_item
        kw['descripcion']=item.descripcion
        kw['complejidad']=item.complejidad
        kw['prioridad']=item.prioridad
        kw['estado']="Desarrollo"
        kw['archivo_externo']=item.archivo_externo
        kw['version']=item.version
        kw['observacion']=item.observacion
        kw['fecha_modificacion']=item.fecha_modificacion
        kw['vivo']=item.vivo

        id_item = item.id_item
        detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item)

        for detalle in detalles:
            nombre = detalle.nombre_atributo
            valor = detalle.valor
            kw[nombre.replace(" ", "_")] = valor

	return dict(nombre_modelo='Item', id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, page='editar_item', value=kw)


#    @validate(editar_item_form, error_handler=editar)
    @expose()
    def update(self, **kw):        
        """Metodo que actualiza la base de datos"""

# FALTAN ALGUNOS PUNTOS:: Cuando el item esta aprobado, se modifica, cambia de version, se va al historial con el estado de Desarrollo, y el actual queda en #estado de Desarrollo y pone en revision todos los que estan afectado por el. Verificar que la Linea Base en la que se encuentra no este #aprobada. Si el item esta en una Linea Base en estado de Desarrollo o en Revision se tiene que desasignar automaticamente de la Linea Base. #Se tiene que tener en cuenta sus antecesores. 

# Al modificarse un item en una fase posterior, hay que poner en revision automaticamente la Linea Base en el que se encuentran los items afectados, dejando intacto los items que no estan afectados.

        item = DBSession.query(Item).get(kw['id_item'])   
        itemHistorial = ItemHistorial()
        itemHistorial.id_item = item.id_item
        itemHistorial.id_tipo_item = item.id_tipo_item
        itemHistorial.descripcion = item.descripcion
        itemHistorial.complejidad = item.complejidad
        itemHistorial.prioridad = item.prioridad
        itemHistorial.estado = "Desarrollo"
        itemHistorial.archivo_externo = item.archivo_externo
        itemHistorial.version = item.version
        itemHistorial.observacion = item.observacion
        itemHistorial.fecha_modificacion = item.fecha_modificacion
        DBSession.add(itemHistorial)
        
        item.id_tipo_item = kw['id_tipo_item']
        item.descripcion = kw['descripcion']
        item.complejidad = kw['complejidad']
        item.prioridad = kw['prioridad']
        item.estado = "Desarrollo"
        item.archivo_externo = kw['archivo_externo']
        item.version = int(kw['version']) + 1
        item.observacion = kw['observacion']
        item.fecha_modificacion = kw['fecha_modificacion']
        item.vivo = True

        id_item = item.id_item
        id_tipo_item = item.id_tipo_item

        detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item)
        atributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item).all()
        listaNom = []

        for atributo in atributos:
            listaNom.append(atributo.nombre)
            
        for detalle in detalles:
            nombre = detalle.nombre_atributo
            listaNom.remove(nombre)
            itemDetalleHistorial = ItemDetalleHistorial()
            itemDetalleHistorial.id_item = id_item
            itemDetalleHistorial.id_item_detalle = detalle.id_item_detalle
            itemDetalleHistorial.nombre_atributo = nombre
            itemDetalleHistorial.valor = detalle.valor
            itemDetalleHistorial.version = itemHistorial.version
            detalle.valor = kw[nombre.replace(" ", "_")]
            DBSession.add(itemDetalleHistorial)
            DBSession.flush()

        for atributo_nuevo in listaNom:
            nombre = atributo_nuevo
            #if kw[nombre.join("_")] != " ":
            itemDetalle = ItemDetalle()
            itemDetalle.id_item = id_item
            itemDetalle.nombre_atributo = nombre
            itemDetalle.valor = kw[nombre.replace(" ", "_")]
            DBSession.add(itemDetalle)
            DBSession.flush()
            
        flash("Item editado")
            
        tipo_item = DBSession.query(TipoItem).filter_by(id_tipo_item=id_tipo_item).first()
        id_fase = tipo_item.id_fase
        fase = DBSession.query(Fase).filter_by(id_fase=id_fase).first()
        id_proyecto = fase.id_proyecto

        redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

    @expose("is2sap.templates.item.listado")
    def listado(self, id_proyecto, id_fase, id_tipo_item, page=1):
        """Metodo para listar todos los items de la base de datos"""
        items = DBSession.query(Item).filter_by(id_tipo_item=id_tipo_item).filter_by(vivo=True).order_by(Item.id_item)
        currentPage = paginate.Page(items, page)#, items_per_page=1)
        return dict(items=currentPage.items, page='listado_item', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, currentPage=currentPage)

    @expose("is2sap.templates.item.listado_detalles")
    def listado_detalles(self, id_proyecto, id_fase, id_tipo_item, id_item, page=1):
        """Metodo para listar todos los items de la base de datos"""
        detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item).order_by(ItemDetalle.id_item_detalle)
        currentPage = paginate.Page(detalles, page)#, items_per_page=1)
        return dict(detalles=detalles, page='listado_detalles', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, currentPage=currentPage)

    @expose("is2sap.templates.item.listado_revivir")
    def listado_revivir(self, id_proyecto, id_fase, id_tipo_item, page=1):
        """Metodo para listar los items del tipo correspondiente que pueden ser revividos"""
        items = DBSession.query(Item).filter_by(id_tipo_item=id_tipo_item).filter_by(vivo=False).order_by(Item.id_item)
        currentPage = paginate.Page(items, page)#, items_per_page=1)
        return dict(items=currentPage.items, page='listado_revivir', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, currentPage=currentPage)

    @expose()
    def revivir_item(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):        
        """Metodo que revive un item que habia sido eliminado"""
        item = DBSession.query(Item).get(id_item)
        item.vivo = True
        item.estado = "Desarrollo"
        DBSession.flush()
        flash("Item revivido")           
        redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

    @expose("is2sap.templates.item.listado_detalles_revivir")
    def listado_detalles_revivir(self, id_proyecto, id_fase, id_tipo_item, id_item, page=1):
        """Metodo para listar todos los items de la base de datos"""
        item_detalle = DBSession.query(ItemDetalle).filter_by(id_item=id_item)
        currentPage = paginate.Page(item_detalle, page)#, items_per_page=1)
        return dict(item_detalle=item_detalle, page='listado_detalles_revivir', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item, currentPage=currentPage)

    @expose()
    def aprobar(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):        
        """Metodo que cambia el estado de un item al de Aprobado"""
        item = DBSession.query(Item).get(id_item)
        item.estado = "Aprobado"
        DBSession.flush()
        flash("Item aprobado")           
        redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

    @expose("is2sap.templates.item.listado_revertir")
    def listado_revertir(self, id_proyecto, id_fase, id_tipo_item, id_item, page=1):
        """Metodo para listar todos los items de la base de datos"""
        item_historial = DBSession.query(ItemHistorial).filter_by(id_item=id_item).order_by(ItemHistorial.version)
        #detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item)
        currentPage = paginate.Page(item_historial, page)#, items_per_page=1)
        return dict(item_historial=item_historial, page='listado_revertir', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item, currentPage=currentPage)

    @expose("is2sap.templates.item.listado_detalles_revertir")
    def listado_detalles_revertir(self, id_proyecto, id_fase, id_tipo_item, id_item, version, page=1):
        """Metodo para listar todos los items de la base de datos"""
        item_detalle_historial = DBSession.query(ItemDetalleHistorial).filter_by(id_item=id_item).filter_by(version=version)
        currentPage = paginate.Page(item_detalle_historial, page)#, items_per_page=1)
        return dict(item_detalle_historial=item_detalle_historial, page='listado_detalles_revertir', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, id_item=id_item, currentPage=currentPage)

    @expose()
    def revertir_item(self, id_proyecto, id_fase, id_tipo_item, id_historial_item, **kw):        
        """Metodo que actualiza la base de datos"""

#FALTAN ALGUNOS PUNTOS:: Para revertir vuelve en estado de Desarrollo y pone en revision a todos los que dependen de el, le asigna una nueva version y trata de recuperar todas las relaciones que se pueda.

        item_a_revertir = DBSession.query(ItemHistorial).get(id_historial_item)
        version_a_revertir = item_a_revertir.version
        id_item = item_a_revertir.id_item
        item_actual = DBSession.query(Item).get(id_item)
        version_actual = item_actual.version    

        item_hist_nuevo = ItemHistorial()
        item_hist_nuevo.id_item = item_actual.id_item
        item_hist_nuevo.id_tipo_item = item_actual.id_tipo_item
        item_hist_nuevo.descripcion = item_actual.descripcion
        item_hist_nuevo.complejidad = item_actual.complejidad
        item_hist_nuevo.prioridad = item_actual.prioridad
        item_hist_nuevo.estado = item_actual.estado
        item_hist_nuevo.archivo_externo = item_actual.archivo_externo
        item_hist_nuevo.version = item_actual.version
        item_hist_nuevo.observacion = item_actual.observacion
        item_hist_nuevo.fecha_modificacion = item_actual.fecha_modificacion
        DBSession.add(item_hist_nuevo)
        
        item_actual.id_tipo_item = item_a_revertir.id_tipo_item
        item_actual.descripcion = item_a_revertir.descripcion
        item_actual.complejidad = item_a_revertir.complejidad
        item_actual.prioridad = item_a_revertir.prioridad
        item_actual.estado = "Desarrollo"
        item_actual.archivo_externo = item_a_revertir.archivo_externo
        item_actual.version = int(item_actual.version) + 1
        item_actual.observacion = item_a_revertir.observacion
        item_actual.fecha_modificacion = item_a_revertir.fecha_modificacion
        item_actual.vivo = True

        #detalles_a_revertir = DBSession.query(ItemDetalleHistorial).filter_by(id_item=id_item).filter_by(version=version_a_revertir)
        detalles_actuales = DBSession.query(ItemDetalle).filter_by(id_item=id_item)
        atributos = DBSession.query(Atributo).filter_by(id_tipo_item=id_tipo_item).all()
        listaNom = []

        for atributo in atributos:
            listaNom.append(atributo.nombre)

        for detalle in detalles_actuales:
            nombre = detalle.nombre_atributo
            listaNom.remove(nombre)
            id_item_detalle = detalle.id_item_detalle
            item_detalle_historial = ItemDetalleHistorial()
            item_detalle_historial.id_item = id_item
            item_detalle_historial.id_item_detalle = detalle.id_item_detalle
            item_detalle_historial.nombre_atributo = nombre
            item_detalle_historial.valor = detalle.valor
            item_detalle_historial.version = version_actual

            detalle_a_revertir = DBSession.query(ItemDetalleHistorial).filter_by(id_item_detalle=id_item_detalle).filter_by(version=version_a_revertir).first()
            if detalle_a_revertir!=None:
                detalle.valor = detalle_a_revertir.valor
            else:
                detalle.valor = ""
            DBSession.add(item_detalle_historial)
            DBSession.flush()

        for atributo_nuevo in listaNom:
            nombre = atributo_nuevo
            #if kw[nombre.join("_")] != " ":
            itemDetalle = ItemDetalle()
            itemDetalle.id_item = id_item
            itemDetalle.nombre_atributo = nombre

            itemDetalle.valor = ""


            DBSession.add(itemDetalle)
            DBSession.flush()
        flash("Item revertido")
           
        redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

    @expose('is2sap.templates.item.confirmar_eliminar')
    def confirmar_eliminar(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):
        """Despliega confirmacion de eliminacion"""
        item=DBSession.query(Item).get(id_item)
        tipo_item=DBSession.query(TipoItem).get(item.id_tipo_item)
        return dict(nombre_modelo='Item', page='confirmar_eliminar', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, nombre_tipo_item=tipo_item.nombre, item=item)

    @expose()
    def delete(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):
        """Metodo que elimina un registro de la base de datos"""

#FALTAN ALGUNOS PUNTOS::Al eliminar el item se tiene que eliminar todas las relaciones que tiene y poner en revision todos los que afectados por el.

        item = DBSession.query(Item).get(id_item)
        item.vivo = False

        #Ejemplo de como eliminar los detalles de un Item
        #detalles_del_item = item.item_detalles
        #tabla_item_detalle = DBSession.query(ItemDetalle).all()
        #for detalle in detalles_del_item:
            #DBSession.delete(DBSession.query(ItemDetalle).get(detalle.id_item_detalle))
        #DBSession.delete(DBSession.query(Item).get(id_item))

        redirect("/item/listado",id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

    @expose("is2sap.templates.item.listado_proyectos")
    def proyectos(self,page=1):
        """Metodo para listar todos los Proyectos existentes de la base de datos"""
        usuario = DBSession.query(Usuario).filter_by(nombre_usuario=request.identity['repoze.who.userid']).first()
        todosProyectos = usuario.proyectos

        proyectos = []

        for proyecto in todosProyectos:
            if proyecto.iniciado == True:
               proyectos.append(proyecto)

        currentPage = paginate.Page(proyectos, page, items_per_page=5)
        return dict(proyectos=currentPage.items,
           page='listado_proyectos', currentPage=currentPage)

    @expose("is2sap.templates.item.listado_fases")
    def fases(self,id_proyecto, page=1):
        """Metodo para listar las Fases de un proyecto """

#FALTAN ALGUNOS PUNTOS: Para poder listar las fases a cargar items, se tiene como criterio que la fase no este en estado Inicial y las anteriores esten con Lineas Bases Parciales o Con Lineas Bases.

        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        fases = proyecto.fases

#Activar este for luego de que se haya hecho todo el metodo Iniciar Proyecto
        #fasesTodas = proyecto.fases
        #fases = []

        #for fase in fasesTodas:
        #    if fase.relacion_estado_fase.nombre_estado != "Inicial":
        #       fases.append(fase)

        currentPage = paginate.Page(fases, page, items_per_page=5)
        return dict(fases=currentPage.items, page='listado_fases', 
           nombre_proyecto=proyecto.nombre, id_proyecto=proyecto.id_proyecto, currentPage=currentPage)

    @expose("is2sap.templates.item.listado_tipo_items")
    def tipoItems(self, id_proyecto, id_fase, page=1):
        """Metodo para listar los Tipos de Items de una Fase """
        fase = DBSession.query(Fase).get(id_fase)
        tipoItems = fase.tipoitems
        currentPage = paginate.Page(tipoItems, page, items_per_page=5)
        return dict(tipoItems=currentPage.items,
           page='listado_tipo_items', nombre_fase=fase.nombre, id_proyecto=id_proyecto, id_fase=id_fase, currentPage=currentPage)

        
    @expose("is2sap.templates.item.listadoItemsPorLineaBase")
    def listadoItemsPorLineaBase(self, id_proyecto, id_fase, id_linea_base, page=1):
        """Metodo para listar todos los items de la base de datos que pertenecen a la linea base"""
        linea_base=DBSession.query(LineaBase).get(id_linea_base)
	items = linea_base.items
        currentPage = paginate.Page(items, page)#, items_per_page=1)
        return dict(items=currentPage.items, page='listadoItemsPorLineaBase', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, currentPage=currentPage)

	
    @expose("is2sap.templates.item.listadoItemsParaAsignaraLineaBase")
    def listadoItemsParaAsignaraLineaBase(self, id_proyecto, id_fase, id_linea_base, page=1):
        """Metodo para listar todos los items a asignar a la linea base"""
        linea_base=DBSession.query(LineaBase).get(id_linea_base)
	itemsLineaBase = linea_base.items
	items = DBSession.query(Item).all()
	for item in itemsLineaBase:
           items.remove(item)
        currentPage = paginate.Page(items, page)#, items_per_page=1)
        return dict(items=currentPage.items, page='listadoItemsParaAsignaraLineaBase', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, currentPage=currentPage)

    
    @expose()
    def asignarItem(self, id_proyecto, id_fase, id_linea_base, id_item):
        """Metodo que realiza la asignacion de un item a la linea base selecccionada"""
        item = DBSession.query(Item).get(id_item)
        linea_base = DBSession.query(LineaBase).get(id_linea_base)
        item.linea_bases.append(linea_base)

        redirect("/item/listadoItemsParaAsignaraLineaBase",id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base)


    @expose()
    def desasignar_item_linea_base(self, id_proyecto, id_fase, id_linea_base, id_item, **kw):
        """Metodo que desasigna un item de la linea base seleccionada"""
        item = DBSession.query(Item).get(id_item)
        linea_base = DBSession.query(LineaBase).get(id_linea_base)
        item.linea_bases.remove(linea_base)

        redirect("/item/listadoItemsPorLineaBase", id_proyecto=id_proyecto, id_fase=id_fase, id_linea_base=id_linea_base)


    @expose("is2sap.templates.item.listado_detalles_items_linea_base")
    def listado_detalles_items_linea_base(self, id_proyecto, id_fase, id_linea_base, id_item, page=1):
        """Metodo para listar todos los detalles de los items que pertenecen a la linea base"""
        detalles = DBSession.query(ItemDetalle).filter_by(id_item=id_item).order_by(ItemDetalle.id_item_detalle)
        currentPage = paginate.Page(detalles, page)#, items_per_page=1)
        return dict(detalles=currentPage.items, page='listado_detalles_items_linea_base', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, id_item=id_item, currentPage=currentPage)


    @expose("is2sap.templates.item.listadoItemsPorLineaBaseHistorial")
    def listadoItemsPorLineaBaseHistorial(self, id_proyecto, id_fase, id_linea_base, version, page=1):
        """Metodo para listar todos los items de la base de datos que pertenecen al historial de la linea base"""
	#No se como hacer aqui para el tema de la version
        linea_base=DBSession.query(LineaBase).get(id_linea_base)
	items = linea_base.itemshistorial
        currentPage = paginate.Page(items, page)#, items_per_page=1)
        return dict(items=currentPage.items, page='listadoItemsPorLineaBaseHistorial', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_linea_base=id_linea_base, currentPage=currentPage)

