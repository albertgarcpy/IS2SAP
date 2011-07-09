# -*- coding: utf-8 -*-
"""Controlador de Relacion"""

from tg import expose, flash, require, redirect
from repoze.what import predicates
from tg import validate
from webhelpers import paginate

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import RelacionItem, Fase, TipoItem, Item, Proyecto
from is2sap import model
from is2sap.controllers.grafo.grafo import Graph
import transaction
import time
import os


newGrafo = Graph()
inserciones=0


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
        return dict(antecesores=listaAntecesores, hijos=listaHijos, idItemActual=id_item, id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)

    
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
                print "La insercion de esta relacion creara un ciclo"
            else:
                print "No se encuentran ciclos"        
            
                relacion = RelacionItem()
                relacion.tipo = "Padre-Hijo"
                relacion.id_item1 = kw['id_item1']
                relacion.id_item2 = kw['id_item2']
                #relacion.estado = "Activo"
                #relacion.version = version        
                DBSession.add(relacion)
                DBSession.flush() 
                transaction.commit()        


    @expose()
    def addHijo(self, **kw):
        self.insertarHijo(kw)
        redirect('listado', id_item=kw['id_item1'], id_proyecto=kw['id_proyecto'], id_fase=kw['id_fase'], id_tipo_item=kw['id_tipo_item'])
        

    def insertarAncestro(self, kw): 
        global inserciones
        inserciones = inserciones + 1
        print "el numero de inserciones es :", inserciones
        if inserciones == 1:
            relacion1 = RelacionItem()
            relacion1.tipo = "Antecesor-Sucesor"        
            relacion1.id_item1 = kw['id_item1']
            relacion1.id_item2 = kw['id_item2']
            ##relacion1.estado = "Activo"
            ##relacion1.version = version        
            DBSession.add(relacion1)
            DBSession.flush()
            transaction.commit()        


    @expose()
    def addAncestro(self, **kw):
        """Metodo para agregar un registro a la base de datos """       
        self.insertarAncestro(kw)
        redirect('listado', id_item=kw['id_item2'], id_proyecto=kw['id_proyecto'], id_fase=kw['id_fase'], id_tipo_item=kw['id_tipo_item'])


    @expose()
    def delete(self, id_relacion, idItemActual, id_proyecto, id_fase, id_tipo_item):
       """Metodo que elimina un registro de la base de datos"""
       DBSession.delete(DBSession.query(RelacionItem).get(id_relacion))
       redirect('/relacion/listado', id_item=idItemActual, id_proyecto=id_proyecto, id_fase=id_fase, id_tipo_item=id_tipo_item)
