# -*- coding: utf-8 -*-
"""Controlador de Relacion"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates
from tg import tmpl_context, validate
from webhelpers import paginate

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap.model.model import RelacionItem, Fase, TipoItem, Item, Proyecto
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController



__all__ = ['RelacionController']


class RelacionController(BaseController):

    @expose()
    def index(self):
        """Muestra la pantalla inicial"""
        return dict(nombre_modelo='RelacionItem', page='index_relacion')        


    @expose('is2sap.templates.relacion.nuevo')
    def nuevo(self, idItemActual):
        """Establece una relacion para el item."""
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
        posicion=0        
        for fase in proyecto.fases:
            print fase.id_fase
            if fase.id_fase==faseActual.id_fase:                
                posicion = proyecto.fases.index(fase) - 1
        itemsDeFaseAdyacente = DBSession.query(Item).join(TipoItem).join(Fase).filter(Fase.id_fase==proyecto.fases[posicion].id_fase).all()
        antecesores = DBSession.query(RelacionItem).filter_by(id_item2=idItemActual).filter_by(tipo="Antecesor-Sucesor").order_by(RelacionItem.id_item1).all()       
        for antec in antecesores:        
            for item2 in itemsDeFaseAdyacente:            
                if item2.id_item == antec.id_item1:
                    itemsDeFaseAdyacente.remove(item2)
        return dict(nombre_modelo='RelacionItem', page='relacion', idItemActual=idItemActual, itemsDeFase=itemsDeFase, itemsDeFaseAdyacente=itemsDeFaseAdyacente)

    @expose("is2sap.templates.relacion.listado")
    def listado(self, id_item):
        """Metodo para listar todos los usuarios de la base de datos"""
        antecesores = DBSession.query(RelacionItem).filter_by(id_item2=id_item).filter_by(tipo="Antecesor-Sucesor").order_by(RelacionItem.id_item1)
        hijos = DBSession.query(RelacionItem).filter_by(id_item1=id_item).filter_by(tipo="Padre-Hijo").order_by(RelacionItem.id_item2)
        return dict(antecesores=antecesores, hijos=hijos, idItemActual=id_item)



    @expose()
    def addHijo(self, id_item1, id_item2):
        """Metodo para agregar un registro a la base de datos """       
        relacion = RelacionItem()
        relacion.tipo = "Padre-Hijo"
        relacion.id_item1 = id_item1
        relacion.id_item2 = id_item2
        #relacion.estado = "Activo"
        #relacion.version = version        
        DBSession.add(relacion)
        DBSession.flush()
        redirect("/relacion/listado", id_item=id_item1)


    @expose()
    def addAncestro(self, id_item1, id_item2):
        """Metodo para agregar un registro a la base de datos """       
        print "Estoy Creando Una relacion"
        relacion1 = RelacionItem()
        relacion1.tipo = "Antecesor-Sucesor"        
        relacion1.id_item1 = id_item1
        relacion1.id_item2 = id_item2
        ##relacion1.estado = "Activo"
        ##relacion1.version = version        
        DBSession.add(relacion1)
        DBSession.flush()       
        redirect("/relacion/listado", id_item=id_item2)

#    @expose('is2sap.templates.usuario.editar')
#    def editar(self, id_usuario, **kw):
#        """Metodo que rellena el formulario para editar los datos de un usuario"""
#        return dict(nombre_modelo='Usuario', page='editar_usuario', value=kw)

#    @validate(editar_usuario_form, error_handler=editar)
#    @expose()
#    def update(self, **kw):        
#        """Metodo que actualiza la base de datos"""


#    @expose('is2sap.templates.usuario.confirmar_eliminar')
#    def confirmar_eliminar(self, id_usuario, **kw):
#        """Despliega confirmacion de eliminacion"""

#        return dict(nombre_modelo='Usuario', page='eliminar_usuario', value=usuario)

    @expose()
    def delete(self, id_relacion, idItemActual, **kw):
       """Metodo que elimina un registro de la base de datos"""
       DBSession.delete(DBSession.query(RelacionItem).get(id_relacion))
       redirect("/relacion/listado", id_item=idItemActual)
