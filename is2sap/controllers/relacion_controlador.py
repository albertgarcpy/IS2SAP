# -*- coding: utf-8 -*-
"""Controlador de Relacion"""

from tg import expose, flash, require, redirect
from repoze.what import predicates
from tg import validate
from webhelpers import paginate

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import RelacionItem, Fase, TipoItem, Item, Proyecto, LineaBase
from is2sap import model
from is2sap.controllers.grafo.grafo import Graph
import transaction
import time
import os

newGrafo = Graph()
inserciones=0
itemsAfectados=[]
listaRelaciones = []

__all__ = ['RelacionController']


class RelacionController(BaseController):
    
    
    @expose()
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='RelacionItem', page='index_relacion')        


    @expose('is2sap.templates.relacion.nuevo')
    def nuevo(self, idItemActual, id_proyecto, id_fase, id_tipo_item):
        """Establece una relacion para el item."""
        global inserciones
        inserciones = 0
        print "el numero de inserciones es :", inserciones
        faseActual=DBSession.query(Fase).join(TipoItem).join(Item).filter(Item.id_item==idItemActual).one()
        itemsDeFase = DBSession.query(Item).join(TipoItem).join(Fase).filter(Fase.id_fase==faseActual.id_fase).filter(Item.id_item!=idItemActual).all()
        hijos = DBSession.query(RelacionItem).filter_by(id_item1=idItemActual).filter_by(tipo="Padre-Hijo").order_by(RelacionItem.id_item2).all()
        print "Estoy en la fase:",faseActual.id_fase
        for hijo in hijos:        
            for item1 in itemsDeFase:            
                if item1.id_item == hijo.id_item2:
                   if itemsDeFase.count(item1) >= 1: 
                      itemsDeFase.remove(item1)

        
        # Comment: Esto trae los items de la fase adyacente anterior para las relaciones del itemActual        
        proyecto=DBSession.query(Proyecto).join(Fase).join(TipoItem).join(Item).filter(Item.id_item==idItemActual).one()
        faseDeProyecto=DBSession.query(Fase).join(Proyecto).filter(Proyecto.id_proyecto==proyecto.id_proyecto).order_by(Fase.id_fase)
        for fa in faseDeProyecto:
            print "FASE:", fa.id_fase
        posicion=0        
        itemsDeFaseAdyacente=[]
        for fase in faseDeProyecto:
            if fase.numero_fase==faseActual.numero_fase-1:
                print "El numero de fase anterior es :", fase.numero_fase
                itemsDeFaseAdyacente = DBSession.query(Item).join(TipoItem).join(Fase).filter(Fase.id_fase==fase.id_fase).filter(Item.estado=="Aprobado").all()
        if faseActual.numero_fase == 1:
            itemsDeFaseAdyacente = DBSession.query(Item).join(TipoItem).join(Fase).filter(Item.complejidad=="100").all()
        antecesores = DBSession.query(RelacionItem).filter_by(id_item2=idItemActual).filter_by(tipo="Antecesor-Sucesor").order_by(RelacionItem.id_item1).all()       
        for antec in antecesores:        
            for item2 in itemsDeFaseAdyacente:            
                if item2.id_item == antec.id_item1:
                   if itemsDeFaseAdyacente.count(item2) >= 1: 
                      itemsDeFaseAdyacente.remove(item2)
        return dict(nombre_modelo='Relacion', page='relacion', idItemActual=idItemActual, itemsDeFase=itemsDeFase, itemsDeFaseAdyacente=itemsDeFaseAdyacente, id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)


    @expose("is2sap.templates.relacion.listado")
    def listado(self, id_item, id_proyecto, id_fase, id_tipo_item):
        """Metodo para listar todos los usuarios de la base de datos"""
        antecesores = DBSession.query(RelacionItem).filter_by(id_item2=id_item).filter_by(tipo="Antecesor-Sucesor").order_by(RelacionItem.id_item1)
        listaAntecesores = []
        for antecesor in antecesores:
            item = DBSession.query(Item).get(antecesor.id_item1)
            ant = [antecesor, item]
            listaAntecesores.append(ant)
        hijos = DBSession.query(RelacionItem).filter_by(id_item1=id_item).filter_by(tipo="Padre-Hijo").order_by(RelacionItem.id_item2)
        listaHijos = []
        for hijo in hijos:
            item1 = DBSession.query(Item).get(hijo.id_item2)
            hij = [hijo, item1]
            listaHijos.append(hij)
        fase = DBSession.query(Fase).get(id_fase)
        permisosFase=[]
        for rol in fase.roles:
            for permiso in rol.permisos:                     
                permisosFase.append(permiso.nombre_permiso)
        return dict(antecesores=listaAntecesores, hijos=listaHijos, idItemActual=id_item, id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item, permisosFase=permisosFase)

    
    def buscarCiclos(self, item):    
        padres = DBSession.query(RelacionItem).filter_by(id_item2=item).filter_by(tipo="Padre-Hijo").order_by(RelacionItem.id_item1)
        for padre in padres:
            print ":::: ", padre.id_item1, padre.id_item2
            newGrafo.add_edge(padre.id_item1, padre.id_item2, False)            
            self.buscarCiclos(padre.id_item1)

    def insertarHijo(self, kw): 
        newGrafo.__init__()
        global inserciones
        inserciones = inserciones + 1
        print "el numero de inserciones es :", inserciones
        if inserciones == 1:                        
            self.buscarCiclos(kw['id_item1'])
            id_item1 = int(kw['id_item1'])
            id_item2 = int(kw['id_item2'])
            newGrafo.add_edge(id_item1, id_item2, False)
            hayciclo = newGrafo.walk(id_item1)
            print newGrafo
            print hayciclo
            if hayciclo:
                flash(_("No se puede insertar la relacion. Produce ciclos!"), 'warning')
                return
            else: 
                item = DBSession.query(Item).get(kw['id_item1'])
                id_item = item.id_item
                version_anterior = item.version
                version_nueva = int(item.version) + 1
                linea_bases_item = item.linea_bases

                #Comprobamos que no se encuentre en una Linea Base
                if linea_bases_item != []:
                   for linea_base_item in linea_bases_item:
                       flash(_("No se puede agregar la relacion! El Item se encuentra en una Linea Base..."), 'error')
                       return

                #El Item padre cambia de version al tener una nueva relacion
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

                #Enviamos al historial los detalles del Item a ser editado
                if detalles != None:
                   for detalle in detalles:
                       if lista_id_atributo.count(detalle.id_atributo) >= 1: 
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

                #Insertamos la nueva relacion
                relacion = RelacionItem()
                relacion.tipo = "Padre-Hijo"
                relacion.id_item1 = kw['id_item1']
                relacion.id_item2 = kw['id_item2']      
                DBSession.add(relacion)
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

                #Los archivos adjuntos del Item a ser editado se copian
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

                transaction.commit()   
                flash(_("Relacion insertada!"), 'ok')

    @expose()
    def addHijo(self, **kw):
        self.insertarHijo(kw)
	DBSession.flush() 
        redirect('listado', id_item=kw['id_item1'], id_proyecto=kw['id_proyecto'], id_fase=kw['id_fase'], id_tipo_item=kw['id_tipo_item'])
        
    def insertarAncestro(self, kw): 
        global inserciones
        inserciones = inserciones + 1
        print "el numero de inserciones es :", inserciones
        if inserciones == 1:
           item = DBSession.query(Item).get(kw['id_item1'])
           id_item = item.id_item
           version_anterior = item.version
           version_nueva = int(item.version) + 1
           linea_bases_item = item.linea_bases

           #Comprobamos que no se encuentre en una Linea Base
           if linea_bases_item != []:
              for linea_base_item in linea_bases_item:
                  flash(_("No se puede agregar la relacion! El Item se encuentra en una Linea Base..."), 'error')
                  return

           #El Item cambia de version al agregar la relacion
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

           #Enviamos al historial los detalles del Item a ser editado
           if detalles != None:
              for detalle in detalles:
                  if lista_id_atributo.count(detalle.id_atributo) >= 1: 
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

           #Insertamos la nueva relacion
           relacion = RelacionItem()
           relacion.tipo = "Antecesor-Sucesor"
           relacion.id_item1 = kw['id_item1']
           relacion.id_item2 = kw['id_item2']      
           DBSession.add(relacion)
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

           #Los archivos adjuntos del Item a ser editado se copian
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

           transaction.commit()   
           flash(_("Relacion insertada!"), 'ok')

	   #Aqui comprobamos si todos los items de la fase actual  tienen sucesores, en ese caso
	   #el estado de la fase cambiamos a Finalizado
	   id_tipo_item=kw['id_tipo_item']
	   id_fase=kw['id_fase']
	   fase_actual=DBSession.query(Fase).get(id_fase)
	   #Obtenemos la fase anterior
	   fase_anterior=DBSession.query(Fase).filter_by(numero_fase=fase_actual.numero_fase-1).filter_by(id_proyecto=fase_actual.id_proyecto).first()
	   fase=fase_anterior
	   items_sin_sucesores = 0
	   if fase.relacion_estado_fase.nombre_estado=='Con Lineas Bases' and fase_anterior != None:
		tipo_items=DBSession.query(TipoItem).filter_by(id_fase=fase.id_fase)
		itemsDeFaseActual = []
		for tipo_item in tipo_items:
			itemsTipoItem = DBSession.query(Item).filter_by(id_tipo_item=tipo_item.id_tipo_item).filter_by(vivo=True).filter_by(estado='Aprobado')
			for itemTipoItem in itemsTipoItem:
				succs = DBSession.query(RelacionItem).filter_by(id_item1=itemTipoItem.id_item)
				sw=0
				for suc in succs:
					sw=1
				if sw==0:
					items_sin_sucesores = items_sin_sucesores + 1
				itemsDeFaseActual.append(itemTipoItem)
		contador_items_en_fase_actual = 0
		for item in itemsDeFaseActual:
			contador_items_en_fase_actual = contador_items_en_fase_actual + 1
		#Si contador_items_en_fase_actual es igual a items_con_sucesores entonces cumple la condicion
		if contador_items_en_fase_actual == contador_items_en_fase_actual - items_sin_sucesores:
			fase.id_estado_fase = '5'

    @expose()
    def addAncestro(self, **kw):
        """Metodo para agregar un registro a la base de datos """       
        self.insertarAncestro(kw)
	DBSession.flush() 
        redirect('listado', id_item=kw['id_item2'], id_proyecto=kw['id_proyecto'], id_fase=kw['id_fase'], id_tipo_item=kw['id_tipo_item'])


    @expose()
    def delete(self, id_relacion, idItemActual, id_proyecto, id_fase, id_tipo_item):
        """Metodo que elimina un registro de la base de datos"""
        item = DBSession.query(Item).get(idItemActual)
        id_item = item.id_item
        version_anterior = item.version
        version_nueva = int(item.version) + 1
        linea_bases_item = item.linea_bases

        #Comprobamos que no se encuentre en una Linea Base
        if linea_bases_item != []:
           for linea_base_item in linea_bases_item:
               flash(_("No puede Eliminar la relacion del Item! Se encuentra en una Linea Base..."), 'error')
               redirect('/relacion/listado', id_item=idItemActual, id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

        #El Item cambia de version al eliminar la relacion
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

        #Enviamos al historial los detalles del Item a ser editado
        if detalles != None:
           for detalle in detalles:
               if lista_id_atributo.count(detalle.id_atributo) >= 1: 
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

        #Ponemos a revision todos los items afectados por el item editado
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

        #Los archivos adjuntos del Item a ser editado se copian
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

        DBSession.delete(DBSession.query(RelacionItem).get(id_relacion))
        DBSession.flush()
        transaction.commit()   
        flash(_("Relacion eliminada!"), 'ok')
        redirect('/relacion/listado', id_item=idItemActual, id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)


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
