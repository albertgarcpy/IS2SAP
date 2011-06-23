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
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import transaction

public_dirname = os.path.join(os.path.abspath(resource_filename('is2sap', 'public')))
items_dirname = os.path.join(public_dirname, 'items')

from is2sap.widgets.mi_validador.mi_validador import *
from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import TipoItem, Item, Proyecto, Usuario, Fase, Atributo, ItemDetalle, ItemHistorial, ItemDetalleHistorial, LineaBase, LineaBase_Item, LineaBaseHistorial, RelacionItem
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController
from is2sap.widgets.item_form import ItemForm, EditItemForm
import pydot

itemsAfectados=[]
listaRelaciones = []

__all__ = ['ItemController']


class ItemController(BaseController):

    allow_only = has_permission('edicion',
                                msg=l_('Solo para usuarios con permiso "edicion"'))
    
    @expose('is2sap.templates.item.index')
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='Item', page='index_item')


#--------------------------- Creacion de Items ---------------------------------
    @expose('is2sap.templates.item.nuevo')
    def nuevo(self, id_proyecto, id_fase, id_tipo_item, **kw):
        """Despliega el formulario para añadir un nuevo Item."""
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
	        FileField('archivo_externo', label_text='Archivo Externo',
                      help_text='Introduzca un archivo externo'),
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

            crear_item_form = ItemForm("CrearItem", action='add',fields=fields)
            tmpl_context.form = crear_item_form
            kw['id_tipo_item']= int(id_tipo_item)
            items = DBSession.query(Item).filter_by(id_tipo_item=id_tipo_item)
            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
            cont = 0

            for item in items:
                cont = cont + 1
            
            kw['codigo'] = str(tipo_item.codigo) + "-" + str(cont + 1)
            kw['version']= 1
            kw['estado']="Desarrollo"
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Creacion de Items! SQLAlchemyError..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Creacion de Items! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        
        return dict(nombre_modelo='Item', id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, page='nuevo_item', value=kw)

    
    #@validate(crear_item_form)#form=globals().get('crear_form'),error_handler=nuevo)
    @expose()
    def add(self, **kw):
        """Metodo para agregar un nuevo item a la base de datos """
        #Al crear un nuevo item, verificar si es que la fase esta en estado Con Lineas Bases, en este caso cambiar al estado
        #Con Lineas Bases Parciales
        try:
            guardarArchivo = True
            item = Item()
            item.id_tipo_item = kw['id_tipo_item']
            item.codigo = kw['codigo']
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
                itemDetalle = ItemDetalle()
                itemDetalle.id_item = id_item
                itemDetalle.id_atributo = atributo_nuevo.id_atributo
                itemDetalle.nombre_atributo = atributo_nuevo.nombre
                itemDetalle.valor = kw[str(atributo_nuevo.id_atributo)]
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
        
            tipo_item = DBSession.query(TipoItem).filter_by(id_tipo_item=id_tipo_item).first()
            id_fase = tipo_item.id_fase
            fase = DBSession.query(Fase).filter_by(id_fase=id_fase).first()
            id_proyecto = fase.id_proyecto
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
            flash(_("No se ha guardado! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        else:
            flash(_("Item creado!"), 'ok')

        redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)


#--------------------------- Edicion de Items ----------------------------------
    @expose('is2sap.templates.item.editar')
    def editar(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):
        """Metodo que rellena el formulario para editar los datos de un item"""
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
	        FileField('archivo_externo', label_text='Archivo Externo',
                      help_text='Introduzca un archivo externo'),
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
            item = DBSession.query(Item).get(id_item)
            kw['id_item'] = item.id_item
            kw['id_tipo_item'] = item.id_tipo_item
            kw['codigo'] = item.codigo
            kw['descripcion'] = item.descripcion
            kw['complejidad'] = item.complejidad
            kw['prioridad'] = item.prioridad
            kw['estado'] = "Desarrollo"
            kw['archivo_externo'] = item.archivo_externo
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
    def update(self, **kw):        
        """Metodo que actualiza los datos de un item"""
        try:
# FALTAN ALGUNOS PUNTOS:: Cuando el item esta aprobado, se modifica, cambia de version, se va al historial con el estado de Desarrollo, y el actual queda en #estado de Desarrollo y pone en revision todos los que estan afectado por el. Verificar que la Linea Base en la que se encuentra no este #aprobada. Si el item esta en una Linea Base en estado de Desarrollo o en Revision se tiene que desasignar automaticamente de la Linea Base. #Se tiene que tener en cuenta sus antecesores. 

# Al modificarse un item en una fase posterior, hay que poner en revision automaticamente la Linea Base en el que se encuentran los items afectados, dejando intacto los items que no estan afectados.

            #Llevamos al historial el item a ser editado
            item = DBSession.query(Item).get(kw['id_item'])   
            itemHistorial = ItemHistorial()
            itemHistorial.id_item = item.id_item
            itemHistorial.id_tipo_item = item.id_tipo_item
            itemHistorial.codigo = item.codigo
            itemHistorial.descripcion = item.descripcion
            itemHistorial.complejidad = item.complejidad
            itemHistorial.prioridad = item.prioridad
            itemHistorial.estado = "Desarrollo"
            itemHistorial.archivo_externo = item.archivo_externo
            itemHistorial.version = item.version
            itemHistorial.observacion = item.observacion
            itemHistorial.fecha_modificacion = item.fecha_modificacion
            DBSession.add(itemHistorial)
            DBSession.flush()

            #Cargamos el item con los valores nuevos
            item.id_tipo_item = kw['id_tipo_item']
            item.codigo = kw['codigo']
            item.descripcion = kw['descripcion']
            item.complejidad = kw['complejidad']
            item.prioridad = kw['prioridad']
            item.estado = "Desarrollo"
            item.archivo_externo = kw['archivo_externo']
            item.version = int(kw['version']) + 1
            item.observacion = kw['observacion']
            item.fecha_modificacion = kw['fecha_modificacion']
            item.vivo = True
            DBSession.flush()

            #Consultamos los detalles actuales del item
            #Se debe agregar en ItemDetalle el id_atributo al que pertenece
            #Luego buscar por listaIdAtributo en vez de listaNom
            id_item = item.id_item
            id_tipo_item = item.id_tipo_item
            tipo_item = DBSession.query(TipoItem).get(id_tipo_item)
            id_fase = tipo_item.id_fase
            fase = DBSession.query(Fase).get(id_fase)
            id_proyecto = fase.id_proyecto

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
    def confirmar_eliminar(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):
        """Despliega confirmacion de eliminacion"""
        try:
            item = DBSession.query(Item).get(id_item)
            tipo_item = DBSession.query(TipoItem).get(item.id_tipo_item)
        except SQLAlchemyError:
            flash(_("No se pudo acceder a Eliminacion de Item! SQLAlchemyError..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
        except (AttributeError, NameError):
            flash(_("No se pudo acceder a Eliminacion de Item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado", id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

        return dict(nombre_modelo='Item', page='confirmar_eliminar', id_proyecto=id_proyecto, 
                    id_fase=id_fase, id_tipo_item=id_tipo_item, nombre_tipo_item=tipo_item.nombre, item=item)

    @expose()
    def delete(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):
        """Metodo que elimina un registro de la base de datos"""
        try:
#FALTAN ALGUNOS PUNTOS::Al eliminar el item se tiene que eliminar todas las relaciones que tiene y poner en revision todos los que afectados por el. Tambien se debe verificar que no se encuentre en una LB aprobada, en cuyo caso no se puede eliminar. Si puede ser eliminado, se debe desasignar de la LB a la que pertenecia.
#Al eliminar un item, verificar si es que la fase esta en estado Con Lineas Bases Parciales y si el item a eliminar es el unico que no esta en alguna Linea BAse, en este caso cambia la fase al estado Con Lineas Bases
            item = DBSession.query(Item).get(id_item)
            item.vivo = False
            DBSession.flush()
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
    def aprobar(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):        
        """Metodo que cambia el estado de un item al de Aprobado"""
        try:
            item = DBSession.query(Item).get(id_item)

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
    def aprobar_desde_fase(self, id_proyecto, id_fase, id_tipo_item, id_item, **kw):        
        """Metodo que cambia el estado de un item al de Aprobado"""
        try:
            item = DBSession.query(Item).get(id_item)

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
    def revertir_item(self, id_proyecto, id_fase, id_tipo_item, id_historial_item, **kw):        
        """Metodo que actualiza la base de datos"""
        try:
#FALTAN ALGUNOS PUNTOS:: Para revertir vuelve en estado de Desarrollo y pone en revision a todos los que dependen de el, le asigna una nueva version y trata de recuperar todas las relaciones que se pueda.

            #Consultamos el item que se encuentra en el historial
            item_a_revertir = DBSession.query(ItemHistorial).get(id_historial_item)
            version_a_revertir = item_a_revertir.version
            id_item = item_a_revertir.id_item
            item_actual = DBSession.query(Item).get(id_item)
            version_actual = item_actual.version    

            #Cargamos en el historial el item que esta con los datos actuales
            item_hist_nuevo = ItemHistorial()
            item_hist_nuevo.id_item = item_actual.id_item
            item_hist_nuevo.id_tipo_item = item_actual.id_tipo_item
            item_hist_nuevo.codigo = item_actual.codigo
            item_hist_nuevo.descripcion = item_actual.descripcion
            item_hist_nuevo.complejidad = item_actual.complejidad
            item_hist_nuevo.prioridad = item_actual.prioridad
            item_hist_nuevo.estado = item_actual.estado
            item_hist_nuevo.archivo_externo = item_actual.archivo_externo
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
            item_actual.archivo_externo = item_a_revertir.archivo_externo
            item_actual.version = int(item_actual.version) + 1
            item_actual.observacion = item_a_revertir.observacion
            item_actual.fecha_modificacion = item_a_revertir.fecha_modificacion
            item_actual.vivo = True

            #Consultamos los detalles actuales del item
            #Se debe agregar en ItemDetalle el id_atributo al que pertenece
            #Luego buscar por listaIdAtributo en vez de listaNom
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
            flash(_("No se pudo revertir el Item! Hay Problemas con el servidor..."), 'error')
            redirect("/item/listado_revertir", id_proyecto=id_proyecto, id_fase=id_fase, 
                     id_tipo_item=id_tipo_item, id_item=id_item)
        else:
            flash(_("Item revertido!"), 'ok')
           
        redirect("/item/listado_revertir", id_proyecto=id_proyecto, id_fase=id_fase, 
                 id_tipo_item=id_tipo_item, id_item=id_item)

    @expose("is2sap.templates.item.revertir_desde_fase")
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
    def revertir_item_desde_fase(self, id_proyecto, id_fase, id_tipo_item, id_historial_item, **kw):        
        """Metodo que actualiza la base de datos"""
        try:
#FALTAN ALGUNOS PUNTOS:: Para revertir vuelve en estado de Desarrollo y pone en revision a todos los que dependen de el, le asigna una nueva version y trata de recuperar todas las relaciones que se pueda.

            #Consultamos el item que se encuentra en el historial
            item_a_revertir = DBSession.query(ItemHistorial).get(id_historial_item)
            version_a_revertir = item_a_revertir.version
            id_item = item_a_revertir.id_item
            item_actual = DBSession.query(Item).get(id_item)
            version_actual = item_actual.version    

            #Cargamos en el historial el item que esta con los datos actuales
            item_hist_nuevo = ItemHistorial()
            item_hist_nuevo.id_item = item_actual.id_item
            item_hist_nuevo.id_tipo_item = item_actual.id_tipo_item
            item_hist_nuevo.codigo = item_actual.codigo
            item_hist_nuevo.descripcion = item_actual.descripcion
            item_hist_nuevo.complejidad = item_actual.complejidad
            item_hist_nuevo.prioridad = item_actual.prioridad
            item_hist_nuevo.estado = item_actual.estado
            item_hist_nuevo.archivo_externo = item_actual.archivo_externo
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
            item_actual.archivo_externo = item_a_revertir.archivo_externo
            item_actual.version = int(item_actual.version) + 1
            item_actual.observacion = item_a_revertir.observacion
            item_actual.fecha_modificacion = item_a_revertir.fecha_modificacion
            item_actual.vivo = True

            #Consultamos los detalles actuales del item
            #Se debe agregar en ItemDetalle el id_atributo al que pertenece
            #Luego buscar por listaIdAtributo en vez de listaNom
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
    def proyectos(self,page=1):
        """Metodo para listar todos los Proyectos existentes de la base de datos"""
        try:
            usuario = DBSession.query(Usuario).filter_by(nombre_usuario=request.identity['repoze.who.userid']).first()
            todosProyectos = usuario.proyectos

            proyectos = []

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


#--------------------------- Listado de Fases por Proyecto----------------------
    @expose("is2sap.templates.item.listado_fases")
    def fases(self,id_proyecto, page=1):
        """Metodo para listar las Fases de un proyecto """
        try:

#FALTAN ALGUNOS PUNTOS: Para poder listar las fases a cargar items, se tiene como criterio que la fase no este en estado Inicial y las anteriores esten con Lineas Bases Parciales o Con Lineas Bases.

            fases= DBSession.query(Fase).join(Fase.relacion_estado_fase).filter(Fase.id_proyecto==id_proyecto).options(contains_eager(Fase.relacion_estado_fase)).order_by(Fase.numero_fase)
            nombreProyecto = DBSession.query(Proyecto.nombre).filter_by(id_proyecto=id_proyecto).first()


#Activar este for luego de que se haya hecho todo el metodo Iniciar Proyecto
        #fasesTodas = proyecto.fases
        #fases = []

        #for fase in fasesTodas:
        #    if fase.relacion_estado_fase.nombre_estado != "Inicial":
        #       fases.append(fase)

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

    @expose("is2sap.templates.item.GraficoImpacto")
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

        graph = pydot.Dot(graph_type='digraph')
        for fase in fases:
            itemsDeFase = DBSession.query(Item).join(TipoItem).join(Fase).filter(Fase.id_fase==fase.id_fase).all()
            impactoPorFase=0
            for item in itemsDeFase:
                if itemsAfectados.count(item.id_item) == 1:
                    impactoPorFase = impactoPorFase + int(item.complejidad)
            impactoTotal = impactoTotal + impactoPorFase
            print "El impacto de la "+fase.nombre+" es :", impactoPorFase
        print "El impacto total es :", impactoTotal   
        
        for i in itemsAfectados:
            graph.add_node(pydot.Node(str(i)))
        for x in listaRelaciones:
            graph.add_edge(pydot.Edge(str(x[0]), str(x[1])))
        graph.write_png('../IS2SAP/is2sap/public/images/example2_graph.png')
        return dict(nombre_modelo="CalculoImpacto")
